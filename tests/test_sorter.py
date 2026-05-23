"""Tests for logslice.sorter."""

from datetime import datetime

import pytest

from logslice.parser import LogEntry
from logslice.sorter import sort_entries, iter_sorted


def make_entry(message: str = "msg", level: str = "INFO", ts=None) -> LogEntry:
    return LogEntry(timestamp=ts, level=level, message=message, raw=message)


_T1 = datetime(2024, 1, 1, 10, 0, 0)
_T2 = datetime(2024, 1, 1, 11, 0, 0)
_T3 = datetime(2024, 1, 1, 12, 0, 0)


def test_sort_by_timestamp_asc():
    entries = [make_entry(ts=_T3), make_entry(ts=_T1), make_entry(ts=_T2)]
    result = sort_entries(entries, key="timestamp", order="asc")
    assert [e.timestamp for e in result] == [_T1, _T2, _T3]


def test_sort_by_timestamp_desc():
    entries = [make_entry(ts=_T1), make_entry(ts=_T3), make_entry(ts=_T2)]
    result = sort_entries(entries, key="timestamp", order="desc")
    assert [e.timestamp for e in result] == [_T3, _T2, _T1]


def test_sort_none_timestamp_goes_last():
    e_none = make_entry(ts=None)
    e_ts = make_entry(ts=_T1)
    result = sort_entries([e_none, e_ts], key="timestamp", order="asc")
    assert result[0].timestamp == _T1
    assert result[1].timestamp is None


def test_sort_by_level_asc():
    entries = [
        make_entry(level="ERROR"),
        make_entry(level="DEBUG"),
        make_entry(level="INFO"),
        make_entry(level="CRITICAL"),
        make_entry(level="WARNING"),
    ]
    result = sort_entries(entries, key="level", order="asc")
    levels = [e.level for e in result]
    assert levels == ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


def test_sort_by_level_desc():
    entries = [make_entry(level="DEBUG"), make_entry(level="ERROR")]
    result = sort_entries(entries, key="level", order="desc")
    assert result[0].level == "ERROR"
    assert result[1].level == "DEBUG"


def test_sort_by_message_asc():
    entries = [make_entry("zebra"), make_entry("apple"), make_entry("mango")]
    result = sort_entries(entries, key="message", order="asc")
    assert [e.message for e in result] == ["apple", "mango", "zebra"]


def test_sort_by_message_desc():
    entries = [make_entry("apple"), make_entry("zebra")]
    result = sort_entries(entries, key="message", order="desc")
    assert result[0].message == "zebra"


def test_sort_empty_returns_empty():
    assert sort_entries([], key="timestamp") == []


def test_invalid_key_raises():
    with pytest.raises(ValueError, match="Unknown sort key"):
        sort_entries([], key="unknown")  # type: ignore[arg-type]


def test_invalid_order_raises():
    with pytest.raises(ValueError, match="Unknown sort order"):
        sort_entries([], key="timestamp", order="random")  # type: ignore[arg-type]


def test_iter_sorted_yields_in_order():
    entries = [make_entry(ts=_T2), make_entry(ts=_T1)]
    result = list(iter_sorted(entries, key="timestamp", order="asc"))
    assert result[0].timestamp == _T1
    assert result[1].timestamp == _T2


def test_sort_stable_preserves_relative_order():
    e1 = make_entry("first", level="INFO", ts=_T1)
    e2 = make_entry("second", level="INFO", ts=_T1)
    result = sort_entries([e1, e2], key="timestamp", order="asc", stable=True)
    assert result[0].message == "first"
    assert result[1].message == "second"
