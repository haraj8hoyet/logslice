"""Deduplication utilities for log entries."""

from __future__ import annotations

import hashlib
from typing import Iterable, Iterator

from logslice.parser import LogEntry


def _entry_key(entry: LogEntry, fields: tuple[str, ...]) -> str:
    """Build a hash key from selected fields of a log entry."""
    parts = []
    if "level" in fields:
        parts.append(entry.level or "")
    if "message" in fields:
        parts.append(entry.message)
    if "source" in fields:
        parts.append(entry.source or "")
    raw = "\x00".join(parts)
    return hashlib.md5(raw.encode(), usedforsecurity=False).hexdigest()


def dedup_entries(
    entries: Iterable[LogEntry],
    fields: tuple[str, ...] = ("level", "message"),
    keep: str = "first",
) -> Iterator[LogEntry]:
    """Yield deduplicated log entries.

    Args:
        entries: Iterable of LogEntry objects.
        fields: Fields used to determine duplicates.
        keep: ``'first'`` keeps the first occurrence; ``'last'`` keeps the last.

    Yields:
        Unique LogEntry objects according to the chosen strategy.
    """
    if keep not in ("first", "last"):
        raise ValueError(f"keep must be 'first' or 'last', got {keep!r}")

    if keep == "first":
        seen: set[str] = set()
        for entry in entries:
            key = _entry_key(entry, fields)
            if key not in seen:
                seen.add(key)
                yield entry
    else:  # keep == "last"
        # Buffer all entries, then emit the last occurrence of each key.
        last: dict[str, LogEntry] = {}
        order: list[str] = []
        for entry in entries:
            key = _entry_key(entry, fields)
            if key not in last:
                order.append(key)
            last[key] = entry
        for key in order:
            yield last[key]


def count_duplicates(
    entries: Iterable[LogEntry],
    fields: tuple[str, ...] = ("level", "message"),
) -> dict[str, int]:
    """Return a mapping of entry-key -> occurrence count."""
    counts: dict[str, int] = {}
    for entry in entries:
        key = _entry_key(entry, fields)
        counts[key] = counts.get(key, 0) + 1
    return counts
