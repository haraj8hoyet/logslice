"""Tests for logslice.formatter module."""

import json
import pytest
from datetime import datetime, timezone
from logslice.parser import LogEntry
from logslice.formatter import (
    format_text,
    format_json,
    format_csv,
    format_entries,
    csv_header,
)


TS = datetime(2024, 3, 15, 12, 0, 0, tzinfo=timezone.utc)


def make_entry(ts=TS, level="INFO", message="hello world", raw=None, extra=None):
    return LogEntry(
        timestamp=ts,
        level=level,
        message=message,
        raw=raw or f"{ts.isoformat()} [{level}] {message}",
        extra=extra or {},
    )


def test_format_text_full_entry():
    entry = make_entry()
    result = format_text(entry)
    assert "2024-03-15" in result
    assert "[INFO]" in result
    assert "hello world" in result


def test_format_text_no_timestamp_falls_back():
    entry = make_entry(ts=None, raw="raw line here")
    result = format_text(entry)
    assert "raw line here" in result


def test_format_json_contains_all_fields():
    entry = make_entry(extra={"host": "srv1"})
    result = format_json(entry)
    data = json.loads(result)
    assert data["level"] == "INFO"
    assert data["message"] == "hello world"
    assert data["timestamp"] is not None
    assert data["extra"] == {"host": "srv1"}


def test_format_json_null_timestamp():
    entry = make_entry(ts=None)
    result = format_json(entry)
    data = json.loads(result)
    assert data["timestamp"] is None


def test_format_csv_basic():
    entry = make_entry()
    result = format_csv(entry)
    parts = result.split(",")
    assert len(parts) == 3
    assert "INFO" in parts[1]


def test_format_csv_escapes_commas_in_message():
    entry = make_entry(message="error, retry")
    result = format_csv(entry)
    assert '"error, retry"' in result


def test_csv_header_format():
    header = csv_header()
    assert header == "timestamp,level,message"


def test_format_entries_text():
    entries = [make_entry(), make_entry(level="ERROR", message="boom")]
    results = format_entries(entries, fmt="text")
    assert len(results) == 2
    assert "[ERROR]" in results[1]


def test_format_entries_json():
    entries = [make_entry()]
    results = format_entries(entries, fmt="json")
    assert json.loads(results[0])["level"] == "INFO"


def test_format_entries_csv():
    entries = [make_entry()]
    results = format_entries(entries, fmt="csv")
    assert "INFO" in results[0]


def test_format_entries_invalid_format():
    with pytest.raises(ValueError, match="Unsupported format"):
        format_entries([], fmt="xml")
