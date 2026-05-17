"""Tracks migration history by associating schema snapshots with migration labels."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

MIGRATION_INDEX_FILE = "migration_index.json"


@dataclass
class MigrationEntry:
    label: str
    snapshot_file: str
    recorded_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "snapshot_file": self.snapshot_file,
            "recorded_at": self.recorded_at,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MigrationEntry":
        return cls(
            label=data["label"],
            snapshot_file=data["snapshot_file"],
            recorded_at=data.get("recorded_at", ""),
            notes=data.get("notes", ""),
        )


def _index_path(snap_dir: str) -> str:
    return os.path.join(snap_dir, MIGRATION_INDEX_FILE)


def _load_index(snap_dir: str) -> List[dict]:
    path = _index_path(snap_dir)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _save_index(snap_dir: str, entries: List[dict]) -> None:
    os.makedirs(snap_dir, exist_ok=True)
    with open(_index_path(snap_dir), "w", encoding="utf-8") as fh:
        json.dump(entries, fh, indent=2)


def record_migration(snap_dir: str, label: str, snapshot_file: str, notes: str = "") -> MigrationEntry:
    """Associate a migration label with an existing snapshot file."""
    entry = MigrationEntry(label=label, snapshot_file=snapshot_file, notes=notes)
    entries = _load_index(snap_dir)
    entries.append(entry.to_dict())
    _save_index(snap_dir, entries)
    return entry


def list_migrations(snap_dir: str) -> List[MigrationEntry]:
    """Return all recorded migration entries in chronological order."""
    return [MigrationEntry.from_dict(d) for d in _load_index(snap_dir)]


def find_migration(snap_dir: str, label: str) -> Optional[MigrationEntry]:
    """Look up a migration entry by label (returns first match)."""
    for entry in list_migrations(snap_dir):
        if entry.label == label:
            return entry
    return None


def clear_migrations(snap_dir: str) -> None:
    """Remove the migration index file entirely."""
    path = _index_path(snap_dir)
    if os.path.exists(path):
        os.remove(path)
