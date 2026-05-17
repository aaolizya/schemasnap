"""CLI commands for managing schema snapshots.

Provides subcommands to capture, list, show, and compare snapshots
without going through the full watcher/scheduler pipeline.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from schemasnap.connector import connect, dialect_from_url
from schemasnap.extractor import extract_schema
from schemasnap.snapshot import SchemaSnapshot
from schemasnap.storage import (
    list_snapshots,
    load_latest_snapshot,
    load_snapshot,
    save_snapshot,
)
from schemasnap.differ import diff_snapshots
from schemasnap.reporter import render_text, render_json, render_markdown


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------

def cmd_snapshot_capture(args: argparse.Namespace) -> None:
    """Connect to the database and capture a new schema snapshot."""
    snap_dir = Path(args.snap_dir)
    snap_dir.mkdir(parents=True, exist_ok=True)

    try:
        conn = connect(args.url)
    except Exception as exc:  # pragma: no cover
        print(f"error: could not connect to database: {exc}", file=sys.stderr)
        sys.exit(1)

    dialect = dialect_from_url(args.url)
    tables = extract_schema(conn, dialect)
    snapshot = SchemaSnapshot(tables=tables)
    path = save_snapshot(snapshot, snap_dir)
    print(f"Snapshot saved: {path}")


def cmd_snapshot_list(args: argparse.Namespace) -> None:
    """List all stored snapshots in chronological order."""
    snap_dir = Path(args.snap_dir)
    snapshots = list_snapshots(snap_dir)

    if not snapshots:
        print("No snapshots found.")
        return

    for entry in snapshots:
        print(entry)


def cmd_snapshot_show(args: argparse.Namespace) -> None:
    """Print the contents of a specific snapshot as JSON."""
    snap_dir = Path(args.snap_dir)

    if args.snapshot_id == "latest":
        snapshot = load_latest_snapshot(snap_dir)
        if snapshot is None:
            print("error: no snapshots found.", file=sys.stderr)
            sys.exit(1)
    else:
        snapshot = load_snapshot(snap_dir, args.snapshot_id)
        if snapshot is None:
            print(f"error: snapshot '{args.snapshot_id}' not found.", file=sys.stderr)
            sys.exit(1)

    print(json.dumps(snapshot.to_dict(), indent=2))


def cmd_snapshot_diff(args: argparse.Namespace) -> None:
    """Diff two snapshots and render the result."""
    snap_dir = Path(args.snap_dir)

    def _load(sid: str) -> SchemaSnapshot:
        if sid == "latest":
            snap = load_latest_snapshot(snap_dir)
        else:
            snap = load_snapshot(snap_dir, sid)
        if snap is None:
            print(f"error: snapshot '{sid}' not found.", file=sys.stderr)
            sys.exit(1)
        return snap

    old_snap = _load(args.old)
    new_snap = _load(args.new)

    diff = diff_snapshots(old_snap, new_snap)

    fmt = getattr(args, "format", "text")
    if fmt == "json":
        print(render_json(diff))
    elif fmt == "markdown":
        print(render_markdown(diff))
    else:
        print(render_text(diff))

    if diff.has_changes():
        sys.exit(1)  # non-zero exit signals schema drift to CI pipelines


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def build_snapshot_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register snapshot sub-commands onto *subparsers*."""
    snap = subparsers.add_parser("snapshot", help="manage schema snapshots")
    snap_sub = snap.add_subparsers(dest="snapshot_cmd", required=True)

    # -- capture -------------------------------------------------------------
    cap = snap_sub.add_parser("capture", help="capture a new snapshot from the database")
    cap.add_argument("url", help="database URL (postgresql:// or mysql://)")
    cap.add_argument("--snap-dir", default=".schemasnap", help="snapshot storage directory")
    cap.set_defaults(func=cmd_snapshot_capture)

    # -- list ----------------------------------------------------------------
    lst = snap_sub.add_parser("list", help="list stored snapshots")
    lst.add_argument("--snap-dir", default=".schemasnap", help="snapshot storage directory")
    lst.set_defaults(func=cmd_snapshot_list)

    # -- show ----------------------------------------------------------------
    show = snap_sub.add_parser("show", help="show a snapshot as JSON")
    show.add_argument("snapshot_id", nargs="?", default="latest",
                      help="snapshot ID or 'latest' (default: latest)")
    show.add_argument("--snap-dir", default=".schemasnap", help="snapshot storage directory")
    show.set_defaults(func=cmd_snapshot_show)

    # -- diff ----------------------------------------------------------------
    dif = snap_sub.add_parser("diff", help="diff two snapshots")
    dif.add_argument("old", help="older snapshot ID or 'latest'")
    dif.add_argument("new", help="newer snapshot ID or 'latest'")
    dif.add_argument("--snap-dir", default=".schemasnap", help="snapshot storage directory")
    dif.add_argument("--format", choices=["text", "json", "markdown"], default="text",
                     help="output format (default: text)")
    dif.set_defaults(func=cmd_snapshot_diff)
