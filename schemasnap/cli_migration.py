"""CLI sub-commands for migration tracking."""

from __future__ import annotations

import argparse
import json
import sys

from schemasnap.migration_tracker import (
    clear_migrations,
    find_migration,
    list_migrations,
    record_migration,
)


def cmd_migration_record(args: argparse.Namespace) -> None:
    """Record a migration label against a snapshot file."""
    entry = record_migration(
        snap_dir=args.snap_dir,
        label=args.label,
        snapshot_file=args.snapshot_file,
        notes=args.notes or "",
    )
    print(f"Recorded migration '{entry.label}' -> {entry.snapshot_file} at {entry.recorded_at}")


def cmd_migration_list(args: argparse.Namespace) -> None:
    """List all recorded migrations."""
    entries = list_migrations(args.snap_dir)
    if not entries:
        print("No migrations recorded.")
        return
    for e in entries:
        notes_str = f"  # {e.notes}" if e.notes else ""
        print(f"[{e.recorded_at}] {e.label} -> {e.snapshot_file}{notes_str}")


def cmd_migration_show(args: argparse.Namespace) -> None:
    """Show details of a single migration by label."""
    entry = find_migration(args.snap_dir, args.label)
    if entry is None:
        print(f"Migration '{args.label}' not found.", file=sys.stderr)
        sys.exit(1)
    print(json.dumps(entry.to_dict(), indent=2))


def cmd_migration_clear(args: argparse.Namespace) -> None:
    """Remove the entire migration index."""
    clear_migrations(args.snap_dir)
    print("Migration index cleared.")


def build_migration_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("migration", help="Manage migration labels")
    sp = p.add_subparsers(dest="migration_cmd", required=True)

    rec = sp.add_parser("record", help="Record a migration label")
    rec.add_argument("label", help="Migration label (e.g. 0012_add_users)")
    rec.add_argument("snapshot_file", help="Snapshot filename to associate")
    rec.add_argument("--notes", default="", help="Optional notes")
    rec.add_argument("--snap-dir", default="snapshots", dest="snap_dir")
    rec.set_defaults(func=cmd_migration_record)

    ls = sp.add_parser("list", help="List all migrations")
    ls.add_argument("--snap-dir", default="snapshots", dest="snap_dir")
    ls.set_defaults(func=cmd_migration_list)

    show = sp.add_parser("show", help="Show a migration by label")
    show.add_argument("label", help="Migration label to look up")
    show.add_argument("--snap-dir", default="snapshots", dest="snap_dir")
    show.set_defaults(func=cmd_migration_show)

    clr = sp.add_parser("clear", help="Clear migration index")
    clr.add_argument("--snap-dir", default="snapshots", dest="snap_dir")
    clr.set_defaults(func=cmd_migration_clear)
