"""Sorting utilities for log entries."""

from __future__ import annotations

from typing import Iterable, Iterator, List, Literal

from logslice.parser import LogEntry

SortKey = Literal["timestamp", "level", "message"]
SortOrder = Literal["asc", "desc"]

_LEVEL_ORDER = {
    "debug": 0,
    "info": 1,
    "warning": 2,
    "warn": 2,
    "error": 3,
    "critical": 4,
    "fatal": 4,
}


def _level_rank(entry: LogEntry) -> int:
    """Return a numeric rank for the entry's level (unknown levels sort last)."""
    level = (entry.level or "").lower()
    return _LEVEL_ORDER.get(level, 99)


def _sort_key_fn(key: SortKey):
    """Return a key function suitable for sorted() based on *key*."""
    if key == "timestamp":
        # Entries without a timestamp sort to the end.
        return lambda e: (e.timestamp is None, e.timestamp)
    if key == "level":
        return _level_rank
    if key == "message":
        return lambda e: (e.message or "")
    raise ValueError(f"Unknown sort key: {key!r}")


def sort_entries(
    entries: Iterable[LogEntry],
    key: SortKey = "timestamp",
    order: SortOrder = "asc",
    stable: bool = True,
) -> List[LogEntry]:
    """Return a sorted list of *entries*.

    Parameters
    ----------
    entries:
        Iterable of :class:`~logslice.parser.LogEntry` objects.
    key:
        Field to sort by – ``"timestamp"``, ``"level"``, or ``"message"``.
    order:
        ``"asc"`` (default) or ``"desc"``.
    stable:
        When *True* (default) Python's stable sort preserves the original
        relative order of entries that compare equal.
    """
    if key not in ("timestamp", "level", "message"):
        raise ValueError(f"Unknown sort key: {key!r}")
    if order not in ("asc", "desc"):
        raise ValueError(f"Unknown sort order: {order!r}")

    reverse = order == "desc"
    return sorted(entries, key=_sort_key_fn(key), reverse=reverse)


def iter_sorted(
    entries: Iterable[LogEntry],
    key: SortKey = "timestamp",
    order: SortOrder = "asc",
) -> Iterator[LogEntry]:
    """Yield entries in sorted order (convenience wrapper around :func:`sort_entries`)."""
    yield from sort_entries(entries, key=key, order=order)
