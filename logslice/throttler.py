"""Rate-based throttling of log entry streams.

Provides utilities to limit the number of entries yielded per time bucket,
useful for reducing noise from high-frequency log sources.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Iterator, Optional

from logslice.parser import LogEntry


def _bucket_key(ts: datetime, bucket_seconds: int) -> int:
    """Return an integer bucket index for the given timestamp."""
    return int(ts.timestamp()) // bucket_seconds


def throttle_by_time(
    entries: Iterator[LogEntry],
    max_per_bucket: int,
    bucket_seconds: int = 60,
) -> Iterator[LogEntry]:
    """Yield at most *max_per_bucket* entries per time bucket.

    Entries whose timestamp is None are always passed through unchanged.

    Args:
        entries: Source stream of LogEntry objects.
        max_per_bucket: Maximum entries to emit per bucket window.
        bucket_seconds: Width of each bucket in seconds (default 60).

    Raises:
        ValueError: If max_per_bucket or bucket_seconds is not positive.
    """
    if max_per_bucket < 1:
        raise ValueError("max_per_bucket must be >= 1")
    if bucket_seconds < 1:
        raise ValueError("bucket_seconds must be >= 1")

    counts: dict[int, int] = defaultdict(int)
    for entry in entries:
        if entry.timestamp is None:
            yield entry
            continue
        key = _bucket_key(entry.timestamp, bucket_seconds)
        if counts[key] < max_per_bucket:
            counts[key] += 1
            yield entry


def throttle_by_level(
    entries: Iterator[LogEntry],
    max_per_level: int,
) -> Iterator[LogEntry]:
    """Yield at most *max_per_level* entries for each distinct log level.

    Entries with no level (empty string) are counted together under ''.

    Args:
        entries: Source stream of LogEntry objects.
        max_per_level: Maximum entries to emit per level.

    Raises:
        ValueError: If max_per_level is not positive.
    """
    if max_per_level < 1:
        raise ValueError("max_per_level must be >= 1")

    counts: dict[str, int] = defaultdict(int)
    for entry in entries:
        level = (entry.level or "").upper()
        if counts[level] < max_per_level:
            counts[level] += 1
            yield entry
