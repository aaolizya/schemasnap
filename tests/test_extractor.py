"""Tests for schemasnap.extractor using mock database connections."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from schemasnap.extractor import ColumnInfo, extract_schema


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_pg_conn(table_rows, column_rows_by_table):
    """Build a mock psycopg2-style connection."""
    cursor = MagicMock()
    call_count = [0]

    def fetchall_side_effect():
        idx = call_count[0]
        call_count[0] += 1
        if idx == 0:
            return table_rows
        table = cursor.execute.call_args_list[idx][0][1][0]
        return column_rows_by_table.get(table, [])

    cursor.fetchall.side_effect = fetchall_side_effect
    cursor.__enter__ = lambda s: cursor
    cursor.__exit__ = MagicMock(return_value=False)
    conn = MagicMock()
    conn.cursor.return_value = cursor
    return conn


# ---------------------------------------------------------------------------
# ColumnInfo tests
# ---------------------------------------------------------------------------

class TestColumnInfo:
    def test_to_dict_contains_all_keys(self):
        col = ColumnInfo(name="id", data_type="integer", nullable=False, default="1")
        d = col.to_dict()
        assert set(d.keys()) == {"name", "data_type", "nullable", "default", "extra"}

    def test_nullable_false(self):
        col = ColumnInfo(name="x", data_type="text", nullable=False)
        assert col.to_dict()["nullable"] is False

    def test_extra_defaults_to_none(self):
        col = ColumnInfo(name="y", data_type="varchar", nullable=True)
        assert col.extra is None


# ---------------------------------------------------------------------------
# extract_schema — unsupported dialect
# ---------------------------------------------------------------------------

def test_unsupported_dialect_raises():
    with pytest.raises(ValueError, match="Unsupported dialect"):
        extract_schema(MagicMock(), "sqlite")


# ---------------------------------------------------------------------------
# PostgreSQL extraction
# ---------------------------------------------------------------------------

class TestExtractPostgres:
    def _build_conn(self, tables, columns_map):
        """Simulate cursor returning table list then column rows per table."""
        cursor = MagicMock()
        results = [tables] + [columns_map.get(t[0], []) for t in tables]
        cursor.fetchall.side_effect = results
        cursor.__enter__ = lambda s: cursor
        cursor.__exit__ = MagicMock(return_value=False)
        conn = MagicMock()
        conn.cursor.return_value = cursor
        return conn

    def test_returns_empty_when_no_tables(self):
        conn = self._build_conn([], {})
        result = extract_schema(conn, "postgresql")
        assert result == {}

    def test_single_table_single_column(self):
        conn = self._build_conn(
            [("users",)],
            {"users": [("id", "integer", "NO", None)]},
        )
        result = extract_schema(conn, "postgresql")
        assert "users" in result
        assert result["users"][0]["name"] == "id"
        assert result["users"][0]["nullable"] is False

    def test_nullable_yes_maps_to_true(self):
        conn = self._build_conn(
            [("orders",)],
            {"orders": [("note", "text", "YES", None)]},
        )
        result = extract_schema(conn, "postgresql")
        assert result["orders"][0]["nullable"] is True


# ---------------------------------------------------------------------------
# MySQL extraction
# ---------------------------------------------------------------------------

class TestExtractMySQL:
    def _build_conn(self, tables, columns_map):
        cursor = MagicMock()
        results = [tables] + [columns_map.get(t[0], []) for t in tables]
        cursor.fetchall.side_effect = results
        cursor.__enter__ = lambda s: cursor
        cursor.__exit__ = MagicMock(return_value=False)
        conn = MagicMock()
        conn.cursor.return_value = cursor
        return conn

    def test_extra_field_captured(self):
        conn = self._build_conn(
            [("products",)],
            {"products": [("id", "int", "NO", None, "auto_increment")]},
        )
        result = extract_schema(conn, "mysql")
        assert result["products"][0]["extra"] == "auto_increment"

    def test_empty_extra_becomes_none(self):
        conn = self._build_conn(
            [("items",)],
            {"items": [("name", "varchar", "YES", None, "")]},
        )
        result = extract_schema(conn, "mysql")
        assert result["items"][0]["extra"] is None
