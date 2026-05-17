"""Load a :class:`FilterConfig` from a YAML or JSON file."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from schemasnap.filter import FilterConfig


def _load_raw(path: str | Path) -> Dict[str, Any]:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Filter config file not found: {path}")
    text = path.read_text()
    try:
        import yaml  # optional dependency
        return yaml.safe_load(text) or {}
    except ImportError:
        return json.loads(text)


def load_filter_config(path: str | Path) -> FilterConfig:
    """Parse *path* (JSON or YAML) and return a :class:`FilterConfig`.

    Expected structure::

        include_tables: ["orders", "users"]
        exclude_tables: ["tmp_*"]
        include_columns:
          orders: ["id", "status"]
        exclude_columns:
          users: ["password_hash"]
    """
    raw = _load_raw(path)
    return FilterConfig(
        include_tables=raw.get("include_tables", []),
        exclude_tables=raw.get("exclude_tables", []),
        include_columns=raw.get("include_columns", {}),
        exclude_columns=raw.get("exclude_columns", {}),
    )
