"""Tag manager: attach human-readable tags/labels to schema snapshots."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

_TAG_INDEX_FILE = "tags.json"


@dataclass
class TagEntry:
    tag: str
    snapshot_id: str
    note: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict:
        return {
            "tag": self.tag,
            "snapshot_id": self.snapshot_id,
            "note": self.note,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "TagEntry":
        return cls(
            tag=data["tag"],
            snapshot_id=data["snapshot_id"],
            note=data.get("note"),
            created_at=data["created_at"],
        )


def _index_path(snap_dir: str) -> str:
    return os.path.join(snap_dir, _TAG_INDEX_FILE)


def _load_index(snap_dir: str) -> List[Dict]:
    path = _index_path(snap_dir)
    if not os.path.exists(path):
        return []
    with open(path, "r") as fh:
        return json.load(fh)


def _save_index(snap_dir: str, entries: List[Dict]) -> None:
    os.makedirs(snap_dir, exist_ok=True)
    with open(_index_path(snap_dir), "w") as fh:
        json.dump(entries, fh, indent=2)


def add_tag(snap_dir: str, tag: str, snapshot_id: str, note: Optional[str] = None) -> TagEntry:
    """Associate *tag* with *snapshot_id*. Raises ValueError if tag already exists."""
    entries = _load_index(snap_dir)
    for e in entries:
        if e["tag"] == tag:
            raise ValueError(f"Tag '{tag}' already exists. Remove it first.")
    entry = TagEntry(tag=tag, snapshot_id=snapshot_id, note=note)
    entries.append(entry.to_dict())
    _save_index(snap_dir, entries)
    return entry


def remove_tag(snap_dir: str, tag: str) -> bool:
    """Remove *tag*. Returns True if found and removed, False otherwise."""
    entries = _load_index(snap_dir)
    new_entries = [e for e in entries if e["tag"] != tag]
    if len(new_entries) == len(entries):
        return False
    _save_index(snap_dir, new_entries)
    return True


def get_tag(snap_dir: str, tag: str) -> Optional[TagEntry]:
    """Return the TagEntry for *tag*, or None if not found."""
    for e in _load_index(snap_dir):
        if e["tag"] == tag:
            return TagEntry.from_dict(e)
    return None


def list_tags(snap_dir: str) -> List[TagEntry]:
    """Return all tags ordered by creation time."""
    return [TagEntry.from_dict(e) for e in _load_index(snap_dir)]
