"""Watcher module: periodically extracts schema snapshots and detects drift."""

from __future__ import annotations

import time
import logging
from dataclasses import dataclass, field
from typing import Callable, Optional

from schemasnap.extractor import extract_schema
from schemasnap.snapshot import SchemaSnapshot
from schemasnap.storage import load_latest_snapshot, save_snapshot
from schemasnap.differ import diff_snapshots, SchemaDiff

logger = logging.getLogger(__name__)


@dataclass
class WatcherConfig:
    """Configuration for the schema watcher."""

    connection: object  # live DB connection
    dialect: str  # 'postgresql' or 'mysql'
    snapshot_dir: str
    interval_seconds: int = 60
    on_drift: Optional[Callable[[SchemaDiff], None]] = field(default=None, repr=False)


class SchemaWatcher:
    """Polls the database on a schedule and fires a callback when schema drift is detected."""

    def __init__(self, config: WatcherConfig) -> None:
        self.config = config
        self._running = False

    def _take_and_compare(self) -> Optional[SchemaDiff]:
        tables = extract_schema(self.config.connection, self.config.dialect)
        current = SchemaSnapshot(tables=tables)
        save_snapshot(current, self.config.snapshot_dir)

        previous = load_latest_snapshot(self.config.snapshot_dir, exclude_hash=current.version_hash)
        if previous is None:
            logger.info("No previous snapshot found — baseline established.")
            return None

        diff = diff_snapshots(previous, current)
        if diff.has_changes():
            logger.warning("Schema drift detected: %s", diff.summary())
            if self.config.on_drift:
                self.config.on_drift(diff)
            return diff

        logger.debug("No schema changes detected.")
        return None

    def run_once(self) -> Optional[SchemaDiff]:
        """Execute a single check cycle."""
        return self._take_and_compare()

    def start(self) -> None:
        """Block and poll indefinitely until stop() is called."""
        self._running = True
        logger.info(
            "SchemaWatcher started (interval=%ds, dir=%s)",
            self.config.interval_seconds,
            self.config.snapshot_dir,
        )
        while self._running:
            try:
                self._take_and_compare()
            except Exception as exc:  # noqa: BLE001
                logger.error("Watcher cycle error: %s", exc)
            time.sleep(self.config.interval_seconds)

    def stop(self) -> None:
        """Signal the polling loop to exit after the current sleep."""
        self._running = False
        logger.info("SchemaWatcher stopping.")
