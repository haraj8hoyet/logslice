"""Tests for logslice.replayer_cli."""

import argparse
import pytest
from unittest.mock import patch, MagicMock
from logslice.replayer_cli import add_replay_subparser, _run_replay
from logslice.parser import LogEntry
from datetime import datetime, timezone


def _namespace(**kwargs):
    defaults = dict(file="log.txt", speed=1.0, max_delay=5.0, fmt="text")
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def make_entry(msg: str) -> LogEntry:
    return LogEntry(
        raw=msg,
        timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
        level="INFO",
        message=msg,
        fields={},
    )


def test_add_replay_subparser_registers_replay():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_replay_subparser(sub)
    ns = parser.parse_args(["replay", "myfile.log"])
    assert ns.file == "myfile.log"


def test_add_replay_subparser_default_speed():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_replay_subparser(sub)
    ns = parser.parse_args(["replay", "f.log"])
    assert ns.speed == 1.0


def test_add_replay_subparser_custom_speed():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_replay_subparser(sub)
    ns = parser.parse_args(["replay", "f.log", "--speed", "4.0"])
    assert ns.speed == 4.0


def test_add_replay_subparser_sets_func():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_replay_subparser(sub)
    ns = parser.parse_args(["replay", "f.log"])
    assert ns.func is _run_replay


def test_run_replay_returns_zero_on_success(capsys):
    entries = [make_entry("hello"), make_entry("world")]
    with patch("logslice.replayer_cli.iter_entries", return_value=iter(entries)), \
         patch("logslice.replayer_cli.replay_entries", return_value=iter(entries)), \
         patch("logslice.replayer_cli.format_entries", return_value=iter(["hello", "world"])):
        code = _run_replay(_namespace())
    assert code == 0


def test_run_replay_prints_formatted_lines(capsys):
    entries = [make_entry("msg1")]
    with patch("logslice.replayer_cli.iter_entries", return_value=iter(entries)), \
         patch("logslice.replayer_cli.replay_entries", return_value=iter(entries)), \
         patch("logslice.replayer_cli.format_entries", return_value=iter(["formatted_msg1"])):
        _run_replay(_namespace())
    out = capsys.readouterr().out
    assert "formatted_msg1" in out


def test_run_replay_returns_one_on_value_error(capsys):
    with patch("logslice.replayer_cli.iter_entries", side_effect=ValueError("bad speed")):
        code = _run_replay(_namespace())
    assert code == 1
    err = capsys.readouterr().err
    assert "replay error" in err


def test_run_replay_returns_one_on_os_error(capsys):
    with patch("logslice.replayer_cli.iter_entries", side_effect=OSError("no file")):
        code = _run_replay(_namespace())
    assert code == 1
