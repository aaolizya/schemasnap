"""Persist and load schema snapshots to/from disk."""

import json
from pathlib import Path

from schemasnap.snapshot import SchemaSnapshot

DEFAULT_SNAPSHOT_DIR = Path(".schemasnap")


def save_snapshot(snapshot: SchemaSnapshot, base_dir: Path = DEFAULT_SNAPSHOT_DIR) -> Path:
    """Save a snapshot as a JSON file. Returns the path written."""
    base_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{snapshot.db_name}__{snapshot.version_hash}.json"
    path = base_dir / filename
    path.write_text(json.dumps(snapshot.to_dict(), indent=2))
    return path


def load_snapshot(path: Path) -> SchemaSnapshot:
    """Load a snapshot from a JSON file."""
    data = json.loads(path.read_text())
    return SchemaSnapshot.from_dict(data)


def list_snapshots(db_name: str, base_dir: Path = DEFAULT_SNAPSHOT_DIR) -> list[Path]:
    """Return all snapshot files for a given database, sorted by filename (chronological)."""
    if not base_dir.exists():
        return []
    return sorted(base_dir.glob(f"{db_name}__*.json"))


def load_latest_snapshot(db_name: str, base_dir: Path = DEFAULT_SNAPSHOT_DIR) -> SchemaSnapshot | None:
    """Load the most recently saved snapshot for a database."""
    snapshots = list_snapshots(db_name, base_dir)
    if not snapshots:
        return None
    # The last file by name; for strict ordering rely on captured_at inside
    candidates = [load_snapshot(p) for p in snapshots]
    return max(candidates, key=lambda s: s.captured_at)
