"""Tests for logslice.exporter."""

import io
import json
from datetime import datetime

import pytest

from logslice.parser import LogEntry
from logslice.exporter import (
    export_entries_csv,
    export_summary_json,
    export_summary_text,
    summary_to_string,
)
from logslice.summarizer import LogSummary


def make_entry(
    message: str = "hello",
    level: str = "INFO",
    timestamp: datetime | None = None,
) -> LogEntry:
    return LogEntry(raw="", timestamp=timestamp, level=level, message=message, fields={})


def test_export_summary_json_structure():
    entries = [make_entry(level="ERROR"), make_entry(level="INFO")]
    buf = io.StringIO()
    export_summary_json(entries, buf)
    data = json.loads(buf.getvalue())
    assert data["total"] == 2
    assert "top_levels" in data
    assert isinstance(data["top_levels"], list)


def test_export_summary_json_empty():
    buf = io.StringIO()
    export_summary_json([], buf)
    data = json.loads(buf.getvalue())
    assert data["total"] == 0
    assert data["first_timestamp"] is None


def test_export_summary_json_timestamps():
    t = datetime(2024, 6, 1, 8, 0, 0)
    entries = [make_entry(timestamp=t)]
    buf = io.StringIO()
    export_summary_json(entries, buf)
    data = json.loads(buf.getvalue())
    assert "2024" in data["first_timestamp"]


def test_export_summary_text_contains_total():
    entries = [make_entry() for _ in range(5)]
    buf = io.StringIO()
    export_summary_text(entries, buf)
    assert "5" in buf.getvalue()


def test_export_summary_text_non_empty():
    buf = io.StringIO()
    export_summary_text([make_entry()], buf)
    assert len(buf.getvalue()) > 0


def test_export_entries_csv_header():
    buf = io.StringIO()
    export_entries_csv([], buf)
    header = buf.getvalue().strip()
    assert "timestamp" in header
    assert "level" in header
    assert "message" in header


def test_export_entries_csv_rows():
    entries = [make_entry(message="boot", level="DEBUG")]
    buf = io.StringIO()
    export_entries_csv(entries, buf)
    lines = buf.getvalue().strip().splitlines()
    assert len(lines) == 2
    assert "boot" in lines[1]
    assert "DEBUG" in lines[1]


def test_export_entries_csv_null_timestamp():
    entries = [make_entry(timestamp=None)]
    buf = io.StringIO()
    export_entries_csv(entries, buf)
    lines = buf.getvalue().strip().splitlines()
    assert lines[1].startswith(",")


def test_summary_to_string_returns_text():
    s = LogSummary(total=10, unique_levels=3)
    text = summary_to_string(s)
    assert "10" in text
