"""Tests for the log line parser."""

from datetime import datetime

import pytest

from logslice.parser import LogEntry, parse_line, parse_timestamp


SAMPLE_LINES = [
    (
        "2024-03-10 08:22:01,123 [INFO] myapp.server - Request received",
        datetime(2024, 3, 10, 8, 22, 1, 123000),
        "INFO",
        "myapp.server",
        "Request received",
    ),
    (
        "2024-03-10T14:55:30.456 [ERROR] db.pool - Connection timeout",
        datetime(2024, 3, 10, 14, 55, 30, 456000),
        "ERROR",
        "db.pool",
        "Connection timeout",
    ),
]


@pytest.mark.parametrize("line,ts,level,logger,msg", SAMPLE_LINES)
def test_parse_line_valid(line, ts, level, logger, msg):
    entry = parse_line(line)
    assert entry.is_valid()
    assert entry.timestamp == ts
    assert entry.level == level
    assert entry.logger == logger
    assert entry.message == msg


def test_parse_line_invalid():
    entry = parse_line("this is not a log line at all")
    assert not entry.is_valid()
    assert entry.raw == "this is not a log line at all"


def test_parse_timestamp_known_formats():
    assert parse_timestamp("2024-01-01 00:00:00") == datetime(2024, 1, 1)
    assert parse_timestamp("2024-01-01T00:00:00,000") == datetime(2024, 1, 1)


def test_parse_timestamp_unknown_returns_none():
    assert parse_timestamp("not-a-date") is None


def test_log_entry_raw_preserved():
    raw = "2024-03-10 08:22:01,123 [DEBUG] app - hello world"
    entry = parse_line(raw)
    assert entry.raw == raw
