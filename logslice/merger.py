"""Merge multiple sorted log entry streams into a single sorted stream."""

from __future__ import annotations

import heapq
from typing import Iterable, Iterator, List, Tuple

from logslice.parser import LogEntry


def _sort_key(entry: LogEntry) -> Tuple:
    """Return a sort key for a log entry, placing entries without timestamps last."""
    if entry.timestamp is not None:
        return (0, entry.timestamp, entry.raw)
    return (1, entry.raw)


def merge_sorted(
    *streams: Iterable[LogEntry],
) -> Iterator[LogEntry]:
    """Merge multiple pre-sorted log entry iterables into one sorted stream.

    Entries are ordered by timestamp (ascending). Entries without a timestamp
    are emitted after all timestamped entries, preserving their relative order
    across streams via a stable heap.

    Args:
        *streams: Any number of iterables yielding LogEntry objects.

    Yields:
        LogEntry objects in merged sorted order.
    """
    heap: List[Tuple] = []
    iters = [iter(s) for s in streams]

    for stream_idx, it in enumerate(iters):
        try:
            entry = next(it)
            heapq.heappush(heap, (_sort_key(entry), stream_idx, entry, it))
        except StopIteration:
            pass

    while heap:
        key, stream_idx, entry, it = heapq.heappop(heap)
        yield entry
        try:
            next_entry = next(it)
            heapq.heappush(
                heap,
                (_sort_key(next_entry), stream_idx, next_entry, it),
            )
        except StopIteration:
            pass


def merge_files(paths: List[str]) -> Iterator[LogEntry]:
    """Open multiple log files and merge their entries in sorted order.

    Args:
        paths: List of file paths to read and merge.

    Yields:
        LogEntry objects in merged sorted order.
    """
    from logslice.reader import iter_entries

    streams = [iter_entries(p) for p in paths]
    yield from merge_sorted(*streams)
