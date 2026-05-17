"""Search and query snapshots by metadata criteria."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from schemasnap.snapshot import SchemaSnapshot
from schemasnap.storage import list_snapshots, load_snapshot


@dataclass
class SearchQuery:
    """Criteria for filtering snapshots."""
    since: Optional[datetime] = None
    until: Optional[datetime] = None
    table_name: Optional[str] = None
    min_table_count: Optional[int] = None
    max_table_count: Optional[int] = None
    label: Optional[str] = None


def _matches(snapshot: SchemaSnapshot, query: SearchQuery) -> bool:
    ts = datetime.fromisoformat(snapshot.captured_at)

    if query.since and ts < query.since:
        return False
    if query.until and ts > query.until:
        return False
    if query.table_name and query.table_name not in snapshot.tables:
        return False
    if query.min_table_count is not None and len(snapshot.tables) < query.min_table_count:
        return False
    if query.max_table_count is not None and len(snapshot.tables) > query.max_table_count:
        return False
    if query.label and getattr(snapshot, "label", None) != query.label:
        return False
    return True


def search_snapshots(
    snap_dir: str,
    query: SearchQuery,
) -> List[SchemaSnapshot]:
    """Return all snapshots in *snap_dir* that satisfy *query*."""
    results: List[SchemaSnapshot] = []
    for snap_id in list_snapshots(snap_dir):
        try:
            snap = load_snapshot(snap_dir, snap_id)
        except Exception:
            continue
        if _matches(snap, query):
            results.append(snap)
    results.sort(key=lambda s: s.captured_at)
    return results


def find_snapshot_by_table(snap_dir: str, table_name: str) -> List[SchemaSnapshot]:
    """Convenience wrapper: return snapshots that contain *table_name*."""
    return search_snapshots(snap_dir, SearchQuery(table_name=table_name))


def find_snapshots_in_range(
    snap_dir: str,
    since: datetime,
    until: datetime,
) -> List[SchemaSnapshot]:
    """Return snapshots captured between *since* and *until* (inclusive)."""
    return search_snapshots(snap_dir, SearchQuery(since=since, until=until))
