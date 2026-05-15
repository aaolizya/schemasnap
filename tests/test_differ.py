"""Tests for schemasnap.differ."""

import pytest
from schemasnap.snapshot import SchemaSnapshot
from schemasnap.differ import diff_snapshots, SchemaDiff, TableDiff, ColumnChange


def make_snapshot(tables: dict) -> SchemaSnapshot:
    return SchemaSnapshot(db_type="postgresql", db_name="testdb", tables=tables)


class TestDiffSnapshots:
    def test_no_changes_returns_empty_diff(self):
        tables = {"users": {"id": "integer", "name": "varchar"}}
        old = make_snapshot(tables)
        new = make_snapshot(tables)
        diff = diff_snapshots(old, new)
        assert not diff.has_changes
        assert diff.table_diffs == []

    def test_added_table_detected(self):
        old = make_snapshot({"users": {"id": "integer"}})
        new = make_snapshot({"users": {"id": "integer"}, "orders": {"id": "integer"}})
        diff = diff_snapshots(old, new)
        assert diff.has_changes
        added = [t for t in diff.table_diffs if t.change_type == "added"]
        assert len(added) == 1
        assert added[0].table == "orders"

    def test_removed_table_detected(self):
        old = make_snapshot({"users": {"id": "integer"}, "orders": {"id": "integer"}})
        new = make_snapshot({"users": {"id": "integer"}})
        diff = diff_snapshots(old, new)
        removed = [t for t in diff.table_diffs if t.change_type == "removed"]
        assert len(removed) == 1
        assert removed[0].table == "orders"

    def test_modified_column_detected(self):
        old = make_snapshot({"users": {"id": "integer", "email": "varchar(100)"}})
        new = make_snapshot({"users": {"id": "integer", "email": "varchar(255)"}})
        diff = diff_snapshots(old, new)
        assert diff.has_changes
        modified = [t for t in diff.table_diffs if t.change_type == "modified"]
        assert len(modified) == 1
        col_change = modified[0].column_changes[0]
        assert col_change.column == "email"
        assert col_change.change_type == "modified"
        assert col_change.old_definition == "varchar(100)"
        assert col_change.new_definition == "varchar(255)"

    def test_added_column_detected(self):
        old = make_snapshot({"users": {"id": "integer"}})
        new = make_snapshot({"users": {"id": "integer", "created_at": "timestamp"}})
        diff = diff_snapshots(old, new)
        modified = [t for t in diff.table_diffs if t.change_type == "modified"]
        assert len(modified) == 1
        col = modified[0].column_changes[0]
        assert col.change_type == "added"
        assert col.column == "created_at"

    def test_removed_column_detected(self):
        old = make_snapshot({"users": {"id": "integer", "legacy": "text"}})
        new = make_snapshot({"users": {"id": "integer"}})
        diff = diff_snapshots(old, new)
        modified = [t for t in diff.table_diffs if t.change_type == "modified"]
        col = modified[0].column_changes[0]
        assert col.change_type == "removed"
        assert col.column == "legacy"

    def test_version_hashes_recorded(self):
        old = make_snapshot({"a": {"id": "int"}})
        new = make_snapshot({"a": {"id": "bigint"}})
        diff = diff_snapshots(old, new)
        assert diff.from_version == old.version_hash
        assert diff.to_version == new.version_hash

    def test_summary_no_changes(self):
        s = make_snapshot({"t": {"id": "int"}})
        diff = diff_snapshots(s, s)
        assert "No changes" in diff.summary()

    def test_summary_with_changes(self):
        old = make_snapshot({"t": {"id": "int"}})
        new = make_snapshot({"t": {"id": "bigint"}})
        diff = diff_snapshots(old, new)
        summary = diff.summary()
        assert "MODIFIED" in summary
        assert "id" in summary
