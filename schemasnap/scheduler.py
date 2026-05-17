"""Periodic schema snapshot scheduler using a simple polling loop."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Optional

from schemasnap.watcher import SchemaWatcher, WatcherConfig

logger = logging.getLogger(__name__)


@dataclass
class SchedulerConfig:
    """Configuration for the polling scheduler."""

    interval_seconds: int = 3600  # default: run every hour
    max_runs: Optional[int] = None  # None means run indefinitely
    stop_on_error: bool = False


class SchemaScheduler:
    """Runs a SchemaWatcher on a fixed interval."""

    def __init__(
        self,
        watcher: SchemaWatcher,
        scheduler_config: SchedulerConfig,
    ) -> None:
        self._watcher = watcher
        self._config = scheduler_config
        self._run_count = 0
        self._running = False

    def start(self) -> None:
        """Start the polling loop."""
        self._running = True
        logger.info(
            "Scheduler started (interval=%ds, max_runs=%s)",
            self._config.interval_seconds,
            self._config.max_runs,
        )
        try:
            self._loop()
        finally:
            self._running = False
            logger.info("Scheduler stopped after %d run(s).", self._run_count)

    def stop(self) -> None:
        """Signal the loop to stop after the current run."""
        self._running = False

    def _loop(self) -> None:
        while self._running:
            try:
                logger.debug("Scheduler triggering watcher run #%d", self._run_count + 1)
                self._watcher.run_once()
                self._run_count += 1
            except Exception as exc:  # pylint: disable=broad-except
                logger.error("Error during scheduled run: %s", exc)
                if self._config.stop_on_error:
                    raise

            if (
                self._config.max_runs is not None
                and self._run_count >= self._config.max_runs
            ):
                logger.info("Reached max_runs=%d, stopping.", self._config.max_runs)
                break

            if self._running:
                logger.debug("Sleeping for %d seconds.", self._config.interval_seconds)
                time.sleep(self._config.interval_seconds)
