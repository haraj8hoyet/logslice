"""Tests for logslice.throttler."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List

import pytest

from logslice.parser import LogEntry
from logslice.throttler import throttle_by_level, throttle_by_time


def make_entry(
    message: str = "msg",
    level: str = "INFO",
    ts: datetime | None = None,
) -> LogEntry:
    return LogEntry(
        timestamp=ts,
        level=level,
        message=message,
        raw=f"{level} {message}",
    )


def _dt(second: int) -> datetime:
    return datetime(2024, 1, 1, 0, 0, second, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# throttle_by_time
# ---------------------------------------------------------------------------

def test_throttle_by_time_limits_within_bucket():
    entries = [make_entry(ts=_dt(i)) for i in range(10)]
    result = list(throttle_by_time(iter(entries), max_per_bucket=3, bucket_seconds=60))
    assert len(result) == 3


def test_throttle_by_time_allows_across_buckets():
    # 0–59 s → bucket 0, 60–119 s → bucket 1
    entries = [make_entry(ts=_dt(i)) for i in range(120)]
    result = list(throttle_by_time(iter(entries), max_per_bucket=2, bucket_seconds=60))
    assert len(result) == 4  # 2 from each of the two buckets


def test_throttle_by_time_none_timestamp_always_passes():
    entries = [make_entry(ts=None) for _ in range(20)]
    result = list(throttle_by_time(iter(entries), max_per_bucket=1, bucket_seconds=60))
    assert len(result) == 20


def test_throttle_by_time_empty_input():
    result = list(throttle_by_time(iter([]), max_per_bucket=5, bucket_seconds=60))
    assert result == []


def test_throttle_by_time_invalid_max_raises():
    with pytest.raises(ValueError, match="max_per_bucket"):
        list(throttle_by_time(iter([]), max_per_bucket=0))


def test_throttle_by_time_invalid_bucket_seconds_raises():
    with pytest.raises(ValueError, match="bucket_seconds"):
        list(throttle_by_time(iter([]), max_per_bucket=1, bucket_seconds=0))


# ---------------------------------------------------------------------------
# throttle_by_level
# ---------------------------------------------------------------------------

def test_throttle_by_level_limits_per_level():
    entries = [make_entry(level="ERROR") for _ in range(5)] + [
        make_entry(level="INFO") for _ in range(5)
    ]
    result = list(throttle_by_level(iter(entries), max_per_level=2))
    error_count = sum(1 for e in result if e.level == "ERROR")
    info_count = sum(1 for e in result if e.level == "INFO")
    assert error_count == 2
    assert info_count == 2


def test_throttle_by_level_case_insensitive():
    entries = [make_entry(level="error"), make_entry(level="ERROR"), make_entry(level="Error")]
    result = list(throttle_by_level(iter(entries), max_per_level=1))
    assert len(result) == 1


def test_throttle_by_level_no_level_counted_together():
    entries = [make_entry(level="") for _ in range(4)]
    result = list(throttle_by_level(iter(entries), max_per_level=2))
    assert len(result) == 2


def test_throttle_by_level_empty_input():
    result = list(throttle_by_level(iter([]), max_per_level=3))
    assert result == []


def test_throttle_by_level_invalid_max_raises():
    with pytest.raises(ValueError, match="max_per_level"):
        list(throttle_by_level(iter([]), max_per_level=0))
