"""Tests for logslice.truncator."""

import pytest
from datetime import datetime
from logslice.parser import LogEntry
from logslice.truncator import (
    truncate_message,
    wrap_message,
    truncate_entry,
)


def make_entry(
    message: str = "hello world",
    level: str = "INFO",
    fields: dict | None = None,
) -> LogEntry:
    return LogEntry(
        raw=message,
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
        level=level,
        message=message,
        fields=fields or {},
    )


# --- truncate_message ---

def test_truncate_message_short_unchanged():
    assert truncate_message("hello", max_len=20) == "hello"


def test_truncate_message_exact_length_unchanged():
    msg = "a" * 10
    assert truncate_message(msg, max_len=10) == msg


def test_truncate_message_long_adds_ellipsis():
    msg = "a" * 50
    result = truncate_message(msg, max_len=10)
    assert result.endswith("...")
    assert len(result) == 10


def test_truncate_message_invalid_max_len_raises():
    with pytest.raises(ValueError):
        truncate_message("hello", max_len=2)


def test_truncate_message_default_max_len():
    long_msg = "x" * 300
    result = truncate_message(long_msg)
    assert len(result) == 200
    assert result.endswith("...")


# --- wrap_message ---

def test_wrap_message_short_single_line():
    assert wrap_message("hello world", width=80) == ["hello world"]


def test_wrap_message_wraps_at_width():
    msg = "one two three four five"
    lines = wrap_message(msg, width=10)
    for line in lines:
        assert len(line) <= 10


def test_wrap_message_preserves_all_words():
    msg = "the quick brown fox jumps over the lazy dog"
    lines = wrap_message(msg, width=15)
    assert " ".join(lines).replace("  ", " ") == msg


def test_wrap_message_single_long_word_own_line():
    word = "superlongwordthatexceedswidth"
    lines = wrap_message(word, width=10)
    assert lines == [word]


def test_wrap_message_invalid_width_raises():
    with pytest.raises(ValueError):
        wrap_message("hello", width=0)


# --- truncate_entry ---

def test_truncate_entry_message_field():
    entry = make_entry(message="a" * 50)
    result = truncate_entry(entry, max_len=10)
    assert len(result.message) == 10
    assert result.message.endswith("...")


def test_truncate_entry_preserves_other_fields():
    entry = make_entry(message="short", fields={"host": "server1"})
    result = truncate_entry(entry, max_len=50)
    assert result.fields["host"] == "server1"
    assert result.timestamp == entry.timestamp


def test_truncate_entry_custom_field():
    entry = make_entry(fields={"trace": "x" * 100})
    result = truncate_entry(entry, max_len=20, field="trace")
    assert len(result.fields["trace"]) == 20
    assert result.fields["trace"].endswith("...")


def test_truncate_entry_missing_field_returns_unchanged():
    entry = make_entry()
    result = truncate_entry(entry, max_len=20, field="nonexistent")
    assert result.message == entry.message


def test_truncate_entry_does_not_mutate_original():
    entry = make_entry(message="a" * 50, fields={"k": "v"})
    _ = truncate_entry(entry, max_len=10)
    assert len(entry.message) == 50
