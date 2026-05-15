"""Tests for schemasnap.connector."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from schemasnap.connector import dialect_from_url, connect


# ---------------------------------------------------------------------------
# dialect_from_url
# ---------------------------------------------------------------------------

class TestDialectFromUrl:
    def test_postgresql_scheme(self):
        assert dialect_from_url("postgresql://user:pw@localhost/mydb") == "postgresql"

    def test_postgres_alias(self):
        assert dialect_from_url("postgres://user:pw@localhost/mydb") == "postgresql"

    def test_mysql_scheme(self):
        assert dialect_from_url("mysql://user:pw@localhost/mydb") == "mysql"

    def test_unsupported_scheme_raises(self):
        with pytest.raises(ValueError, match="Unsupported scheme"):
            dialect_from_url("sqlite:///local.db")

    def test_case_insensitive(self):
        assert dialect_from_url("POSTGRESQL://host/db") == "postgresql"


# ---------------------------------------------------------------------------
# connect — postgresql
# ---------------------------------------------------------------------------

class TestConnectPostgres:
    def test_returns_conn_and_dialect(self):
        mock_conn = MagicMock()
        mock_psycopg2 = MagicMock()
        mock_psycopg2.connect.return_value = mock_conn

        with patch.dict("sys.modules", {"psycopg2": mock_psycopg2}):
            conn, dialect = connect("postgresql://alice:secret@db.host:5432/appdb")

        assert dialect == "postgresql"
        assert conn is mock_conn
        mock_psycopg2.connect.assert_called_once_with(
            host="db.host",
            port=5432,
            user="alice",
            password="secret",
            dbname="appdb",
        )

    def test_default_port_5432(self):
        mock_psycopg2 = MagicMock()
        with patch.dict("sys.modules", {"psycopg2": mock_psycopg2}):
            connect("postgresql://u:p@host/db")
        call_kwargs = mock_psycopg2.connect.call_args[1]
        assert call_kwargs["port"] == 5432


# ---------------------------------------------------------------------------
# connect — mysql
# ---------------------------------------------------------------------------

class TestConnectMySQL:
    def test_returns_conn_and_dialect(self):
        mock_conn = MagicMock()
        mock_pymysql = MagicMock()
        mock_pymysql.connect.return_value = mock_conn

        with patch.dict("sys.modules", {"pymysql": mock_pymysql}):
            conn, dialect = connect("mysql://bob:pass@dbhost:3306/shop")

        assert dialect == "mysql"
        assert conn is mock_conn

    def test_default_port_3306(self):
        mock_pymysql = MagicMock()
        with patch.dict("sys.modules", {"pymysql": mock_pymysql}):
            connect("mysql://u:p@host/db")
        call_kwargs = mock_pymysql.connect.call_args[1]
        assert call_kwargs["port"] == 3306


# ---------------------------------------------------------------------------
# connect — unsupported
# ---------------------------------------------------------------------------

def test_connect_unsupported_scheme_raises():
    with pytest.raises(ValueError, match="Unsupported database scheme"):
        connect("sqlite:///test.db")


# ---------------------------------------------------------------------------
# _require helper — missing package
# ---------------------------------------------------------------------------

def test_connect_missing_driver_raises():
    import sys
    # Remove psycopg2 from modules if present so import fails
    with patch.dict("sys.modules", {"psycopg2": None}):
        with pytest.raises(ModuleNotFoundError, match="psycopg2"):
            connect("postgresql://u:p@host/db")
