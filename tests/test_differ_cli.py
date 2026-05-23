"""Tests for logslice.differ_cli."""

from __future__ import annotations

import argparse
import sys
from io import StringIO
from unittest.mock import patch, MagicMock

import pytest

from logslice.differ_cli import add_diff_subparser, _run_diff
from logslice.parser import LogEntry


def _make_entry(msg: str) -> LogEntry:
    return LogEntry(timestamp=None, level="INFO", message=msg, raw=f"INFO {msg}", fields={})


def _namespace(**kwargs) -> argparse.Namespace:
    defaults = {"left": "a.log", "right": "b.log", "color": False, "summary": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_add_diff_subparser_registers_diff():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_diff_subparser(sub)
    args = parser.parse_args(["diff", "a.log", "b.log"])
    assert args.left == "a.log"
    assert args.right == "b.log"


def test_run_diff_identical_files_returns_zero():
    entries = [_make_entry("hello")]
    with patch("logslice.differ_cli.iter_entries", return_value=iter(entries)):
        ns = _namespace()
        code = _run_diff(ns)
    assert code == 0


def test_run_diff_different_files_returns_one():
    left = [_make_entry("hello")]
    right = [_make_entry("world")]
    call_count = 0

    def fake_iter(path):
        nonlocal call_count
        result = left if call_count == 0 else right
        call_count += 1
        return iter(result)

    with patch("logslice.differ_cli.iter_entries", side_effect=fake_iter):
        ns = _namespace()
        code = _run_diff(ns)
    assert code == 1


def test_run_diff_summary_flag_prints_counts(capsys):
    left = [_make_entry("a")]
    right = [_make_entry("a"), _make_entry("b")]
    call_count = 0

    def fake_iter(path):
        nonlocal call_count
        result = left if call_count == 0 else right
        call_count += 1
        return iter(result)

    with patch("logslice.differ_cli.iter_entries", side_effect=fake_iter):
        ns = _namespace(summary=True)
        _run_diff(ns)

    captured = capsys.readouterr()
    assert "added" in captured.out
    assert "unchanged" in captured.out


def test_run_diff_oserror_returns_one(capsys):
    with patch("logslice.differ_cli.iter_entries", side_effect=OSError("not found")):
        ns = _namespace()
        code = _run_diff(ns)
    assert code == 1
    captured = capsys.readouterr()
    assert "error" in captured.err
