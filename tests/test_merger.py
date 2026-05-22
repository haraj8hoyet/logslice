"""Tests for logslice.merger module."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List

import pytest

from logslice.merger import merge_sorted
from logslice.parser import LogEntry


def _dt(hour: int, minute: int = 0) -> datetime:
    return datetime(2024, 1, 1, hour, minute, tzinfo=timezone.utc)


def make_entry(message: str, ts: datetime | None = None) -> LogEntry:
    raw = f"{ts.isoformat()} INFO {message}" if ts else message
    return LogEntry(timestamp=ts, level="INFO", message=message, raw=raw, fields={})


# ---------------------------------------------------------------------------
# merge_sorted
# ---------------------------------------------------------------------------

def test_merge_sorted_two_streams_interleaved():
    a = [make_entry("a1", _dt(1)), make_entry("a2", _dt(3))]
    b = [make_entry("b1", _dt(2)), make_entry("b2", _dt(4))]
    result = list(merge_sorted(a, b))
    messages = [e.message for e in result]
    assert messages == ["a1", "b1", "a2", "b2"]


def test_merge_sorted_single_stream_unchanged():
    entries = [make_entry(f"msg{i}", _dt(i)) for i in range(5)]
    result = list(merge_sorted(entries))
    assert result == entries


def test_merge_sorted_empty_streams_yield_nothing():
    result = list(merge_sorted([], []))
    assert result == []


def test_merge_sorted_one_empty_one_full():
    full = [make_entry("x", _dt(1)), make_entry("y", _dt(2))]
    result = list(merge_sorted([], full))
    assert [e.message for e in result] == ["x", "y"]


def test_merge_sorted_no_timestamp_entries_come_last():
    timestamped = [make_entry("ts", _dt(1))]
    no_ts = [make_entry("no_ts", None)]
    result = list(merge_sorted(timestamped, no_ts))
    assert result[0].message == "ts"
    assert result[1].message == "no_ts"


def test_merge_sorted_all_no_timestamp_preserves_stream_order():
    a = [make_entry("a1"), make_entry("a2")]
    b = [make_entry("b1"), make_entry("b2")]
    result = list(merge_sorted(a, b))
    # all lack timestamps; stream 0 entries come before stream 1 via stable idx
    messages = [e.message for e in result]
    assert set(messages) == {"a1", "a2", "b1", "b2"}
    assert len(messages) == 4


def test_merge_sorted_three_streams():
    a = [make_entry("a", _dt(1))]
    b = [make_entry("b", _dt(2))]
    c = [make_entry("c", _dt(3))]
    result = list(merge_sorted(a, b, c))
    assert [e.message for e in result] == ["a", "b", "c"]


def test_merge_sorted_duplicate_timestamps_all_included():
    ts = _dt(5)
    a = [make_entry("dup1", ts)]
    b = [make_entry("dup2", ts)]
    result = list(merge_sorted(a, b))
    assert len(result) == 2
    assert {e.message for e in result} == {"dup1", "dup2"}
