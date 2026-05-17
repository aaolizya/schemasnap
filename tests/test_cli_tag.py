"""Tests for schemasnap.cli_tag CLI commands."""

from __future__ import annotations

import argparse
import pytest

from schemasnap.cli_tag import (
    build_tag_parser,
    cmd_tag_add,
    cmd_tag_list,
    cmd_tag_remove,
    cmd_tag_show,
)
from schemasnap.tag_manager import add_tag


@pytest.fixture()
def snap_dir(tmp_path):
    return str(tmp_path)


def _ns(snap_dir, **kwargs):
    """Build a minimal Namespace for CLI handlers."""
    return argparse.Namespace(snap_dir=snap_dir, **kwargs)


class TestCmdTagAdd:
    def test_adds_tag_and_prints(self, snap_dir, capsys):
        ns = _ns(snap_dir, tag="v1", snapshot_id="snap-001", note=None)
        cmd_tag_add(ns)
        out = capsys.readouterr().out
        assert "v1" in out
        assert "snap-001" in out

    def test_duplicate_exits_nonzero(self, snap_dir):
        add_tag(snap_dir, "v1", "snap-001")
        ns = _ns(snap_dir, tag="v1", snapshot_id="snap-002", note=None)
        with pytest.raises(SystemExit) as exc_info:
            cmd_tag_add(ns)
        assert exc_info.value.code == 1


class TestCmdTagRemove:
    def test_removes_existing_tag(self, snap_dir, capsys):
        add_tag(snap_dir, "v1", "snap-001")
        ns = _ns(snap_dir, tag="v1")
        cmd_tag_remove(ns)
        out = capsys.readouterr().out
        assert "removed" in out.lower()

    def test_missing_tag_exits_nonzero(self, snap_dir):
        ns = _ns(snap_dir, tag="ghost")
        with pytest.raises(SystemExit) as exc_info:
            cmd_tag_remove(ns)
        assert exc_info.value.code == 1


class TestCmdTagShow:
    def test_shows_tag_details(self, snap_dir, capsys):
        add_tag(snap_dir, "v1", "snap-001", note="first")
        ns = _ns(snap_dir, tag="v1")
        cmd_tag_show(ns)
        out = capsys.readouterr().out
        assert "snap-001" in out
        assert "first" in out

    def test_missing_tag_exits_nonzero(self, snap_dir):
        ns = _ns(snap_dir, tag="nope")
        with pytest.raises(SystemExit) as exc_info:
            cmd_tag_show(ns)
        assert exc_info.value.code == 1


class TestCmdTagList:
    def test_empty_prints_no_tags(self, snap_dir, capsys):
        ns = _ns(snap_dir)
        cmd_tag_list(ns)
        out = capsys.readouterr().out
        assert "No tags" in out

    def test_lists_all_tags(self, snap_dir, capsys):
        add_tag(snap_dir, "alpha", "snap-001")
        add_tag(snap_dir, "beta", "snap-002")
        ns = _ns(snap_dir)
        cmd_tag_list(ns)
        out = capsys.readouterr().out
        assert "alpha" in out
        assert "beta" in out


class TestBuildTagParser:
    def test_parser_builds_without_error(self):
        root = argparse.ArgumentParser()
        subs = root.add_subparsers(dest="cmd")
        build_tag_parser(subs)  # should not raise
