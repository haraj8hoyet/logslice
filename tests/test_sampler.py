"""Tests for logslice.sampler."""

from __future__ import annotations

import pytest

from logslice.parser import LogEntry
from logslice.sampler import (
    count_duplicates,
    sample_fraction,
    sample_head,
    sample_nth,
    sample_tail,
)


def make_entry(msg: str, level: str = "INFO") -> LogEntry:
    return LogEntry(raw=f"[{level}] {msg}", message=msg, level=level, timestamp=None, fields={})


ENTRIES = [make_entry(f"msg-{i}") for i in range(10)]


# --- sample_nth ---

def test_sample_nth_every_second():
    result = list(sample_nth(ENTRIES, 2))
    assert len(result) == 5
    assert result[0].message == "msg-1"
    assert result[-1].message == "msg-9"


def test_sample_nth_every_first_is_all():
    result = list(sample_nth(ENTRIES, 1))
    assert result == ENTRIES


def test_sample_nth_invalid_raises():
    with pytest.raises(ValueError):
        list(sample_nth(ENTRIES, 0))


# --- sample_fraction ---

def test_sample_fraction_seed_reproducible():
    a = list(sample_fraction(ENTRIES, 0.5, seed=42))
    b = list(sample_fraction(ENTRIES, 0.5, seed=42))
    assert a == b


def test_sample_fraction_one_returns_all():
    result = list(sample_fraction(ENTRIES, 1.0, seed=0))
    assert result == ENTRIES


def test_sample_fraction_invalid_raises():
    with pytest.raises(ValueError):
        list(sample_fraction(ENTRIES, 0.0))
    with pytest.raises(ValueError):
        list(sample_fraction(ENTRIES, 1.5))


# --- sample_head ---

def test_sample_head_returns_first_n():
    result = sample_head(ENTRIES, 3)
    assert [e.message for e in result] == ["msg-0", "msg-1", "msg-2"]


def test_sample_head_zero_returns_empty():
    assert sample_head(ENTRIES, 0) == []


def test_sample_head_larger_than_stream():
    assert sample_head(ENTRIES, 100) == ENTRIES


# --- sample_tail ---

def test_sample_tail_returns_last_n():
    result = sample_tail(ENTRIES, 3)
    assert [e.message for e in result] == ["msg-7", "msg-8", "msg-9"]


def test_sample_tail_zero_returns_empty():
    assert sample_tail(ENTRIES, 0) == []


def test_sample_tail_larger_than_stream():
    assert sample_tail(ENTRIES, 100) == ENTRIES
