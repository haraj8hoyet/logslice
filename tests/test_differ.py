"""Tests for logslice.differ."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

import pytest

from logslice.parser import LogEntry
from logslice.differ import (
    DiffEntry,
    diff_entries,
    diff_summary,
    format_diff,
)


def make_entry(
    message: str,
    level: str = "INFO",
    ts: Optional[datetime] = None,
    raw: Optional[str] = None,
) -> LogEntry:
    return LogEntry(
        timestamp=ts,
        level=level,
        message=message,
        raw=raw or f"{level} {message}",
        fields={},
    )


# ---------------------------------------------------------------------------
# diff_entries
# ---------------------------------------------------------------------------

def test_diff_entries_identical_streams_all_unchanged():
    a = [make_entry("hello"), make_entry("world")]
    b = [make_entry("hello"), make_entry("world")]
    result = list(diff_entries(a, b))
    assert all(d.kind == "unchanged" for d in result)
    assert len(result) == 2


def test_diff_entries_added_in_right():
    a = [make_entry("hello")]
    b = [make_entry("hello"), make_entry("new line")]
    result = list(diff_entries(a, b))
    kinds = [d.kind for d in result]
    assert "added" in kinds
    assert kinds.count("unchanged") == 1


def test_diff_entries_removed_from_left():
    a = [make_entry("hello"), make_entry("gone")]
    b = [make_entry("hello")]
    result = list(diff_entries(a, b))
    kinds = [d.kind for d in result]
    assert "removed" in kinds
    assert kinds.count("unchanged") == 1


def test_diff_entries_completely_different():
    a = [make_entry("alpha")]
    b = [make_entry("beta")]
    result = list(diff_entries(a, b))
    kinds = {d.kind for d in result}
    assert kinds == {"added", "removed"}


def test_diff_entries_empty_left():
    a: list = []
    b = [make_entry("only right")]
    result = list(diff_entries(a, b))
    assert len(result) == 1
    assert result[0].kind == "added"


def test_diff_entries_empty_right():
    a = [make_entry("only left")]
    b: list = []
    result = list(diff_entries(a, b))
    assert len(result) == 1
    assert result[0].kind == "removed"


def test_diff_entries_both_empty():
    result = list(diff_entries([], []))
    assert result == []


# ---------------------------------------------------------------------------
# diff_summary
# ---------------------------------------------------------------------------

def test_diff_summary_counts():
    diffs = [
        DiffEntry(kind="unchanged", entry=make_entry("x")),
        DiffEntry(kind="added", entry=make_entry("y")),
        DiffEntry(kind="added", entry=make_entry("z")),
        DiffEntry(kind="removed", entry=make_entry("w")),
    ]
    summary = diff_summary(diffs)
    assert summary["unchanged"] == 1
    assert summary["added"] == 2
    assert summary["removed"] == 1


def test_diff_summary_empty():
    summary = diff_summary([])
    assert summary == {"added": 0, "removed": 0, "unchanged": 0}


# ---------------------------------------------------------------------------
# format_diff
# ---------------------------------------------------------------------------

def test_format_diff_prefix_added():
    diffs = [DiffEntry(kind="added", entry=make_entry("new", raw="INFO new"))]
    lines = list(format_diff(diffs))
    assert lines[0].startswith("+ ")


def test_format_diff_prefix_removed():
    diffs = [DiffEntry(kind="removed", entry=make_entry("old", raw="INFO old"))]
    lines = list(format_diff(diffs))
    assert lines[0].startswith("- ")


def test_format_diff_prefix_unchanged():
    diffs = [DiffEntry(kind="unchanged", entry=make_entry("same", raw="INFO same"))]
    lines = list(format_diff(diffs))
    assert lines[0].startswith("  ")


def test_format_diff_color_added_contains_escape():
    diffs = [DiffEntry(kind="added", entry=make_entry("x", raw="INFO x"))]
    lines = list(format_diff(diffs, use_color=True))
    assert "\033[" in lines[0]


def test_format_diff_no_color_no_escape():
    diffs = [DiffEntry(kind="added", entry=make_entry("x", raw="INFO x"))]
    lines = list(format_diff(diffs, use_color=False))
    assert "\033[" not in lines[0]
