"""Export snapshots and diffs to various file formats (JSON, CSV, Markdown, HTML)."""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import Optional

from schemasnap.differ import SchemaDiff
from schemasnap.reporter import render_markdown, render_json
from schemasnap.snapshot import SchemaSnapshot


# ---------------------------------------------------------------------------
# Snapshot export
# ---------------------------------------------------------------------------

def export_snapshot_json(snapshot: SchemaSnapshot, dest: Path) -> None:
    """Write a snapshot to *dest* as a pretty-printed JSON file."""
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("w", encoding="utf-8") as fh:
        json.dump(snapshot.to_dict(), fh, indent=2)


def export_snapshot_csv(snapshot: SchemaSnapshot, dest: Path) -> None:
    """Write a snapshot's column inventory to *dest* as a CSV file.

    Each row represents one column with the fields:
    ``table``, ``column``, ``type``, ``nullable``, ``default``.
    """
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = ["table", "column", "type", "nullable", "default"]
    with dest.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for table_name, columns in sorted(snapshot.tables.items()):
            for col in columns:
                writer.writerow(
                    {
                        "table": table_name,
                        "column": col.get("name", ""),
                        "type": col.get("type", ""),
                        "nullable": col.get("nullable", ""),
                        "default": col.get("default", ""),
                    }
                )


# ---------------------------------------------------------------------------
# Diff export
# ---------------------------------------------------------------------------

def export_diff_json(diff: SchemaDiff, dest: Path) -> None:
    """Write a *SchemaDiff* to *dest* as a JSON file."""
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("w", encoding="utf-8") as fh:
        fh.write(render_json(diff))


def export_diff_markdown(diff: SchemaDiff, dest: Path) -> None:
    """Write a *SchemaDiff* to *dest* as a Markdown file."""
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("w", encoding="utf-8") as fh:
        fh.write(render_markdown(diff))


def export_diff_html(diff: SchemaDiff, dest: Path) -> None:
    """Write a *SchemaDiff* to *dest* as a minimal HTML report."""
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)

    buf = io.StringIO()
    buf.write("<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n")
    buf.write("  <meta charset=\"UTF-8\">\n")
    buf.write("  <title>SchemaSnap Diff Report</title>\n")
    buf.write("  <style>\n")
    buf.write("    body { font-family: monospace; padding: 2rem; }\n")
    buf.write("    h1 { color: #333; }\n")
    buf.write("    h2 { color: #555; border-bottom: 1px solid #ccc; }\n")
    buf.write("    .added { color: green; } .removed { color: red; }\n")
    buf.write("    .changed { color: darkorange; }\n")
    buf.write("    pre { background: #f4f4f4; padding: 1rem; border-radius: 4px; }\n")
    buf.write("  </style>\n</head>\n<body>\n")
    buf.write("  <h1>SchemaSnap &mdash; Schema Diff Report</h1>\n")

    if not diff.has_changes():
        buf.write("  <p>No schema changes detected.</p>\n")
    else:
        if diff.added_tables:
            buf.write("  <h2 class=\"added\">Added Tables</h2>\n  <ul>\n")
            for t in sorted(diff.added_tables):
                buf.write(f"    <li class=\"added\">{t}</li>\n")
            buf.write("  </ul>\n")

        if diff.removed_tables:
            buf.write("  <h2 class=\"removed\">Removed Tables</h2>\n  <ul>\n")
            for t in sorted(diff.removed_tables):
                buf.write(f"    <li class=\"removed\">{t}</li>\n")
            buf.write("  </ul>\n")

        if diff.modified_tables:
            buf.write("  <h2 class=\"changed\">Modified Tables</h2>\n")
            for table_name, table_diff in sorted(diff.modified_tables.items()):
                buf.write(f"  <h3>{table_name}</h3>\n  <pre>\n")
                if table_diff.added_columns:
                    buf.write("Added columns:\n")
                    for c in table_diff.added_columns:
                        buf.write(f"  + {c}\n")
                if table_diff.removed_columns:
                    buf.write("Removed columns:\n")
                    for c in table_diff.removed_columns:
                        buf.write(f"  - {c}\n")
                if table_diff.changed_columns:
                    buf.write("Changed columns:\n")
                    for col_name, change in table_diff.changed_columns.items():
                        buf.write(
                            f"  ~ {col_name}: "
                            f"{change.old_value!r} -> {change.new_value!r}\n"
                        )
                buf.write("  </pre>\n")

    buf.write("</body>\n</html>\n")

    with dest.open("w", encoding="utf-8") as fh:
        fh.write(buf.getvalue())


# ---------------------------------------------------------------------------
# Convenience dispatcher
# ---------------------------------------------------------------------------

_DIFF_EXPORTERS = {
    "json": export_diff_json,
    "md": export_diff_markdown,
    "markdown": export_diff_markdown,
    "html": export_diff_html,
}

_SNAPSHOT_EXPORTERS = {
    "json": export_snapshot_json,
    "csv": export_snapshot_csv,
}


def export_diff(diff: SchemaDiff, dest: Path, fmt: Optional[str] = None) -> None:
    """Export *diff* to *dest*, inferring format from the file extension when *fmt* is omitted."""
    fmt = (fmt or Path(dest).suffix.lstrip(".")).lower()
    exporter = _DIFF_EXPORTERS.get(fmt)
    if exporter is None:
        raise ValueError(
            f"Unsupported diff export format {fmt!r}. "
            f"Choose from: {', '.join(_DIFF_EXPORTERS)}"
        )
    exporter(diff, dest)


def export_snapshot(snapshot: SchemaSnapshot, dest: Path, fmt: Optional[str] = None) -> None:
    """Export *snapshot* to *dest*, inferring format from the file extension when *fmt* is omitted."""
    fmt = (fmt or Path(dest).suffix.lstrip(".")).lower()
    exporter = _SNAPSHOT_EXPORTERS.get(fmt)
    if exporter is None:
        raise ValueError(
            f"Unsupported snapshot export format {fmt!r}. "
            f"Choose from: {', '.join(_SNAPSHOT_EXPORTERS)}"
        )
    exporter(snapshot, dest)
