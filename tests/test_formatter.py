"""Tests for schemasnap.formatter."""

from __future__ import annotations

import pytest

from schemasnap.differ import ColumnChange, TableDiff, SchemaDiff
from schemasnap.formatter import (
    format_column_changes,
    format_table_diff,
    format_diff_table,
)


def _make_diff(
    added=None, removed=None, modified=None
) -> SchemaDiff:
    return SchemaDiff(
        added_tables=added or [],
        removed_tables=removed or [],
        modified_tables=modified or {},
    )


class TestFormatColumnChanges:
    def test_empty_returns_no_changes_message(self):
        result = format_column_changes([])
        assert "no column changes" in result

    def test_single_change_contains_column_name(self):
        change = ColumnChange(column_name="email", field="type", before="varchar", after="text")
        result = format_column_changes([change])
        assert "email" in result
        assert "type" in result
        assert "varchar" in result
        assert "text" in result

    def test_output_has_table_borders(self):
        change = ColumnChange(column_name="id", field="nullable", before=True, after=False)
        result = format_column_changes([change])
        assert "+" in result
        assert "|" in result

    def test_multiple_changes_all_present(self):
        changes = [
            ColumnChange(column_name="a", field="type", before="int", after="bigint"),
            ColumnChange(column_name="b", field="nullable", before=False, after=True),
        ]
        result = format_column_changes(changes)
        assert "a" in result
        assert "b" in result


class TestFormatTableDiff:
    def test_added_columns_listed(self):
        diff = TableDiff(added_columns=["new_col"], removed_columns=[], changed_columns=[])
        result = format_table_diff("users", diff)
        assert "new_col" in result
        assert "Added" in result

    def test_removed_columns_listed(self):
        diff = TableDiff(added_columns=[], removed_columns=["old_col"], changed_columns=[])
        result = format_table_diff("orders", diff)
        assert "old_col" in result
        assert "Removed" in result

    def test_table_name_in_output(self):
        diff = TableDiff(added_columns=["x"], removed_columns=[], changed_columns=[])
        result = format_table_diff("products", diff)
        assert "products" in result


class TestFormatDiffTable:
    def test_no_changes_returns_no_changes_message(self):
        diff = _make_diff()
        result = format_diff_table(diff)
        assert "No schema changes" in result

    def test_added_tables_shown(self):
        diff = _make_diff(added=["new_table"])
        result = format_diff_table(diff)
        assert "new_table" in result
        assert "Added" in result

    def test_removed_tables_shown(self):
        diff = _make_diff(removed=["old_table"])
        result = format_diff_table(diff)
        assert "old_table" in result
        assert "Removed" in result

    def test_modified_table_section_present(self):
        table_diff = TableDiff(
            added_columns=["score"],
            removed_columns=[],
            changed_columns=[],
        )
        diff = _make_diff(modified={"events": table_diff})
        result = format_diff_table(diff)
        assert "events" in result
        assert "score" in result
