"""Tests for schemasnap.watcher."""

from __future__ import annotations

from unittest.mock import MagicMock, patch, call
from pathlib import Path

import pytest

from schemasnap.watcher import SchemaWatcher, WatcherConfig
from schemasnap.snapshot import SchemaSnapshot
from schemasnap.differ import SchemaDiff


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_tables(names: list[str]) -> dict:
    return {n: [{"name": "id", "type": "int", "nullable": False, "default": None}] for n in names}


def _snap(names: list[str]) -> SchemaSnapshot:
    return SchemaSnapshot(tables=_make_tables(names))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def snap_dir(tmp_path: Path) -> str:
    return str(tmp_path / "snaps")


@pytest.fixture()
def fake_conn() -> MagicMock:
    return MagicMock()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestRunOnce:
    def test_baseline_returns_none(self, snap_dir, fake_conn):
        """First run has no previous snapshot — no diff returned."""
        cfg = WatcherConfig(connection=fake_conn, dialect="postgresql", snapshot_dir=snap_dir)
        watcher = SchemaWatcher(cfg)

        with patch("schemasnap.watcher.extract_schema", return_value=_make_tables(["users"])):
            result = watcher.run_once()

        assert result is None

    def test_no_drift_returns_none(self, snap_dir, fake_conn):
        """Two identical snapshots produce no diff."""
        cfg = WatcherConfig(connection=fake_conn, dialect="postgresql", snapshot_dir=snap_dir)
        watcher = SchemaWatcher(cfg)
        tables = _make_tables(["users"])

        with patch("schemasnap.watcher.extract_schema", return_value=tables):
            watcher.run_once()  # baseline
            # Patch load_latest_snapshot to return a *different* hash snap so
            # comparison proceeds but tables are identical.
            first_snap = _snap(["users"])
            with patch("schemasnap.watcher.load_latest_snapshot", return_value=first_snap):
                result = watcher.run_once()

        assert result is None

    def test_drift_triggers_callback(self, snap_dir, fake_conn):
        """Detected drift should invoke on_drift callback with the SchemaDiff."""
        callback = MagicMock()
        cfg = WatcherConfig(
            connection=fake_conn,
            dialect="postgresql",
            snapshot_dir=snap_dir,
            on_drift=callback,
        )
        watcher = SchemaWatcher(cfg)

        old_snap = _snap(["users"])
        new_tables = _make_tables(["users", "orders"])

        with (
            patch("schemasnap.watcher.extract_schema", return_value=new_tables),
            patch("schemasnap.watcher.save_snapshot"),
            patch("schemasnap.watcher.load_latest_snapshot", return_value=old_snap),
        ):
            result = watcher.run_once()

        assert result is not None
        assert isinstance(result, SchemaDiff)
        callback.assert_called_once()
        diff_arg = callback.call_args[0][0]
        assert "orders" in diff_arg.added_tables

    def test_stop_sets_flag(self, snap_dir, fake_conn):
        cfg = WatcherConfig(connection=fake_conn, dialect="mysql", snapshot_dir=snap_dir)
        watcher = SchemaWatcher(cfg)
        watcher._running = True
        watcher.stop()
        assert watcher._running is False
