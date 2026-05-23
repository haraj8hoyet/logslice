"""Integration tests: replay a real temp log file end-to-end."""

import os
import tempfile
import pytest
from logslice.reader import iter_entries
from logslice.replayer import collect_replay


LOG_LINES = [
    "2024-01-01T00:00:00Z INFO  service started",
    "2024-01-01T00:00:02Z DEBUG checking config",
    "2024-01-01T00:00:05Z WARN  slow response detected",
    "2024-01-01T00:00:06Z ERROR connection timeout",
]


def _write_log(lines):
    fd, path = tempfile.mkstemp(suffix=".log")
    with os.fdopen(fd, "w") as f:
        f.write("\n".join(lines) + "\n")
    return path


def test_replay_preserves_all_entries():
    path = _write_log(LOG_LINES)
    try:
        entries = list(iter_entries(path))
        replayed = collect_replay(entries, speed=1000.0, sleep_fn=lambda _: None)
        assert len(replayed) == len(entries)
    finally:
        os.unlink(path)


def test_replay_entry_messages_match_original():
    path = _write_log(LOG_LINES)
    try:
        entries = list(iter_entries(path))
        replayed = collect_replay(entries, speed=1000.0, sleep_fn=lambda _: None)
        for orig, rep in zip(entries, replayed):
            assert orig.message == rep.message
    finally:
        os.unlink(path)


def test_replay_sleep_called_for_timestamped_entries():
    path = _write_log(LOG_LINES)
    try:
        entries = list(iter_entries(path))
        sleeps = []
        collect_replay(entries, speed=1000.0, max_delay=60.0, sleep_fn=sleeps.append)
        # All 4 entries have timestamps; first has no prior so 3 sleeps expected
        assert len(sleeps) == len(entries) - 1
    finally:
        os.unlink(path)


def test_replay_sleep_values_are_positive():
    path = _write_log(LOG_LINES)
    try:
        entries = list(iter_entries(path))
        sleeps = []
        collect_replay(entries, speed=1.0, max_delay=60.0, sleep_fn=sleeps.append)
        assert all(s > 0 for s in sleeps)
    finally:
        os.unlink(path)
