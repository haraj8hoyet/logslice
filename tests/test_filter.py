"""Tests for log entry filtering."""

from datetime import datetime
from typing import List

import pytest

from logslice.filter import apply_filters, filter_by_level, filter_by_pattern, filter_by_time
from logslice.parser import LogEntry


def make_entry(ts: datetime, level: str, message: str) -> LogEntry:
    return LogEntry(raw="", timestamp=ts, level=level, message=message)


ENTRIES: List[LogEntry] = [
    make_entry(datetime(2024, 1, 1, 10, 0), "INFO", "Server started"),
    make_entry(datetime(2024, 1, 1, 10, 30), "DEBUG", "Health check ok"),
    make_entry(datetime(2024, 1, 1, 11, 0), "ERROR", "Connection refused"),
    make_entry(datetime(2024, 1, 1, 12, 0), "WARN", "Slow query detected"),
    LogEntry(raw="unparseable line"),  # invalid entry
]


def test_filter_by_time_start_only():
    result = list(filter_by_time(ENTRIES, start=datetime(2024, 1, 1, 10, 30)))
    assert len(result) == 3


def test_filter_by_time_end_only():
    result = list(filter_by_time(ENTRIES, end=datetime(2024, 1, 1, 10, 30)))
    assert len(result) == 2


def test_filter_by_time_range():
    result = list(filter_by_time(
        ENTRIES,
        start=datetime(2024, 1, 1, 10, 30),
        end=datetime(2024, 1, 1, 11, 0),
    ))
    assert len(result) == 2


def test_filter_by_level():
    result = list(filter_by_level(ENTRIES, ["ERROR", "WARN"]))
    assert len(result) == 2
    assert all(e.level in ("ERROR", "WARN") for e in result)


def test_filter_by_pattern():
    result = list(filter_by_pattern(ENTRIES, r"[Cc]onnection"))
    assert len(result) == 1
    assert "Connection" in result[0].message


def test_apply_filters_combined():
    result = list(apply_filters(
        ENTRIES,
        start=datetime(2024, 1, 1, 10, 0),
        end=datetime(2024, 1, 1, 12, 0),
        levels=["ERROR", "DEBUG"],
    ))
    assert len(result) == 2


def test_apply_filters_no_filters():
    # Without filters, only valid entries pass through (time filter skipped)
    result = list(apply_filters(ENTRIES))
    assert len(result) == 5  # all entries including invalid
