"""Tests for schemasnap.snapshot_search."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone

import pytest

from schemasnap.snapshot import SchemaSnapshot
from schemasnap.snapshot_search import (
    SearchQuery,
    find_snapshot_by_table,
    find_snapshots_in_range,
    search_snapshots,
)


def _snap(tables: dict, captured_at: str, snap_dir: str) -> SchemaSnapshot:
    s = SchemaSnapshot(tables=tables, captured_at=captured_at)
    path = os.path.join(snap_dir, f"{s.version_hash}.json")
    with open(path, "w") as fh:
        json.dump(s.to_dict(), fh)
    return s


@pytest.fixture()
def snap_dir(tmp_path):
    return str(tmp_path)


class TestSearchSnapshots:
    def test_empty_dir_returns_empty(self, snap_dir):
        results = search_snapshots(snap_dir, SearchQuery())
        assert results == []

    def test_no_filter_returns_all(self, snap_dir):
        _snap({"users": {}}, "2024-01-01T00:00:00", snap_dir)
        _snap({"orders": {}}, "2024-01-02T00:00:00", snap_dir)
        results = search_snapshots(snap_dir, SearchQuery())
        assert len(results) == 2

    def test_results_sorted_by_captured_at(self, snap_dir):
        _snap({"b": {}}, "2024-02-01T00:00:00", snap_dir)
        _snap({"a": {}}, "2024-01-01T00:00:00", snap_dir)
        results = search_snapshots(snap_dir, SearchQuery())
        assert results[0].captured_at < results[1].captured_at

    def test_since_filter(self, snap_dir):
        _snap({"old": {}}, "2023-06-01T00:00:00", snap_dir)
        _snap({"new": {}}, "2024-06-01T00:00:00", snap_dir)
        q = SearchQuery(since=datetime(2024, 1, 1))
        results = search_snapshots(snap_dir, q)
        assert len(results) == 1
        assert "new" in results[0].tables

    def test_until_filter(self, snap_dir):
        _snap({"old": {}}, "2023-06-01T00:00:00", snap_dir)
        _snap({"new": {}}, "2024-06-01T00:00:00", snap_dir)
        q = SearchQuery(until=datetime(2023, 12, 31))
        results = search_snapshots(snap_dir, q)
        assert len(results) == 1
        assert "old" in results[0].tables

    def test_table_name_filter(self, snap_dir):
        _snap({"users": {}, "orders": {}}, "2024-01-01T00:00:00", snap_dir)
        _snap({"products": {}}, "2024-01-02T00:00:00", snap_dir)
        results = find_snapshot_by_table(snap_dir, "users")
        assert len(results) == 1
        assert "users" in results[0].tables

    def test_min_table_count(self, snap_dir):
        _snap({"a": {}, "b": {}, "c": {}}, "2024-01-01T00:00:00", snap_dir)
        _snap({"x": {}}, "2024-01-02T00:00:00", snap_dir)
        q = SearchQuery(min_table_count=2)
        results = search_snapshots(snap_dir, q)
        assert len(results) == 1
        assert len(results[0].tables) == 3

    def test_max_table_count(self, snap_dir):
        _snap({"a": {}, "b": {}, "c": {}}, "2024-01-01T00:00:00", snap_dir)
        _snap({"x": {}}, "2024-01-02T00:00:00", snap_dir)
        q = SearchQuery(max_table_count=1)
        results = search_snapshots(snap_dir, q)
        assert len(results) == 1
        assert "x" in results[0].tables

    def test_find_snapshots_in_range(self, snap_dir):
        _snap({"a": {}}, "2024-01-01T00:00:00", snap_dir)
        _snap({"b": {}}, "2024-03-01T00:00:00", snap_dir)
        _snap({"c": {}}, "2024-06-01T00:00:00", snap_dir)
        results = find_snapshots_in_range(
            snap_dir, datetime(2024, 2, 1), datetime(2024, 5, 1)
        )
        assert len(results) == 1
        assert "b" in results[0].tables
