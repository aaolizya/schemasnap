"""Tests for schemasnap.filter_config_loader."""

import json
import pytest

from schemasnap.filter_config_loader import load_filter_config


@pytest.fixture()
def tmp_cfg(tmp_path):
    """Return a helper that writes a JSON config and returns its path."""
    def _write(data: dict):
        p = tmp_path / "filter.json"
        p.write_text(json.dumps(data))
        return p
    return _write


class TestLoadFilterConfigJson:
    def test_loads_include_tables(self, tmp_cfg):
        p = tmp_cfg({"include_tables": ["users", "orders"]})
        cfg = load_filter_config(p)
        assert cfg.include_tables == ["users", "orders"]

    def test_loads_exclude_tables(self, tmp_cfg):
        p = tmp_cfg({"exclude_tables": ["tmp_*"]})
        cfg = load_filter_config(p)
        assert cfg.exclude_tables == ["tmp_*"]

    def test_loads_include_columns(self, tmp_cfg):
        p = tmp_cfg({"include_columns": {"orders": ["id", "status"]}})
        cfg = load_filter_config(p)
        assert cfg.include_columns == {"orders": ["id", "status"]}

    def test_loads_exclude_columns(self, tmp_cfg):
        p = tmp_cfg({"exclude_columns": {"users": ["password_hash"]}})
        cfg = load_filter_config(p)
        assert cfg.exclude_columns == {"users": ["password_hash"]}

    def test_missing_keys_default_to_empty(self, tmp_cfg):
        p = tmp_cfg({})
        cfg = load_filter_config(p)
        assert cfg.include_tables == []
        assert cfg.exclude_tables == []
        assert cfg.include_columns == {}
        assert cfg.exclude_columns == {}

    def test_file_not_found_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_filter_config(tmp_path / "nonexistent.json")

    def test_full_config(self, tmp_cfg):
        data = {
            "include_tables": ["users"],
            "exclude_tables": ["tmp_*"],
            "include_columns": {"users": ["id", "email"]},
            "exclude_columns": {"users": ["password_hash"]},
        }
        p = tmp_cfg(data)
        cfg = load_filter_config(p)
        assert cfg.include_tables == ["users"]
        assert cfg.exclude_tables == ["tmp_*"]
        assert cfg.include_columns["users"] == ["id", "email"]
        assert cfg.exclude_columns["users"] == ["password_hash"]
