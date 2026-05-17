"""Tests for schemasnap.tag_manager."""

from __future__ import annotations

import json
import os
import pytest

from schemasnap.tag_manager import (
    TagEntry,
    add_tag,
    get_tag,
    list_tags,
    remove_tag,
    _index_path,
)


@pytest.fixture()
def snap_dir(tmp_path):
    return str(tmp_path)


# ---------------------------------------------------------------------------
# TagEntry unit tests
# ---------------------------------------------------------------------------

class TestTagEntry:
    def test_to_dict_contains_required_keys(self):
        e = TagEntry(tag="v1", snapshot_id="abc123")
        d = e.to_dict()
        assert {"tag", "snapshot_id", "note", "created_at"} <= d.keys()

    def test_from_dict_round_trip(self):
        e = TagEntry(tag="release", snapshot_id="snap-001", note="initial release")
        assert TagEntry.from_dict(e.to_dict()).tag == "release"
        assert TagEntry.from_dict(e.to_dict()).note == "initial release"

    def test_created_at_is_iso_format(self):
        from datetime import datetime
        e = TagEntry(tag="t", snapshot_id="s")
        # Should not raise
        datetime.fromisoformat(e.created_at)


# ---------------------------------------------------------------------------
# add_tag
# ---------------------------------------------------------------------------

class TestAddTag:
    def test_creates_index_file(self, snap_dir):
        add_tag(snap_dir, "v1", "snap-001")
        assert os.path.exists(_index_path(snap_dir))

    def test_index_is_valid_json(self, snap_dir):
        add_tag(snap_dir, "v1", "snap-001")
        with open(_index_path(snap_dir)) as fh:
            data = json.load(fh)
        assert isinstance(data, list)
        assert data[0]["tag"] == "v1"

    def test_duplicate_tag_raises(self, snap_dir):
        add_tag(snap_dir, "v1", "snap-001")
        with pytest.raises(ValueError, match="already exists"):
            add_tag(snap_dir, "v1", "snap-002")

    def test_note_is_persisted(self, snap_dir):
        add_tag(snap_dir, "v1", "snap-001", note="hello")
        entry = get_tag(snap_dir, "v1")
        assert entry is not None
        assert entry.note == "hello"


# ---------------------------------------------------------------------------
# remove_tag
# ---------------------------------------------------------------------------

class TestRemoveTag:
    def test_returns_true_when_found(self, snap_dir):
        add_tag(snap_dir, "v1", "snap-001")
        assert remove_tag(snap_dir, "v1") is True

    def test_returns_false_when_missing(self, snap_dir):
        assert remove_tag(snap_dir, "nonexistent") is False

    def test_tag_gone_after_removal(self, snap_dir):
        add_tag(snap_dir, "v1", "snap-001")
        remove_tag(snap_dir, "v1")
        assert get_tag(snap_dir, "v1") is None


# ---------------------------------------------------------------------------
# list_tags
# ---------------------------------------------------------------------------

class TestListTags:
    def test_empty_when_no_tags(self, snap_dir):
        assert list_tags(snap_dir) == []

    def test_returns_all_added_tags(self, snap_dir):
        add_tag(snap_dir, "alpha", "snap-001")
        add_tag(snap_dir, "beta", "snap-002")
        tags = list_tags(snap_dir)
        assert len(tags) == 2
        names = {t.tag for t in tags}
        assert names == {"alpha", "beta"}
