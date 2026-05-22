"""Tests for logslice.stats module."""

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from logslice.parser import LogEntry
from logslice.stats import LogStats, compute_stats, format_stats


def make_entry(raw="log line", timestamp=None, fields=None):
    entry = MagicMock(spec=LogEntry)
    entry.raw = raw
    entry.timestamp = timestamp
    entry.fields = fields or {}
    return entry


DT1 = datetime(2024, 1, 1, 10, 0, 0)
DT2 = datetime(2024, 1, 2, 12, 0, 0)


def test_compute_stats_total():
    entries = [make_entry(), make_entry(), make_entry()]
    stats = compute_stats(entries)
    assert stats.total == 3


def test_compute_stats_by_level():
    entries = [
        make_entry(fields={"level": "info"}),
        make_entry(fields={"level": "error"}),
        make_entry(fields={"level": "info"}),
    ]
    stats = compute_stats(entries)
    assert stats.by_level["INFO"] == 2
    assert stats.by_level["ERROR"] == 1


def test_compute_stats_unknown_level_when_missing():
    entries = [make_entry(fields={})]
    stats = compute_stats(entries)
    assert stats.by_level.get("UNKNOWN", 0) == 1


def test_compute_stats_earliest_latest():
    entries = [
        make_entry(timestamp=DT2),
        make_entry(timestamp=DT1),
    ]
    stats = compute_stats(entries)
    assert stats.earliest == DT1.isoformat()
    assert stats.latest == DT2.isoformat()


def test_compute_stats_unparsed_count():
    entries = [
        make_entry(timestamp=None),
        make_entry(timestamp=DT1),
        make_entry(timestamp=None),
    ]
    stats = compute_stats(entries)
    assert stats.unparsed == 2


def test_compute_stats_top_sources():
    entries = [
        make_entry(fields={"source": "app"}),
        make_entry(fields={"source": "app"}),
        make_entry(fields={"source": "db"}),
    ]
    stats = compute_stats(entries, top_n=2)
    sources = dict(stats.top_sources)
    assert sources["app"] == 2
    assert sources["db"] == 1


def test_compute_stats_empty():
    stats = compute_stats([])
    assert stats.total == 0
    assert stats.earliest is None
    assert stats.latest is None


def test_format_stats_contains_key_fields():
    stats = LogStats(
        total=10,
        by_level={"INFO": 7, "ERROR": 3},
        earliest="2024-01-01T00:00:00",
        latest="2024-01-02T00:00:00",
        top_sources=[("app", 5)],
        unparsed=1,
    )
    output = format_stats(stats)
    assert "10" in output
    assert "INFO" in output
    assert "ERROR" in output
    assert "2024-01-01" in output
    assert "app" in output
    assert "1" in output
