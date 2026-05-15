"""Render a SchemaDiff to various output formats."""

import json
from schemasnap.differ import SchemaDiff


def render_text(diff: SchemaDiff) -> str:
    """Return a human-readable text report of the diff."""
    return diff.summary()


def render_json(diff: SchemaDiff) -> str:
    """Return a JSON-serialisable representation of the diff."""
    data = {
        "from_version": diff.from_version,
        "to_version": diff.to_version,
        "has_changes": diff.has_changes,
        "tables": [],
    }
    for td in diff.table_diffs:
        table_entry = {
            "table": td.table,
            "change_type": td.change_type,
            "columns": [
                {
                    "column": cc.column,
                    "change_type": cc.change_type,
                    "old_definition": cc.old_definition,
                    "new_definition": cc.new_definition,
                }
                for cc in td.column_changes
            ],
        }
        data["tables"].append(table_entry)
    return json.dumps(data, indent=2)


def render_markdown(diff: SchemaDiff) -> str:
    """Return a Markdown-formatted diff report."""
    lines = [
        f"## Schema Diff",
        f"",
        f"| | |",
        f"|---|---|" ,
        f"| **From** | `{diff.from_version}` |",
        f"| **To**   | `{diff.to_version}` |",
        f"",
    ]
    if not diff.has_changes:
        lines.append("_No schema changes detected._")
        return "\n".join(lines)

    for td in diff.table_diffs:
        lines.append(f"### `{td.table}` — {td.change_type}")
        if td.column_changes:
            lines.append("")
            lines.append("| Column | Change | Old | New |")
            lines.append("|--------|--------|-----|-----|")
            for cc in td.column_changes:
                old = cc.old_definition or ""
                new = cc.new_definition or ""
                lines.append(f"| `{cc.column}` | {cc.change_type} | {old} | {new} |")
        lines.append("")
    return "\n".join(lines)
