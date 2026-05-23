"""Tests for logslice.rotator."""

from datetime import datetime, timezone
from typing import Optional

import pytest

from logslice.parser import LogEntry
from logslice.rotator import (
    RotationSegment,
    detect_rotation,
    iter_segments,
    segment_summary,
)


def make_entry(ts: Optional[datetime], message: str = "msg") -> LogEntry:
    return LogEntry(
        raw=message,
        timestamp=ts,
        level="INFO",
        message=message,
        fields={},
    )


def dt(hour: int, minute: int = 0) -> datetime:
    return datetime(2024, 1, 1, hour, minute, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# detect_rotation
# ---------------------------------------------------------------------------

def test_detect_rotation_single_segment_monotonic():
    entries = [make_entry(dt(1)), make_entry(dt(2)), make_entry(dt(3))]
    segs = detect_rotation(entries)
    assert len(segs) == 1
    assert len(segs[0]) == 3


def test_detect_rotation_splits_on_backwards_jump():
    entries = [
        make_entry(dt(10)),
        make_entry(dt(11)),
        make_entry(dt(1)),   # rotation — time goes backwards
        make_entry(dt(2)),
    ]
    segs = detect_rotation(entries, max_gap_seconds=0)
    assert len(segs) == 2
    assert len(segs[0]) == 2
    assert len(segs[1]) == 2


def test_detect_rotation_no_split_when_gap_within_threshold():
    # Jump of -30 min but threshold is 3600 s — should stay one segment
    entries = [
        make_entry(dt(10)),
        make_entry(dt(9, 30)),  # 30-minute regression
    ]
    segs = detect_rotation(entries, max_gap_seconds=3600.0)
    assert len(segs) == 1


def test_detect_rotation_none_timestamps_do_not_split():
    entries = [
        make_entry(dt(1)),
        make_entry(None),
        make_entry(None),
        make_entry(dt(2)),
    ]
    segs = detect_rotation(entries)
    assert len(segs) == 1


def test_detect_rotation_empty_input_returns_empty():
    assert detect_rotation([]) == []


def test_detect_rotation_segment_indices_are_sequential():
    entries = [
        make_entry(dt(5)),
        make_entry(dt(1)),  # rotation
        make_entry(dt(3)),  # rotation
    ]
    segs = detect_rotation(entries, max_gap_seconds=0)
    assert [s.index for s in segs] == [0, 1, 2]


def test_detect_rotation_bounds_tracked():
    entries = [make_entry(dt(2)), make_entry(dt(4)), make_entry(dt(3))]
    segs = detect_rotation(entries, max_gap_seconds=0)
    # No backwards jump > 0 for first two; dt(3) < dt(4) triggers split
    assert segs[0].earliest == dt(2)
    assert segs[0].latest == dt(4)
    assert segs[1].earliest == dt(3)


def test_detect_rotation_invalid_gap_raises():
    with pytest.raises(ValueError):
        detect_rotation([], max_gap_seconds=-1)


# ---------------------------------------------------------------------------
# iter_segments
# ---------------------------------------------------------------------------

def test_iter_segments_yields_all_entries_in_order():
    e1, e2, e3 = make_entry(dt(1)), make_entry(dt(2)), make_entry(dt(3))
    seg0 = RotationSegment(index=0, entries=[e1, e2])
    seg1 = RotationSegment(index=1, entries=[e3])
    result = list(iter_segments([seg0, seg1]))
    assert result == [e1, e2, e3]


# ---------------------------------------------------------------------------
# segment_summary
# ---------------------------------------------------------------------------

def test_segment_summary_structure():
    entries = [make_entry(dt(1)), make_entry(dt(5)), make_entry(dt(2))]
    segs = detect_rotation(entries, max_gap_seconds=0)
    summary = segment_summary(segs)
    assert isinstance(summary, list)
    for item in summary:
        assert "index" in item
        assert "count" in item
        assert "earliest" in item
        assert "latest" in item


def test_segment_summary_null_timestamps_when_no_ts():
    entries = [make_entry(None), make_entry(None)]
    segs = detect_rotation(entries)
    summary = segment_summary(segs)
    assert summary[0]["earliest"] is None
    assert summary[0]["latest"] is None
