"""Schema filtering utilities — include/exclude tables and columns by pattern."""

from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class FilterConfig:
    """Configuration for table/column inclusion and exclusion filters."""

    include_tables: List[str] = field(default_factory=list)
    exclude_tables: List[str] = field(default_factory=list)
    include_columns: Dict[str, List[str]] = field(default_factory=dict)
    exclude_columns: Dict[str, List[str]] = field(default_factory=dict)

    def table_is_included(self, table_name: str) -> bool:
        """Return True if *table_name* passes the include/exclude rules."""
        if self.include_tables:
            if not any(fnmatch.fnmatch(table_name, p) for p in self.include_tables):
                return False
        if self.exclude_tables:
            if any(fnmatch.fnmatch(table_name, p) for p in self.exclude_tables):
                return False
        return True

    def column_is_included(self, table_name: str, column_name: str) -> bool:
        """Return True if *column_name* passes the include/exclude rules for *table_name*."""
        inc_patterns = self.include_columns.get(table_name, [])
        exc_patterns = self.exclude_columns.get(table_name, [])

        if inc_patterns:
            if not any(fnmatch.fnmatch(column_name, p) for p in inc_patterns):
                return False
        if exc_patterns:
            if any(fnmatch.fnmatch(column_name, p) for p in exc_patterns):
                return False
        return True


def apply_filter(
    tables: Dict[str, List[dict]],
    config: Optional[FilterConfig] = None,
) -> Dict[str, List[dict]]:
    """Return a new tables dict with tables/columns removed per *config*.

    Args:
        tables: Mapping of table_name -> list of column dicts (as produced by extractor).
        config: A :class:`FilterConfig` instance; if *None* the original dict is returned.
    """
    if config is None:
        return tables

    filtered: Dict[str, List[dict]] = {}
    for table_name, columns in tables.items():
        if not config.table_is_included(table_name):
            continue
        filtered[table_name] = [
            col for col in columns
            if config.column_is_included(table_name, col.get("name", ""))
        ]
    return filtered
