"""Load AlertConfig from a YAML or JSON file."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from schemasnap.alerting import AlertConfig


def _load_raw(path: Path) -> dict[str, Any]:
    text = path.read_text()
    suffix = path.suffix.lower()
    if suffix in (".yaml", ".yml"):
        try:
            import yaml  # type: ignore[import]
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "PyYAML is required to load YAML alert configs. "
                "Install it with: pip install pyyaml"
            ) from exc
        return yaml.safe_load(text) or {}
    if suffix == ".json":
        return json.loads(text)
    raise ValueError(f"Unsupported config file format: {suffix!r}")


def load_alert_config(path: str | Path) -> AlertConfig:
    """Parse *path* (JSON or YAML) and return an :class:`AlertConfig`."""
    raw = _load_raw(Path(path))

    email_cfg = raw.get("email", {})
    slack_cfg = raw.get("slack", {})

    return AlertConfig(
        smtp_host=email_cfg.get("smtp_host"),
        smtp_port=int(email_cfg.get("smtp_port", 587)),
        smtp_user=email_cfg.get("smtp_user"),
        smtp_password=email_cfg.get("smtp_password"),
        email_from=email_cfg.get("from"),
        email_to=email_cfg.get("to", []),
        slack_webhook_url=slack_cfg.get("webhook_url"),
    )
