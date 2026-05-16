"""Tests for schemasnap.alerting."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from schemasnap.alerting import AlertConfig, notify, _send_email, _send_slack
from schemasnap.differ import SchemaDiff, TableDiff, ColumnChange


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_diff(has_changes: bool = True) -> SchemaDiff:
    if not has_changes:
        return SchemaDiff(added_tables=[], removed_tables=[], modified_tables=[])
    change = ColumnChange(column="id", field="type", old="int", new="bigint")
    td = TableDiff(table="users", added_columns=[], removed_columns=[], column_changes=[change])
    return SchemaDiff(added_tables=[], removed_tables=[], modified_tables=[td])


# ---------------------------------------------------------------------------
# AlertConfig
# ---------------------------------------------------------------------------

class TestAlertConfig:
    def test_has_email_all_fields(self):
        cfg = AlertConfig(
            smtp_host="smtp.example.com",
            email_from="a@b.com",
            email_to=["c@d.com"],
        )
        assert cfg.has_email() is True

    def test_has_email_missing_host(self):
        cfg = AlertConfig(email_from="a@b.com", email_to=["c@d.com"])
        assert cfg.has_email() is False

    def test_has_slack_with_url(self):
        cfg = AlertConfig(slack_webhook_url="https://hooks.slack.com/xxx")
        assert cfg.has_slack() is True

    def test_has_slack_without_url(self):
        assert AlertConfig().has_slack() is False


# ---------------------------------------------------------------------------
# notify
# ---------------------------------------------------------------------------

class TestNotify:
    def test_no_changes_skips_all_channels(self):
        diff = _make_diff(has_changes=False)
        cfg = AlertConfig(
            smtp_host="smtp.example.com",
            email_from="a@b.com",
            email_to=["c@d.com"],
            slack_webhook_url="https://hooks.slack.com/xxx",
        )
        with patch("schemasnap.alerting._send_email") as mock_email, \
             patch("schemasnap.alerting._send_slack") as mock_slack:
            notify(diff, cfg)
            mock_email.assert_not_called()
            mock_slack.assert_not_called()

    def test_sends_email_when_configured(self):
        diff = _make_diff()
        cfg = AlertConfig(
            smtp_host="smtp.example.com",
            email_from="a@b.com",
            email_to=["c@d.com"],
        )
        with patch("schemasnap.alerting._send_email") as mock_email:
            notify(diff, cfg, db_name="mydb")
            mock_email.assert_called_once()
            _, subject, body = mock_email.call_args[0]
            assert "mydb" in subject
            assert "users" in body

    def test_sends_slack_when_configured(self):
        diff = _make_diff()
        cfg = AlertConfig(slack_webhook_url="https://hooks.slack.com/xxx")
        with patch("schemasnap.alerting._send_slack") as mock_slack:
            notify(diff, cfg)
            mock_slack.assert_called_once()
            url, text = mock_slack.call_args[0]
            assert url == "https://hooks.slack.com/xxx"
            assert "users" in text

    def test_sends_both_channels(self):
        diff = _make_diff()
        cfg = AlertConfig(
            smtp_host="smtp.example.com",
            email_from="a@b.com",
            email_to=["c@d.com"],
            slack_webhook_url="https://hooks.slack.com/xxx",
        )
        with patch("schemasnap.alerting._send_email") as me, \
             patch("schemasnap.alerting._send_slack") as ms:
            notify(diff, cfg)
            me.assert_called_once()
            ms.assert_called_once()
