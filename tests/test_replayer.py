"""Tests for logslice.replayer."""

import pytest
from datetime import datetime, timezone
from logslice.parser import LogEntry
from logslice.replayer import replay_entries, replay_realtime, collect_replay


def _dt(hour: int, minute: int = 0, second: int = 0) -> datetime:
    return datetime(2024, 1, 1, hour, minute, second, tzinfo=timezone.utc)


def make_entry(msg: str, ts: datetime | None = None) -> LogEntry:
    return LogEntry(
        raw=msg,
        timestamp=ts,
        level="INFO",
        message=msg,
        fields={},
    )


def test_replay_yields_all_entries():
    entries = [make_entry(f"msg{i}", _dt(0, i)) for i in range(4)]
    sleeps = []
    result = collect_replay(entries, speed=1.0, sleep_fn=sleeps.append)
    assert len(result) == 4


def test_replay_sleep_count_is_n_minus_one():
    entries = [make_entry(f"msg{i}", _dt(0, i)) for i in range(5)]
    sleeps = []
    collect_replay(entries, speed=1.0, sleep_fn=sleeps.append)
    # First entry has no previous, so N-1 sleeps
    assert len(sleeps) == 4


def test_replay_sleep_duration_proportional_to_gap():
    entries = [
        make_entry("a", _dt(0, 0, 0)),
        make_entry("b", _dt(0, 0, 10)),  # 10s gap
    ]
    sleeps = []
    collect_replay(entries, speed=1.0, max_delay=60.0, sleep_fn=sleeps.append)
    assert sleeps == [pytest.approx(10.0)]


def test_replay_speed_halves_delay():
    entries = [
        make_entry("a", _dt(0, 0, 0)),
        make_entry("b", _dt(0, 0, 20)),  # 20s gap at 2x speed => 10s
    ]
    sleeps = []
    collect_replay(entries, speed=2.0, max_delay=60.0, sleep_fn=sleeps.append)
    assert sleeps == [pytest.approx(10.0)]


def test_replay_max_delay_caps_sleep():
    entries = [
        make_entry("a", _dt(0, 0, 0)),
        make_entry("b", _dt(1, 0, 0)),  # 3600s gap
    ]
    sleeps = []
    collect_replay(entries, speed=1.0, max_delay=3.0, sleep_fn=sleeps.append)
    assert sleeps == [pytest.approx(3.0)]


def test_replay_no_sleep_for_entries_without_timestamp():
    entries = [
        make_entry("a", None),
        make_entry("b", None),
        make_entry("c", None),
    ]
    sleeps = []
    collect_replay(entries, speed=1.0, sleep_fn=sleeps.append)
    assert sleeps == []


def test_replay_no_sleep_for_negative_gap():
    """Entries with decreasing timestamps (e.g. rotation) should not sleep."""
    entries = [
        make_entry("a", _dt(1, 0, 0)),
        make_entry("b", _dt(0, 0, 0)),  # earlier than previous
    ]
    sleeps = []
    collect_replay(entries, speed=1.0, sleep_fn=sleeps.append)
    assert sleeps == []


def test_replay_invalid_speed_raises():
    with pytest.raises(ValueError, match="speed"):
        collect_replay([], speed=0.0)


def test_replay_negative_speed_raises():
    with pytest.raises(ValueError, match="speed"):
        collect_replay([], speed=-1.0)


def test_replay_negative_max_delay_raises():
    with pytest.raises(ValueError, match="max_delay"):
        collect_replay([], speed=1.0, max_delay=-1.0)


def test_replay_realtime_delegates_correctly():
    entries = [
        make_entry("a", _dt(0, 0, 0)),
        make_entry("b", _dt(0, 0, 5)),
    ]
    sleeps = []
    result = list(replay_realtime(entries, max_delay=60.0, sleep_fn=sleeps.append))
    assert len(result) == 2
    assert sleeps == [pytest.approx(5.0)]


def test_replay_preserves_entry_order():
    entries = [make_entry(str(i), _dt(0, i)) for i in range(6)]
    result = collect_replay(entries, sleep_fn=lambda _: None)
    assert [e.message for e in result] == [str(i) for i in range(6)]
