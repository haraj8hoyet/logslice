"""Tests for the logslice CLI module."""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
import argparse

from logslice.cli import build_parser, parse_datetime, main


# --- parse_datetime ---

def test_parse_datetime_iso_format():
    result = parse_datetime("2024-03-15T10:30:00")
    assert result == datetime(2024, 3, 15, 10, 30, 0)


def test_parse_datetime_space_format():
    result = parse_datetime("2024-03-15 10:30:00")
    assert result == datetime(2024, 3, 15, 10, 30, 0)


def test_parse_datetime_date_only():
    result = parse_datetime("2024-03-15")
    assert result == datetime(2024, 3, 15, 0, 0, 0)


def test_parse_datetime_invalid_raises():
    with pytest.raises(argparse.ArgumentTypeError, match="Cannot parse datetime"):
        parse_datetime("not-a-date")


# --- build_parser ---

def test_build_parser_defaults():
    parser = build_parser()
    args = parser.parse_args([])
    assert args.file == "-"
    assert args.start is None
    assert args.end is None
    assert args.level is None
    assert args.pattern is None
    assert args.fmt == "text"
    assert args.no_header is False
    assert args.count is False


def test_build_parser_all_options():
    parser = build_parser()
    args = parser.parse_args([
        "mylog.log",
        "--start", "2024-01-01",
        "--end", "2024-01-31",
        "--level", "ERROR",
        "--pattern", "timeout",
        "--format", "json",
        "--no-header",
        "--count",
    ])
    assert args.file == "mylog.log"
    assert args.start == datetime(2024, 1, 1)
    assert args.end == datetime(2024, 1, 31)
    assert args.level == "ERROR"
    assert args.pattern == "timeout"
    assert args.fmt == "json"
    assert args.no_header is True
    assert args.count is True


# --- main ---

def test_main_count_mode(tmp_path):
    log_file = tmp_path / "app.log"
    log_file.write_text(
        "2024-01-10 12:00:00 INFO  service started\n"
        "2024-01-10 12:01:00 ERROR disk full\n"
        "2024-01-10 12:02:00 WARN  high memory\n"
    )
    with patch("sys.stdout") as mock_stdout:
        mock_stdout.write = MagicMock()
        result = main([str(log_file), "--count"])
    assert result == 0


def test_main_returns_zero_on_success(tmp_path):
    log_file = tmp_path / "app.log"
    log_file.write_text("2024-01-10 12:00:00 INFO  all good\n")
    with patch("logslice.cli.write_entries") as mock_write:
        result = main([str(log_file), "--format", "text"])
    assert result == 0
    mock_write.assert_called_once()


def test_main_invalid_format_exits():
    with pytest.raises(SystemExit):
        main(["somefile.log", "--format", "xml"])
