"""Tests for schemasnap.cli_search."""
from __future__ import annotations

import argparse
import json
import os
from unittest.mock import patch

import pytest

from schemasnap.cli_search import build_search_parser, cmd_search
from schemasnap.snapshot import SchemaSnapshot


def _write_snap(tables: dict, captured_at: str, snap_dir: str) -> SchemaSnapshot:
    s = SchemaSnapshot(tables=tables, captured_at=captured_at)
    path = os.path.join(snap_dir, f"{s.version_hash}.json")
    with open(path, "w") as fh:
        json.dump(s.to_dict(), fh)
    return s


def _ns(snap_dir, **kwargs) -> argparse.Namespace:
    defaults = dict(
        snap_dir=snap_dir,
        since=None,
        until=None,
        table=None,
        min_tables=None,
        max_tables=None,
        label=None,
        format="text",
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestCmdSearch:
    def test_no_results_prints_message(self, tmp_path, capsys):
        cmd_search(_ns(str(tmp_path)))
        out = capsys.readouterr().out
        assert "No snapshots matched" in out

    def test_text_output_contains_hash_prefix(self, tmp_path, capsys):
        snap = _write_snap({"users": {}}, "2024-01-01T00:00:00", str(tmp_path))
        cmd_search(_ns(str(tmp_path)))
        out = capsys.readouterr().out
        assert snap.version_hash[:12] in out

    def test_text_output_shows_count(self, tmp_path, capsys):
        _write_snap({"a": {}}, "2024-01-01T00:00:00", str(tmp_path))
        _write_snap({"b": {}}, "2024-02-01T00:00:00", str(tmp_path))
        cmd_search(_ns(str(tmp_path)))
        out = capsys.readouterr().out
        assert "2 snapshot(s) found" in out

    def test_json_format_is_valid(self, tmp_path, capsys):
        _write_snap({"orders": {}}, "2024-01-01T00:00:00", str(tmp_path))
        cmd_search(_ns(str(tmp_path), format="json"))
        out = capsys.readouterr().out
        data = json.loads(out)
        assert isinstance(data, list)
        assert len(data) == 1

    def test_table_filter_applied(self, tmp_path, capsys):
        _write_snap({"users": {}}, "2024-01-01T00:00:00", str(tmp_path))
        _write_snap({"products": {}}, "2024-01-02T00:00:00", str(tmp_path))
        cmd_search(_ns(str(tmp_path), table="users"))
        out = capsys.readouterr().out
        assert "1 snapshot(s) found" in out


class TestBuildSearchParser:
    def test_registers_search_subcommand(self):
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        build_search_parser(sub)
        args = parser.parse_args(["search", "--snap-dir", "/tmp"])
        assert args.snap_dir == "/tmp"
        assert args.func is cmd_search

    def test_format_default_is_text(self):
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        build_search_parser(sub)
        args = parser.parse_args(["search", "--snap-dir", "/tmp"])
        assert args.format == "text"
