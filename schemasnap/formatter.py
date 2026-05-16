"""Utilities for formatting schema snapshots and diffs as human-readable tables."""

from __future__ import annotations

from typing import List

from schemasnap.differ import SchemaDiff, TableDiff, ColumnChange


def _pad(text: str, width: int) -> str:
    return text.ljust(width)


def _divider(widths: List[int], char: str = "-") -> str:
    return "+" + "+".join(char * (w + 2) for w in widths) + "+"


def _row(cells: List[str], widths: List[int]) -> str:
    padded = [" " + _pad(str(c), w) + " " for c, w in zip(cells, widths)]
    return "|" + "|".join(padded) + "|"


def format_column_changes(changes: List[ColumnChange]) -> str:
    """Render a list of ColumnChange objects as an ASCII table."""
    if not changes:
        return "  (no column changes)"

    headers = ["column", "field", "before", "after"]
    rows = [
        [c.column_name, c.field, str(c.before), str(c.after)]
        for c in changes
    ]
    all_rows = [headers] + rows
    widths = [
        max(len(r[i]) for r in all_rows)
        for i in range(len(headers))
    ]

    lines = [_divider(widths), _row(headers, widths), _divider(widths, "=")]
    for r in rows:
        lines.append(_row(r, widths))
    lines.append(_divider(widths))
    return "\n".join(lines)


def format_table_diff(table_name: str, diff: TableDiff) -> str:
    """Render a single TableDiff as a formatted block."""
    lines = [f"Table: {table_name}"]
    if diff.added_columns:
        lines.append(f"  Added columns   : {', '.join(diff.added_columns)}")
    if diff.removed_columns:
        lines.append(f"  Removed columns : {', '.join(diff.removed_columns)}")
    if diff.changed_columns:
        lines.append("  Changed columns:")
        lines.append(format_column_changes(diff.changed_columns))
    return "\n".join(lines)


def format_diff_table(diff: SchemaDiff) -> str:
    """Render a full SchemaDiff as a formatted multi-section string."""
    if not diff.has_changes():
        return "No schema changes detected."

    sections: List[str] = []

    if diff.added_tables:
        sections.append("Added tables: " + ", ".join(diff.added_tables))

    if diff.removed_tables:
        sections.append("Removed tables: " + ", ".join(diff.removed_tables))

    for table_name, table_diff in diff.modified_tables.items():
        sections.append(format_table_diff(table_name, table_diff))

    return "\n\n".join(sections)
