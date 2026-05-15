"""Database schema extraction for PostgreSQL and MySQL."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ColumnInfo:
    name: str
    data_type: str
    nullable: bool
    default: Optional[str] = None
    extra: Optional[str] = None  # e.g. AUTO_INCREMENT, ON UPDATE, etc.

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "data_type": self.data_type,
            "nullable": self.nullable,
            "default": self.default,
            "extra": self.extra,
        }


def _extract_postgres(conn: Any) -> Dict[str, List[Dict[str, Any]]]:
    """Extract schema from a PostgreSQL connection (psycopg2-compatible)."""
    tables: Dict[str, List[Dict[str, Any]]] = {}
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_type = 'BASE TABLE'
            ORDER BY table_name;
            """
        )
        table_names = [row[0] for row in cur.fetchall()]

        for table in table_names:
            cur.execute(
                """
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = %s
                ORDER BY ordinal_position;
                """,
                (table,),
            )
            columns = [
                ColumnInfo(
                    name=row[0],
                    data_type=row[1],
                    nullable=(row[2] == "YES"),
                    default=row[3],
                ).to_dict()
                for row in cur.fetchall()
            ]
            tables[table] = columns
    return tables


def _extract_mysql(conn: Any) -> Dict[str, List[Dict[str, Any]]]:
    """Extract schema from a MySQL connection (mysql-connector or PyMySQL)."""
    tables: Dict[str, List[Dict[str, Any]]] = {}
    with conn.cursor() as cur:
        cur.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = DATABASE() AND table_type = 'BASE TABLE' "
            "ORDER BY table_name;"
        )
        table_names = [row[0] for row in cur.fetchall()]

        for table in table_names:
            cur.execute(
                "SELECT column_name, data_type, is_nullable, column_default, extra "
                "FROM information_schema.columns "
                "WHERE table_schema = DATABASE() AND table_name = %s "
                "ORDER BY ordinal_position;",
                (table,),
            )
            columns = [
                ColumnInfo(
                    name=row[0],
                    data_type=row[1],
                    nullable=(row[2] == "YES"),
                    default=row[3],
                    extra=row[4] or None,
                ).to_dict()
                for row in cur.fetchall()
            ]
            tables[table] = columns
    return tables


def extract_schema(conn: Any, dialect: str) -> Dict[str, List[Dict[str, Any]]]:
    """Extract schema tables and columns for the given dialect.

    Args:
        conn: An open database connection.
        dialect: Either ``'postgresql'`` or ``'mysql'``.

    Returns:
        A mapping of table name -> list of column dicts.
    """
    if dialect == "postgresql":
        return _extract_postgres(conn)
    elif dialect == "mysql":
        return _extract_mysql(conn)
    else:
        raise ValueError(f"Unsupported dialect: {dialect!r}. Use 'postgresql' or 'mysql'.")
