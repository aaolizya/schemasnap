"""Top-level CLI entry point that composes all sub-command parsers.

This module wires together the individual command groups (snapshot, diff,
baseline, migration, tag) into a single ``schemasnap`` command that users
interact with from the terminal.
"""

from __future__ import annotations

import sys
import argparse

from schemasnap.cli_snapshot import (
    build_snapshot_parser,
    cmd_snapshot_capture,
    cmd_snapshot_list,
    cmd_snapshot_show,
    cmd_snapshot_diff,
)
from schemasnap.cli_baseline import (
    build_baseline_parser,
    cmd_baseline_set,
    cmd_baseline_show,
    cmd_baseline_clear,
    cmd_baseline_diff,
)
from schemasnap.cli_migration import (
    build_migration_parser,
    cmd_migration_record,
    cmd_migration_list,
    cmd_migration_show,
    cmd_migration_clear,
)
from schemasnap.cli_tag import (
    build_tag_parser,
    cmd_tag_add,
    cmd_tag_remove,
    cmd_tag_show,
    cmd_tag_list,
)


# ---------------------------------------------------------------------------
# Root parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    """Return the root argument parser with all sub-command groups attached."""
    parser = argparse.ArgumentParser(
        prog="schemasnap",
        description=(
            "Automatically diff and version database schema changes "
            "across migrations for PostgreSQL and MySQL."
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
    )

    subparsers = parser.add_subparsers(dest="command_group", metavar="<command>")
    subparsers.required = True

    # --- snapshot group ---
    snap_parser = subparsers.add_parser(
        "snapshot",
        help="Capture, list, show, or diff schema snapshots.",
    )
    build_snapshot_parser(snap_parser)

    # --- baseline group ---
    base_parser = subparsers.add_parser(
        "baseline",
        help="Manage the baseline snapshot used for long-running comparisons.",
    )
    build_baseline_parser(base_parser)

    # --- migration group ---
    mig_parser = subparsers.add_parser(
        "migration",
        help="Record and inspect migration events linked to snapshots.",
    )
    build_migration_parser(mig_parser)

    # --- tag group ---
    tag_parser = subparsers.add_parser(
        "tag",
        help="Add, remove, and list human-readable tags on snapshots.",
    )
    build_tag_parser(tag_parser)

    return parser


# ---------------------------------------------------------------------------
# Dispatch helpers
# ---------------------------------------------------------------------------

_SNAPSHOT_DISPATCH: dict[str, object] = {
    "capture": cmd_snapshot_capture,
    "list": cmd_snapshot_list,
    "show": cmd_snapshot_show,
    "diff": cmd_snapshot_diff,
}

_BASELINE_DISPATCH: dict[str, object] = {
    "set": cmd_baseline_set,
    "show": cmd_baseline_show,
    "clear": cmd_baseline_clear,
    "diff": cmd_baseline_diff,
}

_MIGRATION_DISPATCH: dict[str, object] = {
    "record": cmd_migration_record,
    "list": cmd_migration_list,
    "show": cmd_migration_show,
    "clear": cmd_migration_clear,
}

_TAG_DISPATCH: dict[str, object] = {
    "add": cmd_tag_add,
    "remove": cmd_tag_remove,
    "show": cmd_tag_show,
    "list": cmd_tag_list,
}

_GROUP_DISPATCH: dict[str, dict[str, object]] = {
    "snapshot": _SNAPSHOT_DISPATCH,
    "baseline": _BASELINE_DISPATCH,
    "migration": _MIGRATION_DISPATCH,
    "tag": _TAG_DISPATCH,
}


def main(argv: list[str] | None = None) -> int:  # pragma: no cover
    """Parse *argv* and dispatch to the appropriate sub-command handler.

    Returns the process exit code (0 for success, non-zero for failure).
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    group = _GROUP_DISPATCH.get(args.command_group)
    if group is None:
        parser.print_help()
        return 1

    sub_cmd = getattr(args, "subcommand", None)
    handler = group.get(sub_cmd) if sub_cmd else None
    if handler is None:
        # Each sub-parser should have printed its own help; just exit cleanly.
        return 1

    try:
        handler(args)  # type: ignore[call-arg]
        return 0
    except SystemExit as exc:
        return int(exc.code) if exc.code is not None else 1
    except Exception as exc:  # noqa: BLE001
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
