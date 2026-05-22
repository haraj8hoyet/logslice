"""Tests for logslice.cache."""

from __future__ import annotations

import json
import os
import tempfile
from typing import List

import pytest

from logslice.cache import (
    _cache_path,
    get_or_build_index,
    load_index,
    save_index,
)
from logslice.indexer import build_index, LogIndex


SAMPLE_LINES = [
    "2024-03-01T08:00:00 INFO  boot\n",
    "2024-03-01T08:01:00 DEBUG ready\n",
]


def _write_tmp(lines: List[str]) -> str:
    fd, path = tempfile.mkstemp(suffix=".log")
    with os.fdopen(fd, "w") as fh:
        fh.writelines(lines)
    return path


def test_cache_path_has_suffix():
    assert _cache_path("/var/log/app.log").endswith(".logslice-index.json")


def test_save_and_load_roundtrip():
    path = _write_tmp(SAMPLE_LINES)
    index = build_index(path)
    save_index(index)
    loaded = load_index(path)
    assert loaded is not None
    assert loaded.offsets == index.offsets
    assert loaded.timestamps == index.timestamps


def test_load_returns_none_when_no_cache():
    path = _write_tmp(SAMPLE_LINES)
    result = load_index(path)
    assert result is None


def test_load_returns_none_when_file_modified(tmp_path):
    log = tmp_path / "app.log"
    log.write_text("".join(SAMPLE_LINES))
    index = build_index(str(log))
    save_index(index)
    # modify the log file to make cache stale
    log.write_text("".join(SAMPLE_LINES) + "2024-03-01T09:00:00 ERROR oops\n")
    result = load_index(str(log))
    assert result is None


def test_load_returns_none_on_corrupt_cache():
    path = _write_tmp(SAMPLE_LINES)
    cache = _cache_path(path)
    with open(cache, "w") as fh:
        fh.write("not valid json{{")
    result = load_index(path)
    assert result is None


def test_get_or_build_index_creates_cache():
    path = _write_tmp(SAMPLE_LINES)
    cache = _cache_path(path)
    assert not os.path.exists(cache)
    index = get_or_build_index(path)
    assert os.path.exists(cache)
    assert len(index) == len(SAMPLE_LINES)


def test_get_or_build_index_uses_cache_on_second_call():
    path = _write_tmp(SAMPLE_LINES)
    first = get_or_build_index(path)
    second = get_or_build_index(path)
    assert first.offsets == second.offsets
    assert first.timestamps == second.timestamps


def test_save_index_returns_cache_path():
    path = _write_tmp(SAMPLE_LINES)
    index = build_index(path)
    returned = save_index(index)
    assert returned == _cache_path(path)
    assert os.path.exists(returned)
