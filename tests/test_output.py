"""Tests for logslice.output module."""

import io
import json
from datetime import datetime, timezone
from logslice.parser import LogEntry
from logslice.output import write_entries, write_entries_streaming


TS = datetime(2024, 5, 1, 8, 30, 0, tzinfo=timezone.utc)


def make_entry(level="INFO", message="test message"):
    return LogEntry(
        timestamp=TS,
        level=level,
        message=message,
        raw=f"{TS.isoformat()} [{level}] {message}",
        extra={},
    )


def test_write_entries_text_format():
    buf = io.StringIO()
    count = write_entries([make_entry()], fmt="text", dest=buf)
    assert count == 1
    output = buf.getvalue()
    assert "[INFO]" in output
    assert "test message" in output


def test_write_entries_json_format():
    buf = io.StringIO()
    write_entries([make_entry(level="ERROR", message="fail")], fmt="json", dest=buf)
    data = json.loads(buf.getvalue().strip())
    assert data["level"] == "ERROR"
    assert data["message"] == "fail"


def test_write_entries_csv_with_header():
    buf = io.StringIO()
    write_entries([make_entry()], fmt="csv", dest=buf, include_csv_header=True)
    lines = buf.getvalue().strip().splitlines()
    assert lines[0] == "timestamp,level,message"
    assert len(lines) == 2


def test_write_entries_csv_without_header():
    buf = io.StringIO()
    write_entries([make_entry()], fmt="csv", dest=buf, include_csv_header=False)
    lines = buf.getvalue().strip().splitlines()
    assert lines[0] != "timestamp,level,message"
    assert len(lines) == 1


def test_write_entries_returns_correct_count():
    buf = io.StringIO()
    entries = [make_entry(), make_entry(level="WARN"), make_entry(level="DEBUG")]
    count = write_entries(entries, fmt="text", dest=buf)
    assert count == 3


def test_write_entries_streaming_text():
    buf = io.StringIO()
    entries = iter([make_entry(), make_entry(level="WARN")])
    count = write_entries_streaming(entries, fmt="text", dest=buf)
    assert count == 2
    assert buf.getvalue().count("\n") == 2


def test_write_entries_streaming_csv_header():
    buf = io.StringIO()
    write_entries_streaming([make_entry()], fmt="csv", dest=buf, include_csv_header=True)
    lines = buf.getvalue().strip().splitlines()
    assert lines[0] == "timestamp,level,message"


def test_write_entries_streaming_invalid_format():
    import pytest
    buf = io.StringIO()
    with pytest.raises(ValueError):
        write_entries_streaming([make_entry()], fmt="yaml", dest=buf)


def test_write_entries_empty_list():
    buf = io.StringIO()
    count = write_entries([], fmt="text", dest=buf)
    assert count == 0
    assert buf.getvalue() == ""
