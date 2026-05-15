"""Command-line interface for schemasnap diff and report commands."""

import argparse
import sys
from schemasnap.storage import load_snapshot, load_latest_snapshot, list_snapshots
from schemasnap.differ import diff_snapshots
from schemasnap.reporter import render_text, render_json, render_markdown


def cmd_diff(args: argparse.Namespace) -> int:
    snap_dir = args.snap_dir
    snapshots = list_snapshots(snap_dir)
    if len(snapshots) < 2 and not (args.from_version and args.to_version):
        print("Need at least two snapshots to diff.", file=sys.stderr)
        return 1

    if args.from_version and args.to_version:
        old = load_snapshot(snap_dir, args.from_version)
        new = load_snapshot(snap_dir, args.to_version)
    else:
        old = load_snapshot(snap_dir, snapshots[-2])
        new = load_snapshot(snap_dir, snapshots[-1])

    if old is None or new is None:
        print("Could not load one or both snapshots.", file=sys.stderr)
        return 1

    diff = diff_snapshots(old, new)

    fmt = args.format
    if fmt == "json":
        print(render_json(diff))
    elif fmt == "markdown":
        print(render_markdown(diff))
    else:
        print(render_text(diff))

    return 0 if diff.has_changes else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="schemasnap",
        description="Diff and version database schema snapshots.",
    )
    subparsers = parser.add_subparsers(dest="command")

    diff_parser = subparsers.add_parser("diff", help="Diff two schema snapshots.")
    diff_parser.add_argument("--snap-dir", default=".schemasnap", help="Snapshot storage directory.")
    diff_parser.add_argument("--from", dest="from_version", default=None, help="Hash of the older snapshot.")
    diff_parser.add_argument("--to", dest="to_version", default=None, help="Hash of the newer snapshot.")
    diff_parser.add_argument(
        "--format", choices=["text", "json", "markdown"], default="text",
        help="Output format (default: text).",
    )
    diff_parser.set_defaults(func=cmd_diff)

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
