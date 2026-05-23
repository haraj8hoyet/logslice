"""Tests for logslice.normalizer."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

import pytest

from logslice.parser import LogEntry
from logslice.normalizer import (
    normalize_level_field,
    strip_message,
    normalize_entry,
    normalize_entries,
)


def make_entry(
    message: str = "hello",
    level: Optional[str] = "INFO",
    timestamp: Optional[datetime] = None,
    raw: str = "",
) -> LogEntry:
    return LogEntry(timestamp=timestamp, level=level, message=message, raw=raw)


# ---------------------------------------------------------------------------
# normalize_level_field
# ---------------------------------------------------------------------------

def test_normalize_level_field_warn_becomes_warning():
    entry = make_entry(level="warn")
    result = normalize_level_field(entry)
    assert result.level == "WARNING"


def test_normalize_level_field_err_becomes_error():
    entry = make_entry(level="err")
    result = normalize_level_field(entry)
    assert result.level == "ERROR"


def test_normalize_level_field_fatal_becomes_critical():
    entry = make_entry(level="fatal")
    result = normalize_level_field(entry)
    assert result.level == "CRITICAL"


def test_normalize_level_field_unknown_uppercased():
    entry = make_entry(level="verbose")
    result = normalize_level_field(entry)
    assert result.level == "VERBOSE"


def test_normalize_level_field_none_unchanged():
    entry = make_entry(level=None)
    result = normalize_level_field(entry)
    assert result.level is None


def test_normalize_level_field_case_insensitive():
    entry = make_entry(level="WaRn")
    result = normalize_level_field(entry)
    assert result.level == "WARNING"


# ---------------------------------------------------------------------------
# strip_message
# ---------------------------------------------------------------------------

def test_strip_message_removes_surrounding_whitespace():
    entry = make_entry(message="  hello world  ")
    result = strip_message(entry)
    assert result.message == "hello world"


def test_strip_message_no_whitespace_unchanged():
    entry = make_entry(message="clean message")
    result = strip_message(entry)
    assert result.message == "clean message"


def test_strip_message_none_unchanged():
    entry = make_entry(message=None)
    result = strip_message(entry)
    assert result.message is None


# ---------------------------------------------------------------------------
# normalize_entry
# ---------------------------------------------------------------------------

def test_normalize_entry_applies_both_by_default():
    entry = make_entry(level="warn", message="  hi  ")
    result = normalize_entry(entry)
    assert result.level == "WARNING"
    assert result.message == "hi"


def test_normalize_entry_skip_level():
    entry = make_entry(level="warn", message="  hi  ")
    result = normalize_entry(entry, standardize_level=False)
    assert result.level == "warn"
    assert result.message == "hi"


def test_normalize_entry_skip_strip():
    entry = make_entry(level="warn", message="  hi  ")
    result = normalize_entry(entry, strip_whitespace=False)
    assert result.level == "WARNING"
    assert result.message == "  hi  "


# ---------------------------------------------------------------------------
# normalize_entries
# ---------------------------------------------------------------------------

def test_normalize_entries_yields_all():
    entries = [make_entry(level="err", message=" a "), make_entry(level="warn", message=" b ")]
    results = list(normalize_entries(entries))
    assert len(results) == 2
    assert results[0].level == "ERROR"
    assert results[0].message == "a"
    assert results[1].level == "WARNING"
    assert results[1].message == "b"


def test_normalize_entries_empty_input():
    results = list(normalize_entries([]))
    assert results == []
