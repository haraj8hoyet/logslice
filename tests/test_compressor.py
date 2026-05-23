"""Tests for logslice.compressor."""

import os
import tempfile
from datetime import datetime

import pytest

from logslice.parser import LogEntry
from logslice.compressor import (
    compress_entries,
    decompress_entries,
    iter_decompressed,
    compress_to_file,
    decompress_from_file,
)


def make_entry(msg: str, level: str = "INFO", ts: datetime = None) -> LogEntry:
    return LogEntry(
        timestamp=ts or datetime(2024, 1, 15, 10, 0, 0),
        level=level,
        message=msg,
        raw=f"2024-01-15T10:00:00 {level} {msg}",
        fields={"host": "srv1"},
    )


def test_compress_decompress_roundtrip():
    entries = [make_entry("alpha"), make_entry("beta", "ERROR")]
    data = compress_entries(entries)
    result = decompress_entries(data)
    assert len(result) == 2
    assert result[0].message == "alpha"
    assert result[1].level == "ERROR"


def test_compress_returns_bytes():
    data = compress_entries([make_entry("x")])
    assert isinstance(data, bytes)
    assert len(data) > 0


def test_compress_empty_list():
    data = compress_entries([])
    result = decompress_entries(data)
    assert result == []


def test_decompress_preserves_timestamp():
    ts = datetime(2023, 6, 1, 12, 30, 45)
    entry = make_entry("ts-check", ts=ts)
    data = compress_entries([entry])
    result = decompress_entries(data)
    assert result[0].timestamp == ts


def test_decompress_preserves_fields():
    entry = make_entry("fields-check")
    data = compress_entries([entry])
    result = decompress_entries(data)
    assert result[0].fields == {"host": "srv1"}


def test_decompress_preserves_raw():
    entry = make_entry("raw-check")
    data = compress_entries([entry])
    result = decompress_entries(data)
    assert result[0].raw == entry.raw


def test_entry_with_none_timestamp():
    entry = LogEntry(timestamp=None, level="WARN", message="no-ts", raw="no-ts", fields={})
    data = compress_entries([entry])
    result = decompress_entries(data)
    assert result[0].timestamp is None
    assert result[0].message == "no-ts"


def test_iter_decompressed_yields_entries():
    entries = [make_entry(f"msg-{i}") for i in range(5)]
    data = compress_entries(entries)
    yielded = list(iter_decompressed(data))
    assert len(yielded) == 5
    assert yielded[2].message == "msg-2"


def test_compress_to_file_and_back(tmp_path):
    entries = [make_entry("file-alpha"), make_entry("file-beta", "DEBUG")]
    path = str(tmp_path / "entries.logz")
    count = compress_to_file(entries, path)
    assert count == 2
    assert os.path.exists(path)
    result = decompress_from_file(path)
    assert len(result) == 2
    assert result[0].message == "file-alpha"
    assert result[1].level == "DEBUG"
