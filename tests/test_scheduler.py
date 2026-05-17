"""Tests for schemasnap.scheduler."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from schemasnap.scheduler import SchedulerConfig, SchemaScheduler


def _make_scheduler(max_runs: int = 1, stop_on_error: bool = False) -> tuple:
    watcher = MagicMock()
    cfg = SchedulerConfig(interval_seconds=0, max_runs=max_runs, stop_on_error=stop_on_error)
    scheduler = SchemaScheduler(watcher, cfg)
    return scheduler, watcher


class TestSchedulerConfig:
    def test_defaults(self):
        cfg = SchedulerConfig()
        assert cfg.interval_seconds == 3600
        assert cfg.max_runs is None
        assert cfg.stop_on_error is False

    def test_custom_values(self):
        cfg = SchedulerConfig(interval_seconds=60, max_runs=5, stop_on_error=True)
        assert cfg.interval_seconds == 60
        assert cfg.max_runs == 5
        assert cfg.stop_on_error is True


class TestSchemaScheduler:
    def test_run_once_calls_watcher(self):
        scheduler, watcher = _make_scheduler(max_runs=1)
        scheduler.start()
        watcher.run_once.assert_called_once()

    def test_run_count_matches_max_runs(self):
        scheduler, watcher = _make_scheduler(max_runs=3)
        scheduler.start()
        assert watcher.run_once.call_count == 3
        assert scheduler._run_count == 3

    def test_stop_on_error_raises(self):
        scheduler, watcher = _make_scheduler(max_runs=5, stop_on_error=True)
        watcher.run_once.side_effect = RuntimeError("db gone")
        with pytest.raises(RuntimeError, match="db gone"):
            scheduler.start()
        assert watcher.run_once.call_count == 1

    def test_no_stop_on_error_continues(self):
        scheduler, watcher = _make_scheduler(max_runs=3, stop_on_error=False)
        watcher.run_once.side_effect = RuntimeError("transient")
        # Should not raise; runs all 3 attempts
        scheduler.start()
        assert watcher.run_once.call_count == 3

    def test_not_running_after_start_completes(self):
        scheduler, _ = _make_scheduler(max_runs=1)
        scheduler.start()
        assert scheduler._running is False

    def test_sleep_called_between_runs(self):
        scheduler, watcher = _make_scheduler(max_runs=2)
        scheduler._config.interval_seconds = 10
        with patch("schemasnap.scheduler.time.sleep") as mock_sleep:
            scheduler.start()
        # sleep should be called once between run 1 and run 2
        mock_sleep.assert_called_once_with(10)

    def test_no_sleep_after_last_run(self):
        scheduler, watcher = _make_scheduler(max_runs=1)
        scheduler._config.interval_seconds = 99
        with patch("schemasnap.scheduler.time.sleep") as mock_sleep:
            scheduler.start()
        mock_sleep.assert_not_called()
