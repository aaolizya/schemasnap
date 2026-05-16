"""Tests for schemasnap.alert_config_loader."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from schemasnap.alert_config_loader import load_alert_config


@pytest.fixture()
def tmp_cfg(tmp_path: Path):
    """Return a helper that writes a config file and returns its path."""
    def _write(name: str, data: dict) -> Path:
        p = tmp_path / name
        if name.endswith(".json"):
            p.write_text(json.dumps(data))
        else:
            pytest.importorskip("yaml")
            import yaml  # type: ignore[import]
            p.write_text(yaml.dump(data))
        return p
    return _write


class TestLoadAlertConfigJson:
    def test_loads_email_fields(self, tmp_cfg):
        path = tmp_cfg("cfg.json", {
            "email": {
                "smtp_host": "smtp.example.com",
                "smtp_port": 465,
                "smtp_user": "user",
                "smtp_password": "secret",
                "from": "a@b.com",
                "to": ["x@y.com"],
            }
        })
        cfg = load_alert_config(path)
        assert cfg.smtp_host == "smtp.example.com"
        assert cfg.smtp_port == 465
        assert cfg.smtp_user == "user"
        assert cfg.smtp_password == "secret"
        assert cfg.email_from == "a@b.com"
        assert cfg.email_to == ["x@y.com"]

    def test_loads_slack_webhook(self, tmp_cfg):
        path = tmp_cfg("cfg.json", {"slack": {"webhook_url": "https://hooks.slack.com/T"}})
        cfg = load_alert_config(path)
        assert cfg.slack_webhook_url == "https://hooks.slack.com/T"

    def test_defaults_when_sections_absent(self, tmp_cfg):
        path = tmp_cfg("cfg.json", {})
        cfg = load_alert_config(path)
        assert cfg.smtp_host is None
        assert cfg.smtp_port == 587
        assert cfg.email_to == []
        assert cfg.slack_webhook_url is None

    def test_unsupported_extension_raises(self, tmp_path):
        p = tmp_path / "cfg.toml"
        p.write_text("")
        with pytest.raises(ValueError, match="Unsupported config file format"):
            load_alert_config(p)


class TestLoadAlertConfigYaml:
    def test_loads_email_and_slack(self, tmp_cfg):
        path = tmp_cfg("cfg.yaml", {
            "email": {"smtp_host": "smtp.y.com", "from": "me@y.com", "to": ["you@y.com"]},
            "slack": {"webhook_url": "https://hooks.slack.com/Y"},
        })
        cfg = load_alert_config(path)
        assert cfg.smtp_host == "smtp.y.com"
        assert cfg.has_email() is True
        assert cfg.has_slack() is True
