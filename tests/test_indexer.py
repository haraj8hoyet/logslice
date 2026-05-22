"""Tests for logslice.indexer."""

from __future__ import annotations

import os
import tempfile
from typing import List

import pytest

from logslice.indexer import (
    LogIndex,
    build_index,
    find_offsets_in_range,
    seek_to_offset,
)


SAMPLE_LINES = [
    "2024-01-01T10:00:00 INFO  started\n",
    "2024-01-01T10:01:00 DEBUG fetching data\n",
    "2024-01-01T10:02:00 ERROR something broke\n",
    "no timestamp here\n",
    "2024-01-01T10:03:00 WARN  retrying\n",
]


def _write_tmp(lines: List[str]) -> str:
    fd, path = tempfile.mkstemp(suffix=".log")
    with os.fdopen(fd, "w") as fh:
        fh.writelines(lines)
    return path


def test_build_index_length():
    path = _write_tmp(SAMPLE_LINES)
    idx = build_index(path)
    assert len(idx) == len(SAMPLE_LINES)


def test_build_index_first_offset_is_zero():
    path = _write_tmp(SAMPLE_LINES)
    idx = build_index(path)
    assert idx.offsets[0] == 0


def test_build_index_offsets_strictly_increasing():
    path = _write_tmp(SAMPLE_LINES)
    idx = build_index(path)
    for a, b in zip(idx.offsets, idx.offsets[1:]):
        assert b > a


def test_build_index_no_timestamp_line_is_none():
    path = _write_tmp(SAMPLE_LINES)
    idx = build_index(path)
    # 4th line has no timestamp
    assert idx.timestamps[3] is None


def test_build_index_timestamps_parsed():
    path = _write_tmp(SAMPLE_LINES)
    idx = build_index(path)
    assert idx.timestamps[0] == "2024-01-01T10:00:00"
    assert idx.timestamps[2] == "2024-01-01T10:02:00"


def test_seek_to_offset_reads_correct_line():
    path = _write_tmp(SAMPLE_LINES)
    idx = build_index(path)
    # seek to the third line
    with seek_to_offset(path, idx.offsets[2]) as fh:
        line = fh.readline()
    assert "ERROR" in line


def test_find_offsets_no_filter_returns_all():
    path = _write_tmp(SAMPLE_LINES)
    idx = build_index(path)
    offsets = find_offsets_in_range(idx)
    assert offsets == idx.offsets


def test_find_offsets_start_filter():
    path = _write_tmp(SAMPLE_LINES)
    idx = build_index(path)
    offsets = find_offsets_in_range(idx, start="2024-01-01T10:02:00")
    # lines 3 (ERROR), 4 (no-ts), 5 (WARN) should be included
    assert len(offsets) == 3


def test_find_offsets_end_filter():
    path = _write_tmp(SAMPLE_LINES)
    idx = build_index(path)
    offsets = find_offsets_in_range(idx, end="2024-01-01T10:01:00")
    # lines 1 (INFO), 2 (DEBUG), 4 (no-ts)
    assert len(offsets) == 3


def test_find_offsets_range_filter():
    path = _write_tmp(SAMPLE_LINES)
    idx = build_index(path)
    offsets = find_offsets_in_range(
        idx,
        start="2024-01-01T10:01:00",
        end="2024-01-01T10:02:00",
    )
    # DEBUG, ERROR, and the no-ts line
    assert len(offsets) == 3


def test_build_index_empty_file():
    path = _write_tmp([])
    idx = build_index(path)
    assert len(idx) == 0
    assert idx.offsets == []
    assert idx.timestamps == []
