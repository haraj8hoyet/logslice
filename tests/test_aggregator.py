"""Tests for logslice.aggregator."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

import pytest

from logslice.aggregator import (
    AggregateGroup,
    aggregate_by_field,
    format_aggregate,
    top_groups,
)
from logslice.parser import LogEntry


def make_entry(
    message: str = "msg",
    level: str = "INFO",
    ts: Optional[datetime] = None,
    **extra,
) -> LogEntry:
    return LogEntry(
        raw=message,
        timestamp=ts or datetime(2024, 1, 1, tzinfo=timezone.utc),
        level=level,
        message=message,
        extra=extra,
    )


# ---------------------------------------------------------------------------
# aggregate_by_field
# ---------------------------------------------------------------------------

def test_aggregate_by_level_counts():
    entries = [
        make_entry(level="INFO"),
        make_entry(level="ERROR"),
        make_entry(level="INFO"),
    ]
    groups = aggregate_by_field(entries, "level")
    assert groups["INFO"].count == 2
    assert groups["ERROR"].count == 1


def test_aggregate_by_extra_field():
    entries = [
        make_entry(service="auth"),
        make_entry(service="auth"),
        make_entry(service="api"),
    ]
    groups = aggregate_by_field(entries, "service")
    assert groups["auth"].count == 2
    assert groups["api"].count == 1


def test_aggregate_missing_field_uses_empty_string():
    entries = [make_entry(), make_entry()]
    groups = aggregate_by_field(entries, "nonexistent")
    assert "" in groups
    assert groups[""].count == 2


def test_aggregate_samples_capped_at_max():
    entries = [make_entry(message=f"msg{i}", level="INFO") for i in range(10)]
    groups = aggregate_by_field(entries, "level", max_samples=3)
    assert len(groups["INFO"].samples) == 3


def test_aggregate_samples_include_messages():
    entries = [make_entry(message="hello", level="WARN")]
    groups = aggregate_by_field(entries, "level")
    assert "hello" in groups["WARN"].samples


def test_aggregate_empty_input_returns_empty_dict():
    groups = aggregate_by_field([], "level")
    assert groups == {}


def test_aggregate_invalid_max_samples_raises():
    with pytest.raises(ValueError):
        aggregate_by_field([], "level", max_samples=-1)


# ---------------------------------------------------------------------------
# top_groups
# ---------------------------------------------------------------------------

def test_top_groups_sorted_by_count_desc():
    entries = [
        make_entry(level="DEBUG"),
        make_entry(level="INFO"),
        make_entry(level="INFO"),
        make_entry(level="INFO"),
        make_entry(level="ERROR"),
        make_entry(level="ERROR"),
    ]
    groups = aggregate_by_field(entries, "level")
    ranked = top_groups(groups)
    assert ranked[0].key == "INFO"
    assert ranked[1].key == "ERROR"
    assert ranked[2].key == "DEBUG"


def test_top_groups_limited_by_n():
    entries = [make_entry(level=lvl) for lvl in ["A", "A", "B", "C"]]
    groups = aggregate_by_field(entries, "level")
    ranked = top_groups(groups, n=2)
    assert len(ranked) == 2


def test_top_groups_n_none_returns_all():
    entries = [make_entry(level=lvl) for lvl in ["X", "Y", "Z"]]
    groups = aggregate_by_field(entries, "level")
    assert len(top_groups(groups, n=None)) == 3


# ---------------------------------------------------------------------------
# format_aggregate
# ---------------------------------------------------------------------------

def test_format_aggregate_contains_key_and_count():
    entries = [make_entry(level="INFO"), make_entry(level="INFO")]
    groups = aggregate_by_field(entries, "level")
    output = format_aggregate(groups)
    assert "INFO" in output
    assert "count=2" in output


def test_format_aggregate_empty_key_shows_placeholder():
    entries = [make_entry()]
    groups = aggregate_by_field(entries, "nonexistent")
    output = format_aggregate(groups)
    assert "(empty)" in output
