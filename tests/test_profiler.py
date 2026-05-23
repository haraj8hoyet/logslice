"""Tests for logslice.profiler."""

from __future__ import annotations

import time
from datetime import datetime

import pytest

from logslice.parser import LogEntry
from logslice.profiler import ProfileResult, profile_iter, profile_iter_streaming


def make_entry(msg: str = "hello", level: str = "INFO") -> LogEntry:
    return LogEntry(
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
        level=level,
        message=msg,
        raw=f"2024-01-01 12:00:00 {level} {msg}",
        extra={},
    )


def test_profile_iter_no_predicate_yields_all():
    entries = [make_entry(f"msg{i}") for i in range(10)]
    results, prof = profile_iter(iter(entries))
    assert len(results) == 10
    assert prof.entries_processed == 10
    assert prof.entries_yielded == 10
    assert prof.skipped == 0


def test_profile_iter_with_predicate_filters():
    entries = [make_entry("x", "ERROR"), make_entry("y", "INFO"), make_entry("z", "ERROR")]
    results, prof = profile_iter(iter(entries), predicate=lambda e: e.level == "ERROR")
    assert len(results) == 2
    assert prof.entries_processed == 3
    assert prof.entries_yielded == 2
    assert prof.skipped == 1


def test_profile_iter_empty_source():
    results, prof = profile_iter(iter([]))
    assert results == []
    assert prof.entries_processed == 0
    assert prof.entries_yielded == 0
    assert prof.skipped == 0


def test_profile_result_throughput_positive():
    entries = [make_entry() for _ in range(5)]
    _, prof = profile_iter(iter(entries))
    assert prof.throughput_per_sec > 0


def test_profile_result_summary_contains_key_info():
    result = ProfileResult(
        elapsed_seconds=1.5,
        entries_processed=100,
        entries_yielded=80,
        throughput_per_sec=66.7,
        skipped=20,
    )
    summary = result.summary()
    assert "100" in summary
    assert "80" in summary
    assert "20" in summary
    assert "66.7" in summary


def test_profile_iter_streaming_yields_entries_with_time():
    entries = [make_entry(f"m{i}") for i in range(4)]
    streamed = list(profile_iter_streaming(iter(entries)))
    assert len(streamed) == 4
    for entry, elapsed in streamed:
        assert isinstance(entry, LogEntry)
        assert elapsed >= 0.0


def test_profile_iter_streaming_predicate_filters():
    entries = [make_entry("a", "DEBUG"), make_entry("b", "WARN")]
    streamed = list(profile_iter_streaming(iter(entries), predicate=lambda e: e.level == "WARN"))
    assert len(streamed) == 1
    assert streamed[0][0].message == "b"


def test_profile_iter_elapsed_non_negative():
    entries = [make_entry() for _ in range(3)]
    _, prof = profile_iter(iter(entries))
    assert prof.elapsed_seconds >= 0.0
