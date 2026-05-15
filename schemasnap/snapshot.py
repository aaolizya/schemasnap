"""Schema snapshot capture module for PostgreSQL and MySQL."""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class SchemaSnapshot:
    """Represents a captured snapshot of a database schema."""

    db_type: str
    db_name: str
    captured_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    tables: dict[str, Any] = field(default_factory=dict)
    version_hash: str = ""

    def __post_init__(self):
        if not self.version_hash:
            self.version_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        """Compute a deterministic hash of the schema structure."""
        schema_str = json.dumps(self.tables, sort_keys=True)
        return hashlib.sha256(schema_str.encode()).hexdigest()[:12]

    def to_dict(self) -> dict:
        return {
            "db_type": self.db_type,
            "db_name": self.db_name,
            "captured_at": self.captured_at,
            "version_hash": self.version_hash,
            "tables": self.tables,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SchemaSnapshot":
        return cls(
            db_type=data["db_type"],
            db_name=data["db_name"],
            captured_at=data["captured_at"],
            tables=data["tables"],
            version_hash=data["version_hash"],
        )


def capture_postgres_schema(connection) -> dict[str, Any]:
    """Capture table/column schema from a PostgreSQL connection."""
    tables: dict[str, Any] = {}
    cursor = connection.cursor()

    cursor.execute("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        ORDER BY table_name;
    """)
    table_names = [row[0] for row in cursor.fetchall()]

    for table in table_names:
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
            ORDER BY ordinal_position;
        """, (table,))
        tables[table] = [
            {"name": r[0], "type": r[1], "nullable": r[2], "default": r[3]}
            for r in cursor.fetchall()
        ]

    cursor.close()
    return tables


def capture_mysql_schema(connection, db_name: str) -> dict[str, Any]:
    """Capture table/column schema from a MySQL connection."""
    tables: dict[str, Any] = {}
    cursor = connection.cursor()

    cursor.execute("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = %s AND table_type = 'BASE TABLE'
        ORDER BY table_name;
    """, (db_name,))
    table_names = [row[0] for row in cursor.fetchall()]

    for table in table_names:
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position;
        """, (db_name, table))
        tables[table] = [
            {"name": r[0], "type": r[1], "nullable": r[2], "default": r[3]}
            for r in cursor.fetchall()
        ]

    cursor.close()
    return tables
