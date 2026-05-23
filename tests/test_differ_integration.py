"""Integration tests: differ + reader working together on real temp files."""

from __future__ import annotations

import tempfile
import os
from pathlib import Path

import pytest

from logslice.differ import diff_entries, diff_summary
from logslice.reader import iter_entries


def _write_log(lines: list, suffix: str = ".log") -> str:
    fd, path = tempfile.mkstemp(suffix=suffix)
    with os.fdopen(fd, "w") as fh:
        fh.write("\n".join(lines) + "\n")
    return path


LINE_A = "2024-01-01T10:00:00 INFO starting service"
LINE_B = "2024-01-01T10:01:00 WARN disk usage high"
LINE_C = "2024-01-01T10:02:00 ERROR connection refused"


def test_identical_files_all_unchanged():
    path = _write_log([LINE_A, LINE_B])
    try:
        left = list(iter_entries(path))
        right = list(iter_entries(path))
        diffs = list(diff_entries(left, right))
        summary = diff_summary(diffs)
        assert summary["unchanged"] == 2
        assert summary["added"] == 0
        assert summary["removed"] == 0
    finally:
        os.unlink(path)


def test_added_line_detected():
    path_a = _write_log([LINE_A])
    path_b = _write_log([LINE_A, LINE_B])
    try:
        left = list(iter_entries(path_a))
        right = list(iter_entries(path_b))
        summary = diff_summary(list(diff_entries(left, right)))
        assert summary["added"] == 1
        assert summary["unchanged"] == 1
    finally:
        os.unlink(path_a)
        os.unlink(path_b)


def test_removed_line_detected():
    path_a = _write_log([LINE_A, LINE_C])
    path_b = _write_log([LINE_A])
    try:
        left = list(iter_entries(path_a))
        right = list(iter_entries(path_b))
        summary = diff_summary(list(diff_entries(left, right)))
        assert summary["removed"] == 1
        assert summary["unchanged"] == 1
    finally:
        os.unlink(path_a)
        os.unlink(path_b)


def test_completely_different_files():
    path_a = _write_log([LINE_A])
    path_b = _write_log([LINE_C])
    try:
        left = list(iter_entries(path_a))
        right = list(iter_entries(path_b))
        diffs = list(diff_entries(left, right))
        kinds = {d.kind for d in diffs}
        assert "added" in kinds
        assert "removed" in kinds
        assert "unchanged" not in kinds
    finally:
        os.unlink(path_a)
        os.unlink(path_b)
