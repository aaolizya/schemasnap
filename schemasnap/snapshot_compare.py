"""High-level snapshot comparison utilities with optional tag and filter support."""

from __future__ import annotations

from typing import Optional

from schemasnap.snapshot import SchemaSnapshot
from schemasnap.storage import load_snapshot, load_latest_snapshot
from schemasnap.differ import diff_snapshots, SchemaDiff
from schemasnap.filter import FilterConfig, apply_filter
from schemasnap.snapshot_tag_integration import resolve_snapshot


def compare_by_ids(
    snap_dir: str,
    id_a: str,
    id_b: str,
    filter_cfg: Optional[FilterConfig] = None,
) -> SchemaDiff:
    """Load two snapshots by version ID and return their diff."""
    snap_a = load_snapshot(snap_dir, id_a)
    snap_b = load_snapshot(snap_dir, id_b)
    if filter_cfg is not None:
        snap_a = apply_filter(snap_a, filter_cfg)
        snap_b = apply_filter(snap_b, filter_cfg)
    return diff_snapshots(snap_a, snap_b)


def compare_tag_to_latest(
    snap_dir: str,
    tag: str,
    filter_cfg: Optional[FilterConfig] = None,
) -> SchemaDiff:
    """Compare a tagged snapshot against the most recent snapshot."""
    snap_a = resolve_snapshot(snap_dir, tag)
    snap_b = load_latest_snapshot(snap_dir)
    if filter_cfg is not None:
        snap_a = apply_filter(snap_a, filter_cfg)
        snap_b = apply_filter(snap_b, filter_cfg)
    return diff_snapshots(snap_a, snap_b)


def compare_latest_pair(
    snap_dir: str,
    filter_cfg: Optional[FilterConfig] = None,
) -> Optional[SchemaDiff]:
    """Diff the two most recent snapshots; return None if fewer than two exist."""
    from schemasnap.storage import list_snapshots

    ids = list_snapshots(snap_dir)
    if len(ids) < 2:
        return None
    snap_a = load_snapshot(snap_dir, ids[-2])
    snap_b = load_snapshot(snap_dir, ids[-1])
    if filter_cfg is not None:
        snap_a = apply_filter(snap_a, filter_cfg)
        snap_b = apply_filter(snap_b, filter_cfg)
    return diff_snapshots(snap_a, snap_b)
