"""CLI sub-commands for baseline management (set, show, clear, diff)."""

from __future__ import annotations

import argparse
import sys

from schemasnap.baseline import (
    baseline_exists,
    clear_baseline,
    diff_against_baseline,
    load_baseline,
    save_baseline,
)
from schemasnap.reporter import render_text
from schemasnap.storage import load_latest_snapshot


def cmd_baseline_set(args: argparse.Namespace) -> None:
    """Mark the latest snapshot as the baseline."""
    snap = load_latest_snapshot(args.snap_dir)
    if snap is None:
        print("ERROR: no snapshots found in", args.snap_dir, file=sys.stderr)
        sys.exit(1)
    path = save_baseline(snap.to_dict(), args.snap_dir)
    print(f"Baseline saved to {path}")


def cmd_baseline_show(args: argparse.Namespace) -> None:
    """Print a summary of the current baseline."""
    raw = load_baseline(args.snap_dir)
    if raw is None:
        print("No baseline set in", args.snap_dir)
        return
    tables = raw.get("tables", {})
    print(f"Baseline snapshot — {len(tables)} table(s):")
    for name in sorted(tables):
        print(f"  {name} ({len(tables[name])} column(s))")


def cmd_baseline_clear(args: argparse.Namespace) -> None:
    """Remove the baseline file."""
    removed = clear_baseline(args.snap_dir)
    if removed:
        print("Baseline cleared.")
    else:
        print("No baseline to clear.")


def cmd_baseline_diff(args: argparse.Namespace) -> None:
    """Diff the latest snapshot against the baseline."""
    if not baseline_exists(args.snap_dir):
        print("ERROR: no baseline set. Run 'baseline set' first.", file=sys.stderr)
        sys.exit(1)
    snap = load_latest_snapshot(args.snap_dir)
    if snap is None:
        print("ERROR: no snapshots found in", args.snap_dir, file=sys.stderr)
        sys.exit(1)
    diff = diff_against_baseline(snap, args.snap_dir)
    if diff is None or not diff.has_changes():
        print("No changes detected since baseline.")
        return
    print(render_text(diff))


def build_baseline_parser(subparsers) -> None:
    """Attach 'baseline' sub-command tree to *subparsers*."""
    p = subparsers.add_parser("baseline", help="Manage the schema baseline")
    p.add_argument("--snap-dir", default=".schemasnap", help="Snapshot storage directory")
    sub = p.add_subparsers(dest="baseline_cmd", required=True)

    sub.add_parser("set", help="Save latest snapshot as baseline")
    sub.add_parser("show", help="Show baseline summary")
    sub.add_parser("clear", help="Remove the baseline")
    sub.add_parser("diff", help="Diff current snapshot against baseline")

    p.set_defaults(func=_dispatch)


def _dispatch(args: argparse.Namespace) -> None:
    handlers = {
        "set": cmd_baseline_set,
        "show": cmd_baseline_show,
        "clear": cmd_baseline_clear,
        "diff": cmd_baseline_diff,
    }
    handlers[args.baseline_cmd](args)
