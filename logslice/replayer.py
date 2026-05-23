"""Replay log entries with timing delays proportional to original timestamps."""

import time
from datetime import datetime, timedelta
from typing import Callable, Iterable, Iterator, Optional

from logslice.parser import LogEntry


def _entry_dt(entry: LogEntry) -> Optional[datetime]:
    """Return the parsed timestamp of an entry, or None."""
    return entry.timestamp


def replay_entries(
    entries: Iterable[LogEntry],
    speed: float = 1.0,
    max_delay: float = 5.0,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> Iterator[LogEntry]:
    """Yield entries with inter-arrival delays proportional to original timestamps.

    Args:
        entries:   Source log entries (must have timestamps to observe delays).
        speed:     Playback multiplier; 2.0 means twice as fast, 0.5 half speed.
        max_delay: Cap on any single sleep in seconds to avoid long pauses.
        sleep_fn:  Callable used for sleeping; injectable for testing.

    Yields:
        Each entry after the appropriate delay.
    """
    if speed <= 0:
        raise ValueError(f"speed must be positive, got {speed!r}")
    if max_delay < 0:
        raise ValueError(f"max_delay must be non-negative, got {max_delay!r}")

    prev_ts: Optional[datetime] = None

    for entry in entries:
        ts = _entry_dt(entry)
        if ts is not None and prev_ts is not None:
            gap: timedelta = ts - prev_ts
            seconds = gap.total_seconds() / speed
            if seconds > 0:
                sleep_fn(min(seconds, max_delay))
        prev_ts = ts
        yield entry


def replay_realtime(
    entries: Iterable[LogEntry],
    max_delay: float = 5.0,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> Iterator[LogEntry]:
    """Convenience wrapper for 1x real-time replay."""
    return replay_entries(entries, speed=1.0, max_delay=max_delay, sleep_fn=sleep_fn)


def collect_replay(
    entries: Iterable[LogEntry],
    speed: float = 1.0,
    max_delay: float = 5.0,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> list:
    """Drain a replay iterator into a list (useful for testing)."""
    return list(replay_entries(entries, speed=speed, max_delay=max_delay, sleep_fn=sleep_fn))
