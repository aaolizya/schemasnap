"""Tests for schemasnap.baseline."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from schemasnap.baseline import (
    BASELINE_FILENAME,
    baseline_exists,
    clear_baseline,
    diff_against_baseline,
    load_baseline,
    save_baseline,
)
from schemasnap.snapshot import SchemaSnapshot


@pytest.fixture()
def snap_dir(tmp_path: Path) -> str:
    return str(tmp_path)


def _make_snapshot(tables: dict | None = None) -> SchemaSnapshot:
    return SchemaSnapshot(
        db_url="postgresql://localhost/testdb",
        tables=tables or {"users": [{"name": "id", "type": "integer", "nullable": False}]},
    )


class TestSaveBaseline:
    def test_creates_file(self, snap_dir):
        snap = _make_snapshot()
        path = save_baseline(snap.to_dict(), snap_dir)
        assert path.exists()
        assert path.name == BASELINE_FILENAME

    def test_file_is_valid_json(self, snap_dir):
        snap = _make_snapshot()
        path = save_baseline(snap.to_dict(), snap_dir)
        data = json.loads(path.read_text())
        assert "tables" in data

    def test_creates_directory_if_missing(self, tmp_path):
        new_dir = str(tmp_path / "nested" / "dir")
        snap = _make_snapshot()
        path = save_baseline(snap.to_dict(), new_dir)
        assert path.exists()


class TestLoadBaseline:
    def test_returns_none_when_missing(self, snap_dir):
        assert load_baseline(snap_dir) is None

    def test_round_trip(self, snap_dir):
        snap = _make_snapshot()
        save_baseline(snap.to_dict(), snap_dir)
        loaded = load_baseline(snap_dir)
        assert loaded["tables"] == snap.tables


class TestBaselineExists:
    def test_false_before_save(self, snap_dir):
        assert baseline_exists(snap_dir) is False

    def test_true_after_save(self, snap_dir):
        save_baseline(_make_snapshot().to_dict(), snap_dir)
        assert baseline_exists(snap_dir) is True


class TestClearBaseline:
    def test_returns_false_when_nothing_to_delete(self, snap_dir):
        assert clear_baseline(snap_dir) is False

    def test_deletes_file(self, snap_dir):
        save_baseline(_make_snapshot().to_dict(), snap_dir)
        result = clear_baseline(snap_dir)
        assert result is True
        assert not baseline_exists(snap_dir)


class TestDiffAgainstBaseline:
    def test_returns_none_when_no_baseline(self, snap_dir):
        snap = _make_snapshot()
        assert diff_against_baseline(snap, snap_dir) is None

    def test_no_changes_when_identical(self, snap_dir):
        snap = _make_snapshot()
        save_baseline(snap.to_dict(), snap_dir)
        diff = diff_against_baseline(snap, snap_dir)
        assert diff is not None
        assert not diff.has_changes()

    def test_detects_added_table(self, snap_dir):
        baseline_snap = _make_snapshot({"users": [{"name": "id", "type": "integer", "nullable": False}]})
        save_baseline(baseline_snap.to_dict(), snap_dir)
        current_snap = _make_snapshot({
            "users": [{"name": "id", "type": "integer", "nullable": False}],
            "orders": [{"name": "id", "type": "integer", "nullable": False}],
        })
        diff = diff_against_baseline(current_snap, snap_dir)
        assert diff is not None
        assert "orders" in diff.added_tables
