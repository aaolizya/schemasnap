"""Tests for schemasnap.migration_tracker."""

from __future__ import annotations

import json
import os

import pytest

from schemasnap.migration_tracker import (
    MigrationEntry,
    clear_migrations,
    find_migration,
    list_migrations,
    record_migration,
    MIGRATION_INDEX_FILE,
)


@pytest.fixture()
def snap_dir(tmp_path):
    return str(tmp_path)


class TestMigrationEntry:
    def test_to_dict_contains_required_keys(self):
        e = MigrationEntry(label="v1", snapshot_file="snap_001.json")
        d = e.to_dict()
        assert {"label", "snapshot_file", "recorded_at", "notes"} <= d.keys()

    def test_from_dict_round_trip(self):
        e = MigrationEntry(label="v2", snapshot_file="snap_002.json", notes="initial")
        restored = MigrationEntry.from_dict(e.to_dict())
        assert restored.label == e.label
        assert restored.snapshot_file == e.snapshot_file
        assert restored.notes == e.notes

    def test_recorded_at_is_iso_format(self):
        e = MigrationEntry(label="v3", snapshot_file="snap_003.json")
        # Should not raise
        from datetime import datetime
        datetime.fromisoformat(e.recorded_at)


class TestRecordMigration:
    def test_creates_index_file(self, snap_dir):
        record_migration(snap_dir, "0001_init", "snap_0001.json")
        assert os.path.exists(os.path.join(snap_dir, MIGRATION_INDEX_FILE))

    def test_index_file_is_valid_json(self, snap_dir):
        record_migration(snap_dir, "0001_init", "snap_0001.json")
        with open(os.path.join(snap_dir, MIGRATION_INDEX_FILE)) as fh:
            data = json.load(fh)
        assert isinstance(data, list)
        assert len(data) == 1

    def test_multiple_records_appended(self, snap_dir):
        record_migration(snap_dir, "0001_init", "snap_0001.json")
        record_migration(snap_dir, "0002_add_col", "snap_0002.json")
        entries = list_migrations(snap_dir)
        assert len(entries) == 2

    def test_returns_migration_entry(self, snap_dir):
        entry = record_migration(snap_dir, "0001_init", "snap_0001.json", notes="first")
        assert isinstance(entry, MigrationEntry)
        assert entry.label == "0001_init"
        assert entry.notes == "first"


class TestListMigrations:
    def test_empty_dir_returns_empty_list(self, snap_dir):
        assert list_migrations(snap_dir) == []

    def test_returns_entries_in_order(self, snap_dir):
        record_migration(snap_dir, "a", "a.json")
        record_migration(snap_dir, "b", "b.json")
        labels = [e.label for e in list_migrations(snap_dir)]
        assert labels == ["a", "b"]


class TestFindMigration:
    def test_finds_existing_label(self, snap_dir):
        record_migration(snap_dir, "0001", "snap.json")
        entry = find_migration(snap_dir, "0001")
        assert entry is not None
        assert entry.label == "0001"

    def test_returns_none_for_missing_label(self, snap_dir):
        assert find_migration(snap_dir, "nonexistent") is None


class TestClearMigrations:
    def test_removes_index_file(self, snap_dir):
        record_migration(snap_dir, "0001", "snap.json")
        clear_migrations(snap_dir)
        assert not os.path.exists(os.path.join(snap_dir, MIGRATION_INDEX_FILE))

    def test_clear_on_empty_dir_does_not_raise(self, snap_dir):
        clear_migrations(snap_dir)  # should not raise
