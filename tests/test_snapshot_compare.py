"""Tests for schemasnap.snapshot_compare."""

from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock

from schemasnap.snapshot import SchemaSnapshot
from schemasnap.snapshot_compare import (
    compare_by_ids,
    compare_tag_to_latest,
    compare_latest_pair,
)


def _snap(tables: dict) -> SchemaSnapshot:
    return SchemaSnapshot(db_url="postgresql://localhost/test", tables=tables)


TABLES_A = {"users": [{"name": "id", "type": "integer", "nullable": False, "default": None}]}
TABLES_B = {
    "users": [{"name": "id", "type": "integer", "nullable": False, "default": None}],
    "orders": [{"name": "id", "type": "integer", "nullable": False, "default": None}],
}


@patch("schemasnap.snapshot_compare.load_snapshot")
def test_compare_by_ids_calls_load(mock_load):
    mock_load.side_effect = [_snap(TABLES_A), _snap(TABLES_B)]
    diff = compare_by_ids("/snaps", "abc", "def")
    assert mock_load.call_count == 2
    assert "orders" in diff.added_tables


@patch("schemasnap.snapshot_compare.load_snapshot")
def test_compare_by_ids_no_changes(mock_load):
    mock_load.side_effect = [_snap(TABLES_A), _snap(TABLES_A)]
    diff = compare_by_ids("/snaps", "abc", "abc")
    assert not diff.has_changes()


@patch("schemasnap.snapshot_compare.load_latest_snapshot")
@patch("schemasnap.snapshot_compare.resolve_snapshot")
def test_compare_tag_to_latest(mock_resolve, mock_latest):
    mock_resolve.return_value = _snap(TABLES_A)
    mock_latest.return_value = _snap(TABLES_B)
    diff = compare_tag_to_latest("/snaps", "v1")
    mock_resolve.assert_called_once_with("/snaps", "v1")
    assert "orders" in diff.added_tables


@patch("schemasnap.snapshot_compare.list_snapshots")
@patch("schemasnap.snapshot_compare.load_snapshot")
def test_compare_latest_pair_returns_diff(mock_load, mock_list):
    mock_list.return_value = ["snap1", "snap2"]
    mock_load.side_effect = [_snap(TABLES_A), _snap(TABLES_B)]
    diff = compare_latest_pair("/snaps")
    assert diff is not None
    assert "orders" in diff.added_tables


@patch("schemasnap.snapshot_compare.list_snapshots")
def test_compare_latest_pair_too_few_snapshots(mock_list):
    mock_list.return_value = ["snap1"]
    diff = compare_latest_pair("/snaps")
    assert diff is None


@patch("schemasnap.snapshot_compare.list_snapshots")
def test_compare_latest_pair_empty(mock_list):
    mock_list.return_value = []
    diff = compare_latest_pair("/snaps")
    assert diff is None


@patch("schemasnap.snapshot_compare.load_snapshot")
def test_compare_by_ids_with_filter(mock_load):
    from schemasnap.filter import FilterConfig

    mock_load.side_effect = [_snap(TABLES_B), _snap(TABLES_B)]
    cfg = FilterConfig(exclude_tables=["orders"])
    diff = compare_by_ids("/snaps", "x", "y", filter_cfg=cfg)
    assert not diff.has_changes()
