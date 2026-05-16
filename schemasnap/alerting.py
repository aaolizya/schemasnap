"""Alerting module: send notifications when schema changes are detected."""

from __future__ import annotations

import json
import smtplib
import urllib.request
from dataclasses import dataclass, field
from email.mime.text import MIMEText
from typing import Optional

from schemasnap.differ import SchemaDiff
from schemasnap.reporter import render_text


@dataclass
class AlertConfig:
    """Configuration for one or more alert channels."""

    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    email_from: Optional[str] = None
    email_to: list[str] = field(default_factory=list)

    slack_webhook_url: Optional[str] = None

    def has_email(self) -> bool:
        return bool(self.smtp_host and self.email_from and self.email_to)

    def has_slack(self) -> bool:
        return bool(self.slack_webhook_url)


def _send_email(config: AlertConfig, subject: str, body: str) -> None:
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = config.email_from  # type: ignore[assignment]
    msg["To"] = ", ".join(config.email_to)

    with smtplib.SMTP(config.smtp_host, config.smtp_port) as server:  # type: ignore[arg-type]
        server.ehlo()
        server.starttls()
        if config.smtp_user and config.smtp_password:
            server.login(config.smtp_user, config.smtp_password)
        server.sendmail(config.email_from, config.email_to, msg.as_string())  # type: ignore[arg-type]


def _send_slack(webhook_url: str, text: str) -> None:
    payload = json.dumps({"text": text}).encode()
    req = urllib.request.Request(
        webhook_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10):
        pass


def notify(diff: SchemaDiff, config: AlertConfig, db_name: str = "database") -> None:
    """Send alerts for *diff* through all configured channels."""
    if not diff.has_changes():
        return

    summary = diff.summary()
    body = render_text(diff)
    subject = f"[schemasnap] Schema change detected in {db_name}: {summary}"

    if config.has_email():
        _send_email(config, subject, body)

    if config.has_slack():
        slack_text = f"*{subject}*\n```\n{body}\n```"
        _send_slack(config.slack_webhook_url, slack_text)  # type: ignore[arg-type]
