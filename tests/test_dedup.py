"""Tests for logslice.dedup."""

from __future__ import annotations

from datetime import datetime

import pytest

from logslice.parser import LogEntry
from logslice.dedup import dedup_entries, count_duplicates, _entry_key


def make_entry(
    message: str = "something happened",
    level: str | None = "INFO",
    source: str | None = "app",
    ts: datetime | None = None,
) -> LogEntry:
    return LogEntry(
        raw=f"{level} {message}",
        timestamp=ts,
        level=level,
        message=message,
        source=source,
    )


def test_entry_key_same_fields_equal():
    e1 = make_entry("disk full", "ERROR")
    e2 = make_entry("disk full", "ERROR")
    assert _entry_key(e1, ("level", "message")) == _entry_key(e2, ("level", "message"))


def test_entry_key_different_message_differs():
    e1 = make_entry("disk full", "ERROR")
    e2 = make_entry("memory low", "ERROR")
    assert _entry_key(e1, ("level", "message")) != _entry_key(e2, ("level", "message"))


def test_dedup_keep_first_removes_duplicates():
    entries = [
        make_entry("msg", "INFO"),
        make_entry("msg", "INFO"),
        make_entry("other", "WARN"),
    ]
    result = list(dedup_entries(entries, keep="first"))
    assert len(result) == 2
    assert result[0].message == "msg"
    assert result[1].message == "other"


def test_dedup_keep_last_returns_last_occurrence():
    ts1 = datetime(2024, 1, 1, 10, 0, 0)
    ts2 = datetime(2024, 1, 1, 11, 0, 0)
    entries = [
        make_entry("msg", "INFO", ts=ts1),
        make_entry("msg", "INFO", ts=ts2),
    ]
    result = list(dedup_entries(entries, keep="last"))
    assert len(result) == 1
    assert result[0].timestamp == ts2


def test_dedup_invalid_keep_raises():
    with pytest.raises(ValueError, match="keep must be"):
        list(dedup_entries([], keep="random"))


def test_dedup_empty_input():
    assert list(dedup_entries([])) == []


def test_dedup_no_duplicates_unchanged():
    entries = [make_entry("a"), make_entry("b"), make_entry("c")]
    result = list(dedup_entries(entries))
    assert len(result) == 3


def test_count_duplicates_basic():
    entries = [
        make_entry("msg", "INFO"),
        make_entry("msg", "INFO"),
        make_entry("other", "WARN"),
    ]
    counts = count_duplicates(entries)
    values = sorted(counts.values(), reverse=True)
    assert values == [2, 1]


def test_count_duplicates_empty():
    assert count_duplicates([]) == {}


def test_dedup_fields_source_only():
    entries = [
        make_entry("msg1", "INFO", source="app"),
        make_entry("msg2", "ERROR", source="app"),
        make_entry("msg3", "DEBUG", source="worker"),
    ]
    result = list(dedup_entries(entries, fields=("source",), keep="first"))
    assert len(result) == 2
