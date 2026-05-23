"""Tests for logslice.flattener."""

import pytest
from datetime import datetime
from logslice.parser import LogEntry
from logslice.flattener import _flatten_dict, flatten_entry, flatten_entries


def make_entry(extra=None):
    return LogEntry(
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
        level="INFO",
        message="test message",
        extra=extra or {},
        raw="raw line",
    )


# --- _flatten_dict ---

def test_flatten_dict_flat_input_unchanged():
    d = {"a": 1, "b": "two"}
    assert _flatten_dict(d) == {"a": 1, "b": "two"}


def test_flatten_dict_single_level_nested():
    d = {"a": {"b": 1}}
    assert _flatten_dict(d) == {"a.b": 1}


def test_flatten_dict_two_levels_nested():
    d = {"a": {"b": {"c": 42}}}
    assert _flatten_dict(d) == {"a.b.c": 42}


def test_flatten_dict_mixed_flat_and_nested():
    d = {"x": 1, "y": {"z": 2}}
    result = _flatten_dict(d)
    assert result == {"x": 1, "y.z": 2}


def test_flatten_dict_custom_separator():
    d = {"a": {"b": 9}}
    assert _flatten_dict(d, sep="/") == {"a/b": 9}


def test_flatten_dict_empty_returns_empty():
    assert _flatten_dict({}) == {}


# --- flatten_entry ---

def test_flatten_entry_preserves_top_level_fields():
    entry = make_entry(extra={"k": "v"})
    result = flatten_entry(entry)
    assert result.timestamp == entry.timestamp
    assert result.level == entry.level
    assert result.message == entry.message
    assert result.raw == entry.raw


def test_flatten_entry_flat_extra_unchanged():
    entry = make_entry(extra={"host": "srv1", "port": 8080})
    result = flatten_entry(entry)
    assert result.extra == {"host": "srv1", "port": 8080}


def test_flatten_entry_nested_extra_flattened():
    entry = make_entry(extra={"request": {"method": "GET", "path": "/api"}})
    result = flatten_entry(entry)
    assert result.extra == {"request.method": "GET", "request.path": "/api"}


def test_flatten_entry_deeply_nested():
    entry = make_entry(extra={"a": {"b": {"c": True}}})
    result = flatten_entry(entry)
    assert result.extra == {"a.b.c": True}


def test_flatten_entry_empty_extra():
    entry = make_entry(extra={})
    result = flatten_entry(entry)
    assert result.extra == {}


def test_flatten_entry_returns_new_object():
    entry = make_entry(extra={"x": {"y": 1}})
    result = flatten_entry(entry)
    assert result is not entry


# --- flatten_entries ---

def test_flatten_entries_yields_all():
    entries = [make_entry(extra={"a": 1}), make_entry(extra={"b": 2})]
    result = list(flatten_entries(iter(entries)))
    assert len(result) == 2


def test_flatten_entries_flattens_each():
    entries = [
        make_entry(extra={"req": {"id": 1}}),
        make_entry(extra={"res": {"status": 200}}),
    ]
    result = list(flatten_entries(iter(entries)))
    assert result[0].extra == {"req.id": 1}
    assert result[1].extra == {"res.status": 200}


def test_flatten_entries_empty_input():
    result = list(flatten_entries(iter([])))
    assert result == []


def test_flatten_entries_custom_sep():
    entries = [make_entry(extra={"a": {"b": 99}})]
    result = list(flatten_entries(iter(entries), sep="__"))
    assert result[0].extra == {"a__b": 99}
