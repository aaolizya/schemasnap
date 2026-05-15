"""Diff two SchemaSnapshots and produce a structured change report."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from schemasnap.snapshot import SchemaSnapshot


@dataclass
class ColumnChange:
    column: str
    change_type: str  # 'added', 'removed', 'modified'
    old_definition: Optional[str] = None
    new_definition: Optional[str] = None


@dataclass
class TableDiff:
    table: str
    change_type: str  # 'added', 'removed', 'modified'
    column_changes: List[ColumnChange] = field(default_factory=list)


@dataclass
class SchemaDiff:
    from_version: str
    to_version: str
    table_diffs: List[TableDiff] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return len(self.table_diffs) > 0

    def summary(self) -> str:
        if not self.has_changes:
            return f"No changes between {self.from_version} and {self.to_version}."
        lines = [f"Schema diff: {self.from_version} → {self.to_version}"]
        for td in self.table_diffs:
            lines.append(f"  [{td.change_type.upper()}] table: {td.table}")
            for cc in td.column_changes:
                lines.append(f"    [{cc.change_type.upper()}] column: {cc.column}")
        return "\n".join(lines)


def diff_snapshots(old: SchemaSnapshot, new: SchemaSnapshot) -> SchemaDiff:
    """Compare two snapshots and return a SchemaDiff."""
    old_tables: Dict[str, Dict] = old.tables
    new_tables: Dict[str, Dict] = new.tables

    table_diffs: List[TableDiff] = []

    removed_tables = set(old_tables) - set(new_tables)
    added_tables = set(new_tables) - set(old_tables)
    common_tables = set(old_tables) & set(new_tables)

    for table in sorted(removed_tables):
        table_diffs.append(TableDiff(table=table, change_type="removed"))

    for table in sorted(added_tables):
        table_diffs.append(TableDiff(table=table, change_type="added"))

    for table in sorted(common_tables):
        col_changes = _diff_columns(old_tables[table], new_tables[table])
        if col_changes:
            table_diffs.append(TableDiff(table=table, change_type="modified", column_changes=col_changes))

    return SchemaDiff(
        from_version=old.version_hash,
        to_version=new.version_hash,
        table_diffs=table_diffs,
    )


def _diff_columns(old_cols: Dict, new_cols: Dict) -> List[ColumnChange]:
    changes: List[ColumnChange] = []
    removed = set(old_cols) - set(new_cols)
    added = set(new_cols) - set(old_cols)
    common = set(old_cols) & set(new_cols)

    for col in sorted(removed):
        changes.append(ColumnChange(column=col, change_type="removed", old_definition=str(old_cols[col])))

    for col in sorted(added):
        changes.append(ColumnChange(column=col, change_type="added", new_definition=str(new_cols[col])))

    for col in sorted(common):
        if old_cols[col] != new_cols[col]:
            changes.append(ColumnChange(
                column=col,
                change_type="modified",
                old_definition=str(old_cols[col]),
                new_definition=str(new_cols[col]),
            ))
    return changes
