"""Tests for logslice.summarizer."""

from datetime import datetime

import pytest

from logslice.parser import LogEntry
from logslice.summarizer import LogSummary, format_summary, summarize


def make_entry(
    message: str = "msg",
    level: str = "INFO",
    timestamp: datetime | None = None,
    raw: str = "",
) -> LogEntry:
    return LogEntry(raw=raw, timestamp=timestamp, level=level, message=message, fields={})


def test_summarize_total():
    entries = [make_entry() for _ in range(7)]
    s = summarize(entries)
    assert s.total == 7


def test_summarize_empty():
    s = summarize([])
    assert s.total == 0
    assert s.top_levels == []
    assert s.first_timestamp is None


def test_summarize_top_levels_order():
    entries = [
        make_entry(level="ERROR"),
        make_entry(level="ERROR"),
        make_entry(level="WARN"),
        make_entry(level="INFO"),
    ]
    s = summarize(entries, top_n=3)
    assert s.top_levels[0] == ("ERROR", 2)
    assert len(s.top_levels) == 3


def test_summarize_unique_levels():
    entries = [make_entry(level=l) for l in ["INFO", "DEBUG", "ERROR", "INFO"]]
    s = summarize(entries)
    assert s.unique_levels == 3


def test_summarize_top_messages():
    entries = [
        make_entry(message="disk full"),
        make_entry(message="disk full"),
        make_entry(message="ok"),
    ]
    s = summarize(entries)
    assert s.top_messages[0] == ("disk full", 2)


def test_summarize_timestamps():
    t1 = datetime(2024, 1, 1, 10, 0, 0)
    t2 = datetime(2024, 1, 1, 12, 0, 0)
    entries = [make_entry(timestamp=t1), make_entry(timestamp=t2)]
    s = summarize(entries)
    assert "2024-01-01 10:00:00" in s.first_timestamp
    assert "2024-01-01 12:00:00" in s.last_timestamp


def test_summarize_none_level_becomes_unknown():
    entry = LogEntry(raw="", timestamp=None, level=None, message="x", fields={})
    s = summarize([entry])
    assert s.top_levels[0][0] == "UNKNOWN"


def test_format_summary_contains_total():
    s = LogSummary(total=42, unique_levels=2)
    text = format_summary(s)
    assert "42" in text
    assert "2" in text


def test_format_summary_top_levels_listed():
    s = LogSummary(total=3, top_levels=[("ERROR", 2), ("INFO", 1)], unique_levels=2)
    text = format_summary(s)
    assert "ERROR" in text
    assert "INFO" in text


def test_format_summary_long_message_truncated():
    long_msg = "x" * 80
    s = LogSummary(total=1, top_messages=[(long_msg, 1)], unique_levels=1)
    text = format_summary(s)
    assert "..." in text
