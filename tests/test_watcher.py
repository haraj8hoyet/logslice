"""Tests for logslice.watcher."""

import tempfile
import time
from pathlib import Path

import pytest

from logslice.watcher import tail_file, collect_tail


def _tmp_log(content: str = "") -> Path:
    f = tempfile.NamedTemporaryFile(
        mode="w", suffix=".log", delete=False, encoding="utf-8"
    )
    f.write(content)
    f.flush()
    f.close()
    return Path(f.name)


def test_tail_file_yields_new_lines():
    path = _tmp_log()
    entries = collect_tail(
        path,
        [
            "2024-01-01T00:00:00 INFO service started",
            "2024-01-01T00:00:01 ERROR something failed",
        ],
    )
    assert len(entries) == 2


def test_tail_file_entry_messages():
    path = _tmp_log()
    entries = collect_tail(path, ["2024-01-01T10:00:00 WARN disk low"])
    assert any("disk low" in e.message for e in entries)


def test_tail_file_parses_level():
    path = _tmp_log()
    entries = collect_tail(path, ["2024-01-01T10:00:00 ERROR kaboom"])
    levels = [e.level for e in entries if e.level]
    assert "ERROR" in levels


def test_tail_file_ignores_existing_content():
    """Lines written before watching starts should NOT appear."""
    path = _tmp_log("2024-01-01T00:00:00 INFO old line\n")
    entries = collect_tail(path, ["2024-01-01T00:00:01 INFO new line"])
    messages = [e.message for e in entries]
    assert all("old" not in m for m in messages)


def test_tail_file_max_iterations_stops():
    path = _tmp_log()
    results = list(
        tail_file(path, poll_interval=0.01, max_iterations=3)
    )
    # No lines appended, so nothing should be yielded
    assert results == []


def test_tail_file_raw_preserved():
    path = _tmp_log()
    raw_line = "2024-06-15T12:34:56 DEBUG raw preserved check"
    entries = collect_tail(path, [raw_line])
    assert any(e.raw == raw_line for e in entries)


def test_collect_tail_multiple_lines_order():
    path = _tmp_log()
    lines = [
        "2024-01-01T00:00:00 INFO first",
        "2024-01-01T00:00:01 INFO second",
        "2024-01-01T00:00:02 INFO third",
    ]
    entries = collect_tail(path, lines, poll_interval=0.03)
    messages = [e.message for e in entries]
    # All three should appear
    assert len([m for m in messages if "first" in m or "second" in m or "third" in m]) == 3
