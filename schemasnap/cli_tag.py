"""CLI sub-commands for snapshot tag management."""

from __future__ import annotations

import argparse
import sys

from schemasnap.tag_manager import add_tag, get_tag, list_tags, remove_tag


def cmd_tag_add(args: argparse.Namespace) -> None:
    try:
        entry = add_tag(
            snap_dir=args.snap_dir,
            tag=args.tag,
            snapshot_id=args.snapshot_id,
            note=args.note,
        )
        print(f"Tagged snapshot '{entry.snapshot_id}' as '{entry.tag}'.")
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_tag_remove(args: argparse.Namespace) -> None:
    removed = remove_tag(snap_dir=args.snap_dir, tag=args.tag)
    if removed:
        print(f"Tag '{args.tag}' removed.")
    else:
        print(f"Tag '{args.tag}' not found.", file=sys.stderr)
        sys.exit(1)


def cmd_tag_show(args: argparse.Namespace) -> None:
    entry = get_tag(snap_dir=args.snap_dir, tag=args.tag)
    if entry is None:
        print(f"Tag '{args.tag}' not found.", file=sys.stderr)
        sys.exit(1)
    print(f"Tag       : {entry.tag}")
    print(f"Snapshot  : {entry.snapshot_id}")
    print(f"Note      : {entry.note or '(none)'}")
    print(f"Created at: {entry.created_at}")


def cmd_tag_list(args: argparse.Namespace) -> None:
    tags = list_tags(snap_dir=args.snap_dir)
    if not tags:
        print("No tags defined.")
        return
    for t in tags:
        note_part = f"  # {t.note}" if t.note else ""
        print(f"{t.tag:<24} -> {t.snapshot_id}{note_part}")


def build_tag_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("tag", help="Manage snapshot tags")
    p.add_argument("--snap-dir", default="snapshots", help="Snapshot storage directory")
    sub = p.add_subparsers(dest="tag_cmd", required=True)

    add_p = sub.add_parser("add", help="Add a tag")
    add_p.add_argument("tag", help="Tag name")
    add_p.add_argument("snapshot_id", help="Snapshot ID to tag")
    add_p.add_argument("--note", default=None, help="Optional note")
    add_p.set_defaults(func=cmd_tag_add)

    rm_p = sub.add_parser("remove", help="Remove a tag")
    rm_p.add_argument("tag", help="Tag name")
    rm_p.set_defaults(func=cmd_tag_remove)

    show_p = sub.add_parser("show", help="Show a tag")
    show_p.add_argument("tag", help="Tag name")
    show_p.set_defaults(func=cmd_tag_show)

    list_p = sub.add_parser("list", help="List all tags")
    list_p.set_defaults(func=cmd_tag_list)
