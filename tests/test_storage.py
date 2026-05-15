"""Tests for snapshot persistence (save/load/list)."""

import json
from pathlib import Path

import pytest

from schemasnap.snapshot import SchemaSnapshot
from schemasnap.storage import (
    load_latest_snapshot,
    load_snapshot,
    list_snapshots,
    save_snapshot,
)

SAMPLE_TABLES = {
    "users": [{"name": "id", "type": "integer", "nullable": "NO", "default": None}]
}


@pytest.fixture
def tmp_snap_dir(tmp_path):
    return tmp_path / ".schemasnap"


def make_snapshot(db_name="testdb", tables=None) -> SchemaSnapshot:
    return SchemaSnapshot(
        db_type="postgresql",
        db_name=db_name,
        tables=tables or SAMPLE_TABLES,
    )


class TestSaveAndLoad:
    def test_save_creates_file(self, tmp_snap_dir):
        snap = make_snapshot()
        path = save_snapshot(snap, base_dir=tmp_snap_dir)
        assert path.exists()

    def test_saved_file_is_valid_json(self, tmp_snap_dir):
        snap = make_snapshot()
        path = save_snapshot(snap, base_dir=tmp_snap_dir)
        data = json.loads(path.read_text())
        assert data["db_name"] == "testdb"

    def test_load_snapshot_roundtrip(self, tmp_snap_dir):
        snap = make_snapshot()
        path = save_snapshot(snap, base_dir=tmp_snap_dir)
        restored = load_snapshot(path)
        assert restored.version_hash == snap.version_hash
        assert restored.tables == snap.tables

    def test_filename_contains_db_name_and_hash(self, tmp_snap_dir):
        snap = make_snapshot(db_name="myapp")
        path = save_snapshot(snap, base_dir=tmp_snap_dir)
        assert "myapp" in path.name
        assert snap.version_hash in path.name


class TestListAndLatest:
    def test_list_returns_empty_when_no_dir(self, tmp_snap_dir):
        result = list_snapshots("testdb", base_dir=tmp_snap_dir)
        assert result == []

    def test_list_returns_only_matching_db(self, tmp_snap_dir):
        save_snapshot(make_snapshot(db_name="alpha"), base_dir=tmp_snap_dir)
        save_snapshot(make_snapshot(db_name="beta", tables={}), base_dir=tmp_snap_dir)
        alpha_snaps = list_snapshots("alpha", base_dir=tmp_snap_dir)
        assert len(alpha_snaps) == 1
        assert "alpha" in alpha_snaps[0].name

    def test_load_latest_returns_none_when_empty(self, tmp_snap_dir):
        assert load_latest_snapshot("ghost", base_dir=tmp_snap_dir) is None

    def test_load_latest_returns_most_recent(self, tmp_snap_dir):
        snap_old = make_snapshot(tables={"a": []})
        snap_new = make_snapshot(tables={"a": [], "b": []})
        # Ensure different captured_at by tweaking manually
        snap_old.captured_at = "2024-01-01T00:00:00+00:00"
        snap_new.captured_at = "2024-06-01T00:00:00+00:00"
        save_snapshot(snap_old, base_dir=tmp_snap_dir)
        save_snapshot(snap_new, base_dir=tmp_snap_dir)
        latest = load_latest_snapshot("testdb", base_dir=tmp_snap_dir)
        assert latest.captured_at == snap_new.captured_at
