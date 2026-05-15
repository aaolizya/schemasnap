"""Tests for schemasnap.reporter."""

import json
import pytest
from schemasnap.snapshot import SchemaSnapshot
from schemasnap.differ import diff_snapshots
from schemasnap.reporter import render_text, render_json, render_markdown


def make_diff():
    old = SchemaSnapshot(db_type="postgresql", db_name="db", tables={
        "users": {"id": "integer", "email": "varchar(100)"},
        "legacy": {"id": "integer"},
    })
    new = SchemaSnapshot(db_type="postgresql", db_name="db", tables={
        "users": {"id": "integer", "email": "varchar(255)"},
        "orders": {"id": "integer"},
    })
    return diff_snapshots(old, new)


class TestRenderText:
    def test_returns_string(self):
        diff = make_diff()
        result = render_text(diff)
        assert isinstance(result, str)

    def test_contains_table_names(self):
        diff = make_diff()
        result = render_text(diff)
        assert "legacy" in result or "orders" in result


class TestRenderJson:
    def test_returns_valid_json(self):
        diff = make_diff()
        result = render_json(diff)
        parsed = json.loads(result)
        assert "from_version" in parsed
        assert "to_version" in parsed
        assert "tables" in parsed

    def test_has_changes_flag(self):
        diff = make_diff()
        parsed = json.loads(render_json(diff))
        assert parsed["has_changes"] is True

    def test_no_changes_json(self):
        s = SchemaSnapshot(db_type="postgresql", db_name="db", tables={"t": {"id": "int"}})
        diff = diff_snapshots(s, s)
        parsed = json.loads(render_json(diff))
        assert parsed["has_changes"] is False
        assert parsed["tables"] == []

    def test_column_entries_present(self):
        diff = make_diff()
        parsed = json.loads(render_json(diff))
        modified = [t for t in parsed["tables"] if t["change_type"] == "modified"]
        assert len(modified) > 0
        assert len(modified[0]["columns"]) > 0


class TestRenderMarkdown:
    def test_returns_string(self):
        diff = make_diff()
        result = render_markdown(diff)
        assert isinstance(result, str)

    def test_contains_markdown_heading(self):
        diff = make_diff()
        result = render_markdown(diff)
        assert "## Schema Diff" in result

    def test_no_changes_message(self):
        s = SchemaSnapshot(db_type="postgresql", db_name="db", tables={"t": {"id": "int"}})
        diff = diff_snapshots(s, s)
        result = render_markdown(diff)
        assert "No schema changes" in result

    def test_table_section_present(self):
        diff = make_diff()
        result = render_markdown(diff)
        assert "`orders`" in result or "`legacy`" in result
