"""CLI sub-commands for snapshot search."""
from __future__ import annotations

import argparse
import json
from datetime import datetime

from schemasnap.snapshot_search import SearchQuery, search_snapshots


def _parse_dt(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"Invalid datetime '{value}': {exc}") from exc


def cmd_search(args: argparse.Namespace) -> None:
    query = SearchQuery(
        since=args.since,
        until=args.until,
        table_name=args.table,
        min_table_count=args.min_tables,
        max_table_count=args.max_tables,
        label=args.label,
    )
    results = search_snapshots(args.snap_dir, query)

    if not results:
        print("No snapshots matched the query.")
        return

    if args.format == "json":
        print(json.dumps([s.to_dict() for s in results], indent=2))
    else:
        for snap in results:
            table_count = len(snap.tables)
            print(f"  {snap.version_hash[:12]}  {snap.captured_at}  tables={table_count}")
    print(f"\n{len(results)} snapshot(s) found.")


def build_search_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("search", help="Search snapshots by metadata criteria")
    p.add_argument("--snap-dir", required=True, help="Directory containing snapshots")
    p.add_argument("--since", type=_parse_dt, default=None, metavar="ISO_DATETIME")
    p.add_argument("--until", type=_parse_dt, default=None, metavar="ISO_DATETIME")
    p.add_argument("--table", default=None, help="Filter to snapshots containing this table")
    p.add_argument("--min-tables", type=int, default=None)
    p.add_argument("--max-tables", type=int, default=None)
    p.add_argument("--label", default=None, help="Match snapshots with this label")
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.set_defaults(func=cmd_search)
