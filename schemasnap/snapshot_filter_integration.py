"""Helpers that tie the filter layer into the snapshot/extractor pipeline."""

from __future__ import annotations

from typing import Optional

from schemasnap.filter import FilterConfig, apply_filter
from schemasnap.snapshot import SchemaSnapshot


def snapshot_with_filter(
    tables: dict,
    label: str,
    config: Optional[FilterConfig] = None,
) -> SchemaSnapshot:
    """Build a :class:`SchemaSnapshot` after applying *config* to *tables*.

    This is the recommended entry-point when you want to capture only a
    subset of the schema.

    Args:
        tables:  Raw tables dict as returned by :func:`schemasnap.extractor.extract_schema`.
        label:   Human-readable label for the snapshot (e.g. ``"prod-2024-01-15"``).
        config:  Optional :class:`FilterConfig`; if *None* all tables are included.

    Returns:
        A new :class:`SchemaSnapshot` containing only the filtered tables.
    """
    filtered = apply_filter(tables, config)
    return SchemaSnapshot(label=label, tables=filtered)


def filter_snapshot(
    snapshot: SchemaSnapshot,
    config: Optional[FilterConfig] = None,
) -> SchemaSnapshot:
    """Return a *new* snapshot derived from *snapshot* with *config* applied.

    Useful for post-hoc filtering of already-captured snapshots without
    re-connecting to the database.

    Args:
        snapshot: An existing :class:`SchemaSnapshot`.
        config:   Optional :class:`FilterConfig`.

    Returns:
        A new :class:`SchemaSnapshot` with the same label and filtered tables.
    """
    filtered = apply_filter(snapshot.tables, config)
    return SchemaSnapshot(label=snapshot.label, tables=filtered)
