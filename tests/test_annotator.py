"""Tests for logslice.annotator."""

from __future__ import annotations

from datetime import datetime
from typing import Optional, Dict

import pytest

from logslice.parser import LogEntry
from logslice.annotator import (
    annotate_with_regex,
    annotate_entry,
    annotate_entries,
    make_regex_annotator,
)


def make_entry(
    message: str = "hello world",
    level: str = "INFO",
    extra: Optional[Dict[str, str]] = None,
) -> LogEntry:
    return LogEntry(
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
        level=level,
        message=message,
        raw=message,
        extra=extra or {},
    )


# ---------------------------------------------------------------------------
# annotate_with_regex
# ---------------------------------------------------------------------------

def test_annotate_with_regex_match_returns_fields():
    entry = make_entry(message="user=alice action=login")
    result = annotate_with_regex(
        entry,
        pattern=r"user=(?P<user>\w+)",
        field_map={"user": "username"},
    )
    assert result == {"username": "alice"}


def test_annotate_with_regex_no_match_returns_none():
    entry = make_entry(message="nothing here")
    result = annotate_with_regex(entry, pattern=r"user=(?P<user>\w+)", field_map={"user": "username"})
    assert result is None


def test_annotate_with_regex_multiple_groups():
    entry = make_entry(message="ip=10.0.0.1 port=8080")
    result = annotate_with_regex(
        entry,
        pattern=r"ip=(?P<ip>[\d.]+) port=(?P<port>\d+)",
        field_map={"ip": "remote_ip", "port": "remote_port"},
    )
    assert result == {"remote_ip": "10.0.0.1", "remote_port": "8080"}


def test_annotate_with_regex_missing_group_skipped():
    entry = make_entry(message="user=bob")
    result = annotate_with_regex(
        entry,
        pattern=r"user=(?P<user>\w+)",
        field_map={"user": "username", "nonexistent": "ghost"},
    )
    assert result == {"username": "bob"}


# ---------------------------------------------------------------------------
# annotate_entry
# ---------------------------------------------------------------------------

def test_annotate_entry_merges_fields():
    entry = make_entry(message="user=carol")
    fn = make_regex_annotator(r"user=(?P<user>\w+)", {"user": "username"})
    result = annotate_entry(entry, [fn])
    assert result.extra.get("username") == "carol"


def test_annotate_entry_preserves_existing_extra():
    entry = make_entry(message="user=dave", extra={"env": "prod"})
    fn = make_regex_annotator(r"user=(?P<user>\w+)", {"user": "username"})
    result = annotate_entry(entry, [fn])
    assert result.extra.get("env") == "prod"
    assert result.extra.get("username") == "dave"


def test_annotate_entry_no_annotators_returns_unchanged():
    entry = make_entry(message="unchanged")
    result = annotate_entry(entry, [])
    assert result.message == "unchanged"
    assert result.extra == {}


def test_annotate_entry_chained_annotators():
    entry = make_entry(message="user=eve level=DEBUG")
    fn1 = make_regex_annotator(r"user=(?P<user>\w+)", {"user": "username"})
    fn2 = make_regex_annotator(r"level=(?P<lvl>\w+)", {"lvl": "parsed_level"})
    result = annotate_entry(entry, [fn1, fn2])
    assert result.extra.get("username") == "eve"
    assert result.extra.get("parsed_level") == "DEBUG"


# ---------------------------------------------------------------------------
# annotate_entries
# ---------------------------------------------------------------------------

def test_annotate_entries_applies_to_all():
    entries = [
        make_entry(message="user=frank"),
        make_entry(message="user=grace"),
    ]
    fn = make_regex_annotator(r"user=(?P<user>\w+)", {"user": "username"})
    results = list(annotate_entries(entries, [fn]))
    assert results[0].extra["username"] == "frank"
    assert results[1].extra["username"] == "grace"


def test_annotate_entries_empty_input_yields_nothing():
    results = list(annotate_entries([], [make_regex_annotator(r"x", {})]))
    assert results == []
