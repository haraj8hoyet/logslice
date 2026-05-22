"""Tests for logslice.grouper."""

from __future__ import annotations

from datetime import datetime

import pytest

from logslice.parser import LogEntry
from logslice.grouper import group_by_field, group_by_time_bucket, sorted_groups


def make_entry(
    msg: str,
    level: str = "INFO",
    ts: datetime | None = None,
    fields: dict | None = None,
) -> LogEntry:
    return LogEntry(
        raw=f"[{level}] {msg}",
        message=msg,
        level=level,
        timestamp=ts,
        fields=fields or {},
    )


# --- group_by_field ---

def test_group_by_level_splits_correctly():
    entries = [
        make_entry("a", level="INFO"),
        make_entry("b", level="ERROR"),
        make_entry("c", level="INFO"),
    ]
    groups = group_by_field(entries, "level")
    assert set(groups.keys()) == {"INFO", "ERROR"}
    assert len(groups["INFO"]) == 2
    assert len(groups["ERROR"]) == 1


def test_group_by_missing_field_uses_empty_string():
    entries = [make_entry("x", fields={"host": "web1"}), make_entry("y")]
    groups = group_by_field(entries, "host")
    assert "web1" in groups
    assert "" in groups


# --- group_by_time_bucket ---

def test_group_by_time_bucket_single_bucket():
    ts = datetime(2024, 1, 1, 12, 0, 5)
    entries = [make_entry("a", ts=ts), make_entry("b", ts=ts)]
    groups = group_by_time_bucket(entries, bucket_seconds=60)
    assert len(groups) == 1
    assert sum(len(v) for v in groups.values()) == 2


def test_group_by_time_bucket_two_buckets():
    t1 = datetime(2024, 1, 1, 12, 0, 10)
    t2 = datetime(2024, 1, 1, 12, 1, 10)
    entries = [make_entry("a", ts=t1), make_entry("b", ts=t2)]
    groups = group_by_time_bucket(entries, bucket_seconds=60)
    assert len(groups) == 2


def test_group_by_time_bucket_skips_no_timestamp():
    entries = [make_entry("no-ts"), make_entry("with-ts", ts=datetime(2024, 1, 1))]
    groups = group_by_time_bucket(entries, bucket_seconds=60)
    assert sum(len(v) for v in groups.values()) == 1


def test_group_by_time_bucket_invalid_bucket_raises():
    with pytest.raises(ValueError):
        group_by_time_bucket([], bucket_seconds=0)


# --- sorted_groups ---

def test_sorted_groups_alphabetical():
    groups = {"z": [], "a": [], "m": []}
    result = sorted_groups(groups)
    assert [k for k, _ in result] == ["a", "m", "z"]


def test_sorted_groups_by_count():
    groups = {"x": [make_entry("1")], "y": [make_entry("2"), make_entry("3")]}
    result = sorted_groups(groups, by_count=True)
    assert result[0][0] == "y"
