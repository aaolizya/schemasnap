"""Database connection factory for schemasnap."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse


def _require(package: str) -> Any:
    """Import *package* and raise a helpful error if it is not installed."""
    import importlib

    try:
        return importlib.import_module(package)
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            f"Required package '{package}' is not installed. "
            f"Install it with: pip install {package}"
        ) from exc


def connect(url: str) -> tuple[Any, str]:
    """Open a database connection from a URL and return ``(conn, dialect)``.

    Supported URL schemes:
      - ``postgresql://user:pass@host/dbname``
      - ``mysql://user:pass@host/dbname``

    Returns:
        A tuple of ``(connection, dialect_string)`` where *dialect_string* is
        either ``'postgresql'`` or ``'mysql'``.

    Raises:
        ValueError: For unsupported URL schemes.
        ModuleNotFoundError: If the required driver is not installed.
    """
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()

    if scheme in ("postgresql", "postgres"):
        psycopg2 = _require("psycopg2")
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            user=parsed.username,
            password=parsed.password,
            dbname=parsed.path.lstrip("/"),
        )
        return conn, "postgresql"

    elif scheme == "mysql":
        pymysql = _require("pymysql")
        conn = pymysql.connect(
            host=parsed.hostname,
            port=parsed.port or 3306,
            user=parsed.username,
            password=parsed.password or "",
            database=parsed.path.lstrip("/"),
            cursorclass=pymysql.cursors.DictCursor
            if hasattr(pymysql, "cursors")
            else None,
        )
        return conn, "mysql"

    else:
        raise ValueError(
            f"Unsupported database scheme: {scheme!r}. "
            "Use 'postgresql://' or 'mysql://'."
        )


def dialect_from_url(url: str) -> str:
    """Return the dialect string for *url* without opening a connection."""
    scheme = urlparse(url).scheme.lower()
    if scheme in ("postgresql", "postgres"):
        return "postgresql"
    if scheme == "mysql":
        return "mysql"
    raise ValueError(f"Unsupported scheme: {scheme!r}")
