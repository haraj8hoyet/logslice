"""Tests for logslice.splitter."""

from __future__ import annotations

from datetime import datetime
from typing import List

import pytest

from logslice.parser import LogEntry
from logslice.splitter import split_by_count, split_by_field


def make_entry(level: str = "INFO", message: str = "msg") -> LogEntry:
    return LogEntry(
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
        level=level,
        message=message,
        raw=f"{level} {message}",
    )


# ---------------------------------------------------------------------------
# split_by_count
# ---------------------------------------------------------------------------

def test_split_by_count_exact_multiple():
    entries = [make_entry() for _ in range(6)]
    chunks = list(split_by_count(entries, 2))
    assert len(chunks) == 3
    assert all(len(c) == 2 for c in chunks)


def test_split_by_count_remainder():
    entries = [make_entry() for _ in range(5)]
    chunks = list(split_by_count(entries, 2))
    assert len(chunks) == 3
    assert len(chunks[-1]) == 1


def test_split_by_count_single_chunk():
    entries = [make_entry() for _ in range(3)]
    chunks = list(split_by_count(entries, 10))
    assert len(chunks) == 1
    assert len(chunks[0]) == 3


def test_split_by_count_empty_input():
    chunks = list(split_by_count([], 5))
    assert chunks == []


def test_split_by_count_invalid_chunk_size_raises():
    with pytest.raises(ValueError, match="chunk_size"):
        list(split_by_count([make_entry()], 0))


def test_split_by_count_chunk_size_one():
    entries = [make_entry() for _ in range(4)]
    chunks = list(split_by_count(entries, 1))
    assert len(chunks) == 4
    assert all(len(c) == 1 for c in chunks)


# ---------------------------------------------------------------------------
# split_by_field
# ---------------------------------------------------------------------------

def test_split_by_field_groups_consecutive_runs():
    entries = [
        make_entry(level="INFO"),
        make_entry(level="INFO"),
        make_entry(level="ERROR"),
        make_entry(level="INFO"),
    ]
    groups = list(split_by_field(entries, "level"))
    assert len(groups) == 3
    assert groups[0] == ("INFO", entries[:2])
    assert groups[1] == ("ERROR", [entries[2]])
    assert groups[2] == ("INFO", [entries[3]])


def test_split_by_field_single_run():
    entries = [make_entry(level="WARN") for _ in range(3)]
    groups = list(split_by_field(entries, "level"))
    assert len(groups) == 1
    assert groups[0][0] == "WARN"
    assert len(groups[0][1]) == 3


def test_split_by_field_empty_input():
    groups = list(split_by_field([], "level"))
    assert groups == []


def test_split_by_field_missing_attribute_uses_empty_string():
    entries = [make_entry() for _ in range(2)]
    # 'nonexistent' attribute doesn't exist — should fall back to ""
    groups = list(split_by_field(entries, "nonexistent"))
    assert len(groups) == 1
    assert groups[0][0] == ""
