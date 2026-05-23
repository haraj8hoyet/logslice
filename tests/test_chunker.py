"""Tests for logslice.chunker."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import List

import pytest

from logslice.chunker import FileChunk, compute_chunks, iter_chunk_lines


def _write_tmp(lines: List[str]) -> str:
    """Write *lines* to a temp file and return its path."""
    fd, path = tempfile.mkstemp(suffix=".log")
    with os.fdopen(fd, "w") as fh:
        fh.write("\n".join(lines) + "\n")
    return path


# ---------------------------------------------------------------------------
# compute_chunks
# ---------------------------------------------------------------------------

def test_compute_chunks_invalid_num_raises():
    with pytest.raises(ValueError, match="num_chunks"):
        compute_chunks("/dev/null", 0)


def test_compute_chunks_empty_file_returns_single_chunk(tmp_path):
    p = tmp_path / "empty.log"
    p.write_text("")
    chunks = compute_chunks(str(p), 4)
    assert len(chunks) == 1
    assert chunks[0].start == 0
    assert chunks[0].end == -1


def test_compute_chunks_covers_whole_file():
    path = _write_tmp([f"line {i}" for i in range(20)])
    try:
        chunks = compute_chunks(path, 4)
        file_size = os.path.getsize(path)
        # First chunk starts at 0
        assert chunks[0].start == 0
        # Last chunk ends at EOF
        assert chunks[-1].end == -1
        # Chunks are contiguous
        for a, b in zip(chunks, chunks[1:]):
            assert a.end == b.start
    finally:
        os.unlink(path)


def test_compute_chunks_num_chunks_one():
    path = _write_tmp(["alpha", "beta", "gamma"])
    try:
        chunks = compute_chunks(path, 1)
        assert len(chunks) == 1
        assert chunks[0].start == 0
        assert chunks[0].end == -1
    finally:
        os.unlink(path)


def test_compute_chunks_returns_file_chunk_objects():
    path = _write_tmp(["a", "b", "c", "d"])
    try:
        chunks = compute_chunks(path, 2)
        assert all(isinstance(c, FileChunk) for c in chunks)
        assert all(c.path == path for c in chunks)
    finally:
        os.unlink(path)


# ---------------------------------------------------------------------------
# iter_chunk_lines
# ---------------------------------------------------------------------------

def test_iter_chunk_lines_full_file():
    lines = ["first", "second", "third"]
    path = _write_tmp(lines)
    try:
        chunk = FileChunk(path=path, start=0, end=-1)
        result = list(iter_chunk_lines(chunk))
        assert result == lines
    finally:
        os.unlink(path)


def test_iter_chunk_lines_partial_chunk():
    lines = [f"line{i}" for i in range(10)]
    path = _write_tmp(lines)
    try:
        chunks = compute_chunks(path, 3)
        all_lines: List[str] = []
        for chunk in chunks:
            all_lines.extend(iter_chunk_lines(chunk))
        assert all_lines == lines
    finally:
        os.unlink(path)


def test_iter_chunk_lines_empty_file(tmp_path):
    p = tmp_path / "empty.log"
    p.write_text("")
    chunk = FileChunk(path=str(p), start=0, end=-1)
    assert list(iter_chunk_lines(chunk)) == []
