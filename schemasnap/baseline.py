"""Baseline management: mark a snapshot as the known-good baseline."""

from __future__ import annotations

import json
import os
from pathlib import Path

BASELINE_FILENAME = "baseline.json"


def save_baseline(snapshot_dict: dict, snap_dir: str) -> Path:
    """Persist *snapshot_dict* as the baseline inside *snap_dir*."""
    directory = Path(snap_dir)
    directory.mkdir(parents=True, exist_ok=True)
    baseline_path = directory / BASELINE_FILENAME
    with baseline_path.open("w", encoding="utf-8") as fh:
        json.dump(snapshot_dict, fh, indent=2)
    return baseline_path


def load_baseline(snap_dir: str) -> dict | None:
    """Return the baseline snapshot dict, or *None* if none has been saved."""
    baseline_path = Path(snap_dir) / BASELINE_FILENAME
    if not baseline_path.exists():
        return None
    with baseline_path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def baseline_exists(snap_dir: str) -> bool:
    """Return *True* when a baseline file is present in *snap_dir*."""
    return (Path(snap_dir) / BASELINE_FILENAME).exists()


def clear_baseline(snap_dir: str) -> bool:
    """Delete the baseline file if it exists.  Returns *True* if deleted."""
    baseline_path = Path(snap_dir) / BASELINE_FILENAME
    if baseline_path.exists():
        os.remove(baseline_path)
        return True
    return False


def diff_against_baseline(current_snapshot, snap_dir: str):
    """Diff *current_snapshot* against the saved baseline.

    Returns a :class:`~schemasnap.differ.SchemaDiff` or *None* when no
    baseline is available.
    """
    from schemasnap.differ import diff_snapshots  # local import avoids cycles
    from schemasnap.snapshot import SchemaSnapshot

    raw = load_baseline(snap_dir)
    if raw is None:
        return None
    baseline = SchemaSnapshot.from_dict(raw)
    return diff_snapshots(baseline, current_snapshot)
