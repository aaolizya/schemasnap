"""Integration helpers: resolve a snapshot by tag name."""

from __future__ import annotations

from typing import Optional

from schemasnap.snapshot import SchemaSnapshot
from schemasnap.storage import load_snapshot
from schemasnap.tag_manager import get_tag


def load_snapshot_by_tag(snap_dir: str, tag: str) -> SchemaSnapshot:
    """Load the snapshot associated with *tag*.

    Raises:
        KeyError: if the tag does not exist.
        FileNotFoundError: if the snapshot file is missing.
    """
    entry = get_tag(snap_dir, tag)
    if entry is None:
        raise KeyError(f"Tag '{tag}' not found in '{snap_dir}'.")
    return load_snapshot(snap_dir, entry.snapshot_id)


def resolve_snapshot(
    snap_dir: str,
    *,
    snapshot_id: Optional[str] = None,
    tag: Optional[str] = None,
) -> SchemaSnapshot:
    """Return a snapshot given either a direct *snapshot_id* or a *tag* name.

    Exactly one of the two keyword arguments must be provided.
    """
    if snapshot_id is not None and tag is not None:
        raise ValueError("Provide either 'snapshot_id' or 'tag', not both.")
    if snapshot_id is None and tag is None:
        raise ValueError("One of 'snapshot_id' or 'tag' must be provided.")

    if tag is not None:
        return load_snapshot_by_tag(snap_dir, tag)
    return load_snapshot(snap_dir, snapshot_id)  # type: ignore[arg-type]
