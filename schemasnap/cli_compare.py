"""CLI sub-commands for flexible snapshot comparison."""

from __future__ import annotations

import argparse
import json
import sys

from schemasnap.snapshot_compare import (
    compare_by_ids,
    compare_tag_to_latest,
    compare_latest_pair,
)
from schemasnap.reporter import render_text, render_json, render_markdown
from schemasnap.filter_config_loader import load_filter_config


def _get_filter(args: argparse.Namespace):
    if getattr(args, "filter_config", None):
        return load_filter_config(args.filter_config)
    return None


def cmd_compare_ids(args: argparse.Namespace) -> None:
    diff = compare_by_ids(args.snap_dir, args.id_a, args.id_b, _get_filter(args))
    _output(diff, args.format)


def cmd_compare_tag(args: argparse.Namespace) -> None:
    diff = compare_tag_to_latest(args.snap_dir, args.tag, _get_filter(args))
    _output(diff, args.format)


def cmd_compare_latest(args: argparse.Namespace) -> None:
    diff = compare_latest_pair(args.snap_dir, _get_filter(args))
    if diff is None:
        print("Not enough snapshots to compare (need at least 2).")
        sys.exit(1)
    _output(diff, args.format)


def _output(diff, fmt: str) -> None:
    if fmt == "json":
        print(render_json(diff))
    elif fmt == "markdown":
        print(render_markdown(diff))
    else:
        print(render_text(diff))


def build_compare_parser(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p_ids = sub.add_parser("compare-ids", help="Diff two snapshots by version ID")
    p_ids.add_argument("snap_dir")
    p_ids.add_argument("id_a")
    p_ids.add_argument("id_b")
    p_ids.add_argument("--format", choices=["text", "json", "markdown"], default="text")
    p_ids.add_argument("--filter-config", default=None)
    p_ids.set_defaults(func=cmd_compare_ids)

    p_tag = sub.add_parser("compare-tag", help="Diff a tagged snapshot against latest")
    p_tag.add_argument("snap_dir")
    p_tag.add_argument("tag")
    p_tag.add_argument("--format", choices=["text", "json", "markdown"], default="text")
    p_tag.add_argument("--filter-config", default=None)
    p_tag.set_defaults(func=cmd_compare_tag)

    p_lat = sub.add_parser("compare-latest", help="Diff the two most recent snapshots")
    p_lat.add_argument("snap_dir")
    p_lat.add_argument("--format", choices=["text", "json", "markdown"], default="text")
    p_lat.add_argument("--filter-config", default=None)
    p_lat.set_defaults(func=cmd_compare_latest)
