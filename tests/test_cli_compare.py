"""Tests for schemasnap.cli_compare sub-commands."""

from __future__ import annotations

import argparse
import sys
import pytest
from unittest.mock import patch, MagicMock

from schemasnap.cli_compare import (
    cmd_compare_ids,
    cmd_compare_tag,
    cmd_compare_latest,
    build_compare_parser,
)
from schemasnap.differ import SchemaDiff


def _empty_diff() -> SchemaDiff:
    return SchemaDiff(added_tables=[], removed_tables=[], modified_tables={})


def _ns(**kwargs):
    defaults = {"snap_dir": "/snaps", "format": "text", "filter_config": None}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


@patch("schemasnap.cli_compare.compare_by_ids", return_value=_empty_diff())
def test_cmd_compare_ids_text(mock_cmp, capsys):
    cmd_compare_ids(_ns(id_a="aaa", id_b="bbb"))
    mock_cmp.assert_called_once()
    out = capsys.readouterr().out
    assert isinstance(out, str)


@patch("schemasnap.cli_compare.compare_by_ids", return_value=_empty_diff())
def test_cmd_compare_ids_json(mock_cmp, capsys):
    cmd_compare_ids(_ns(id_a="aaa", id_b="bbb", format="json"))
    out = capsys.readouterr().out
    assert "{" in out


@patch("schemasnap.cli_compare.compare_by_ids", return_value=_empty_diff())
def test_cmd_compare_ids_markdown(mock_cmp, capsys):
    cmd_compare_ids(_ns(id_a="aaa", id_b="bbb", format="markdown"))
    out = capsys.readouterr().out
    assert isinstance(out, str)


@patch("schemasnap.cli_compare.compare_tag_to_latest", return_value=_empty_diff())
def test_cmd_compare_tag(mock_cmp, capsys):
    cmd_compare_tag(_ns(tag="v1"))
    mock_cmp.assert_called_once_with("/snaps", "v1", None)


@patch("schemasnap.cli_compare.compare_latest_pair", return_value=_empty_diff())
def test_cmd_compare_latest(mock_cmp, capsys):
    cmd_compare_latest(_ns())
    mock_cmp.assert_called_once()


@patch("schemasnap.cli_compare.compare_latest_pair", return_value=None)
def test_cmd_compare_latest_no_snapshots_exits(mock_cmp):
    with pytest.raises(SystemExit) as exc:
        cmd_compare_latest(_ns())
    assert exc.value.code == 1


def test_build_compare_parser_registers_subcommands():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    build_compare_parser(sub)
    args = parser.parse_args(["compare-latest", "/snaps"])
    assert args.snap_dir == "/snaps"
    assert args.format == "text"
