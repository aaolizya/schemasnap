"""Tests for schemasnap.filter."""

import pytest

from schemasnap.filter import FilterConfig, apply_filter


def _tables():
    return {
        "users": [
            {"name": "id", "type": "int"},
            {"name": "email", "type": "varchar"},
            {"name": "password_hash", "type": "varchar"},
        ],
        "orders": [
            {"name": "id", "type": "int"},
            {"name": "status", "type": "varchar"},
        ],
        "tmp_cache": [
            {"name": "key", "type": "varchar"},
        ],
    }


class TestFilterConfig:
    def test_no_rules_includes_all_tables(self):
        cfg = FilterConfig()
        assert cfg.table_is_included("users") is True
        assert cfg.table_is_included("tmp_cache") is True

    def test_include_tables_glob(self):
        cfg = FilterConfig(include_tables=["users", "orders"])
        assert cfg.table_is_included("users") is True
        assert cfg.table_is_included("tmp_cache") is False

    def test_exclude_tables_glob(self):
        cfg = FilterConfig(exclude_tables=["tmp_*"])
        assert cfg.table_is_included("tmp_cache") is False
        assert cfg.table_is_included("users") is True

    def test_include_overrides_exclude(self):
        cfg = FilterConfig(include_tables=["tmp_cache"], exclude_tables=["tmp_*"])
        # include is checked first; tmp_cache IS in include_tables so it passes
        # but then exclude removes it — exclude wins after include
        assert cfg.table_is_included("tmp_cache") is False

    def test_no_column_rules_includes_all(self):
        cfg = FilterConfig()
        assert cfg.column_is_included("users", "password_hash") is True

    def test_exclude_column(self):
        cfg = FilterConfig(exclude_columns={"users": ["password_hash"]})
        assert cfg.column_is_included("users", "password_hash") is False
        assert cfg.column_is_included("users", "email") is True

    def test_include_column(self):
        cfg = FilterConfig(include_columns={"orders": ["id", "status"]})
        assert cfg.column_is_included("orders", "id") is True
        assert cfg.column_is_included("orders", "created_at") is False

    def test_column_rule_other_table_unaffected(self):
        cfg = FilterConfig(exclude_columns={"users": ["password_hash"]})
        assert cfg.column_is_included("orders", "password_hash") is True


class TestApplyFilter:
    def test_none_config_returns_original(self):
        tables = _tables()
        assert apply_filter(tables, None) is tables

    def test_exclude_table(self):
        cfg = FilterConfig(exclude_tables=["tmp_*"])
        result = apply_filter(_tables(), cfg)
        assert "tmp_cache" not in result
        assert "users" in result

    def test_include_tables_only(self):
        cfg = FilterConfig(include_tables=["orders"])
        result = apply_filter(_tables(), cfg)
        assert list(result.keys()) == ["orders"]

    def test_exclude_column_from_table(self):
        cfg = FilterConfig(exclude_columns={"users": ["password_hash"]})
        result = apply_filter(_tables(), cfg)
        col_names = [c["name"] for c in result["users"]]
        assert "password_hash" not in col_names
        assert "email" in col_names

    def test_empty_config_keeps_all(self):
        cfg = FilterConfig()
        result = apply_filter(_tables(), cfg)
        assert set(result.keys()) == {"users", "orders", "tmp_cache"}
