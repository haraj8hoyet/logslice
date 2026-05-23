"""Tests for logslice.correlator."""

from datetime import datetime, timedelta
from typing import Optional

import pytest

from logslice.correlator import CorrelatedGroup, correlate_by_field, correlate_by_time
from logslice.parser import LogEntry


def make_entry(
    message: str = "msg",
    level: str = "INFO",
    timestamp: Optional[datetime] = None,
    extra: Optional[dict] = None,
) -> LogEntry:
    return LogEntry(
        raw=message,
        timestamp=timestamp,
        level=level,
        message=message,
        extra=extra or {},
    )


# ---------------------------------------------------------------------------
# CorrelatedGroup
# ---------------------------------------------------------------------------

def test_correlated_group_len():
    g = CorrelatedGroup(key="x")
    g.entries.append(("s1", make_entry()))
    g.entries.append(("s2", make_entry()))
    assert len(g) == 2


def test_correlated_group_stream_names():
    g = CorrelatedGroup(key="x")
    g.entries.append(("alpha", make_entry()))
    g.entries.append(("beta", make_entry()))
    assert g.stream_names == ["alpha", "beta"]


# ---------------------------------------------------------------------------
# correlate_by_field
# ---------------------------------------------------------------------------

def test_correlate_by_field_groups_matching_values():
    streams = {
        "s1": [make_entry(extra={"request_id": "abc"}), make_entry(extra={"request_id": "xyz"})],
        "s2": [make_entry(extra={"request_id": "abc"})],
    }
    groups = correlate_by_field(streams, "request_id")
    keys = {g.key for g in groups}
    assert "abc" in keys
    assert "xyz" in keys


def test_correlate_by_field_abc_has_two_entries():
    streams = {
        "s1": [make_entry(extra={"request_id": "abc"})],
        "s2": [make_entry(extra={"request_id": "abc"})],
    }
    groups = correlate_by_field(streams, "request_id")
    abc_group = next(g for g in groups if g.key == "abc")
    assert len(abc_group) == 2


def test_correlate_by_field_missing_field_uses_empty_string():
    streams = {
        "s1": [make_entry()],  # no extra fields
    }
    groups = correlate_by_field(streams, "request_id")
    assert len(groups) == 1
    assert groups[0].key == ""


def test_correlate_by_field_empty_streams_returns_empty():
    groups = correlate_by_field({}, "request_id")
    assert groups == []


# ---------------------------------------------------------------------------
# correlate_by_time
# ---------------------------------------------------------------------------

def _dt(offset_seconds: float) -> datetime:
    return datetime(2024, 1, 1, 12, 0, 0) + timedelta(seconds=offset_seconds)


def test_correlate_by_time_same_window_grouped_together():
    streams = {
        "s1": [make_entry(timestamp=_dt(0.0)), make_entry(timestamp=_dt(0.5))],
        "s2": [make_entry(timestamp=_dt(0.3))],
    }
    groups = correlate_by_time(streams, window=timedelta(seconds=1))
    assert len(groups) == 1
    assert len(groups[0]) == 3


def test_correlate_by_time_different_windows_split():
    streams = {
        "s1": [make_entry(timestamp=_dt(0.0)), make_entry(timestamp=_dt(5.0))],
    }
    groups = correlate_by_time(streams, window=timedelta(seconds=1))
    assert len(groups) == 2


def test_correlate_by_time_entries_without_timestamp_skipped():
    streams = {
        "s1": [make_entry(timestamp=None), make_entry(timestamp=_dt(0.0))],
    }
    groups = correlate_by_time(streams, window=timedelta(seconds=1))
    total = sum(len(g) for g in groups)
    assert total == 1


def test_correlate_by_time_empty_streams_returns_empty():
    groups = correlate_by_time({}, window=timedelta(seconds=1))
    assert groups == []
