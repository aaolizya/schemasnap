"""Tests for the snapshot capture and data model."""

import json
from unittest.mock import MagicMock, patch

import pytest

from schemasnap.snapshot import (
    SchemaSnapshot,
    capture_mysql_schema,
    capture_postgres_schema,
)


SAMPLE_TABLES = {
    "users": [
        {"name": "id", "type": "integer", "nullable": "NO", "default": None},
        {"name": "email", "type": "character varying", "nullable": "NO", "default": None},
    ],
    "posts": [
        {"name": "id", "type": "integer", "nullable": "NO", "default": None},
        {"name": "title", "type": "text", "nullable": "YES", "default": None},
    ],
}


class TestSchemaSnapshot:
    def test_version_hash_computed_on_init(self):
        snap = SchemaSnapshot(db_type="postgresql", db_name="mydb", tables=SAMPLE_TABLES)
        assert len(snap.version_hash) == 12

    def test_same_tables_same_hash(self):
        snap1 = SchemaSnapshot(db_type="postgresql", db_name="mydb", tables=SAMPLE_TABLES)
        snap2 = SchemaSnapshot(db_type="postgresql", db_name="mydb", tables=SAMPLE_TABLES)
        assert snap1.version_hash == snap2.version_hash

    def test_different_tables_different_hash(self):
        snap1 = SchemaSnapshot(db_type="postgresql", db_name="mydb", tables=SAMPLE_TABLES)
        snap2 = SchemaSnapshot(db_type="postgresql", db_name="mydb", tables={})
        assert snap1.version_hash != snap2.version_hash

    def test_round_trip_serialization(self):
        snap = SchemaSnapshot(db_type="mysql", db_name="shop", tables=SAMPLE_TABLES)
        restored = SchemaSnapshot.from_dict(snap.to_dict())
        assert restored.db_type == snap.db_type
        assert restored.db_name == snap.db_name
        assert restored.tables == snap.tables
        assert restored.version_hash == snap.version_hash

    def test_to_dict_contains_required_keys(self):
        snap = SchemaSnapshot(db_type="postgresql", db_name="mydb", tables={})
        d = snap.to_dict()
        for key in ("db_type", "db_name", "captured_at", "version_hash", "tables"):
            assert key in d


class TestCapturePostgres:
    def _make_connection(self, table_rows, column_rows):
        cursor = MagicMock()
        cursor.fetchall.side_effect = [table_rows, column_rows]
        conn = MagicMock()
        conn.cursor.return_value = cursor
        return conn

    def test_returns_table_dict(self):
        conn = self._make_connection(
            [("users",)],
            [("id", "integer", "NO", None)],
        )
        result = capture_postgres_schema(conn)
        assert "users" in result
        assert result["users"][0]["name"] == "id"

    def test_empty_schema(self):
        conn = self._make_connection([], [])
        result = capture_postgres_schema(conn)
        assert result == {}


class TestCaptureMySQL:
    def _make_connection(self, table_rows, column_rows):
        cursor = MagicMock()
        cursor.fetchall.side_effect = [table_rows, column_rows]
        conn = MagicMock()
        conn.cursor.return_value = cursor
        return conn

    def test_returns_table_dict(self):
        conn = self._make_connection(
            [("orders",)],
            [("id", "int", "NO", None)],
        )
        result = capture_mysql_schema(conn, "shopdb")
        assert "orders" in result
        assert result["orders"][0]["type"] == "int"
