"""Persistence helpers for SchemaSnapshot objects."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List, Optional

from schemasnap.snapshot import SchemaSnapshot

_FILENAME_PREFIX = "snapshot_"
_FILENAME_EXT = ".json"


def save_snapshot(snapshot: SchemaSnapshot, directory: str) -> Path:
    """Persist *snapshot* to *directory* as a JSON file named by its hash."""
    dest = Path(directory)
    dest.mkdir(parents=True, exist_ok=True)
    filename = f"{_FILENAME_PREFIX}{snapshot.version_hash}{_FILENAME_EXT}"
    filepath = dest / filename
    with filepath.open("w", encoding="utf-8") as fh:
        json.dump(snapshot.to_dict(), fh, indent=2)
    return filepath


def load_snapshot(path: str | Path) -> SchemaSnapshot:
    """Load a single snapshot from *path*."""
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    return SchemaSnapshot.from_dict(data)


def list_snapshots(directory: str) -> List[Path]:
    """Return all snapshot files in *directory*, sorted oldest-first by mtime."""
    base = Path(directory)
    if not base.exists():
        return []
    files = [
        p
        for p in base.iterdir()
        if p.name.startswith(_FILENAME_PREFIX) and p.suffix == _FILENAME_EXT
    ]
    return sorted(files, key=lambda p: p.stat().st_mtime)


def load_latest_snapshot(
    directory: str, exclude_hash: Optional[str] = None
) -> Optional[SchemaSnapshot]:
    """Return the most-recent snapshot, optionally skipping one with *exclude_hash*.

    This is useful in the watcher so we don't compare a snapshot against itself.
    """
    candidates = list_snapshots(directory)
    # Traverse newest-first
    for path in reversed(candidates):
        snap = load_snapshot(path)
        if exclude_hash and snap.version_hash == exclude_hash:
            continue
        return snap
    return None
