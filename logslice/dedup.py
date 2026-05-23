"""Deduplication utilities for log entries."""

from __future__ import annotations

import hashlib
from typing import Iterable, Iterator

from logslice.parser import LogEntry

VALID_FIELDS = frozenset({"level", "message", "source"})


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


def _validate_dedup_args(fields: tuple[str, ...], keep: str) -> None:
    """Validate common arguments shared by dedup functions.

    Raises:
        ValueError: If ``keep`` is not ``'first'`` or ``'last'``, if
            ``fields`` is empty, or if ``fields`` contains an unrecognised
            field name.
    """
    if keep not in ("first", "last"):
        raise ValueError(f"keep must be 'first' or 'last', got {keep!r}")

    if not fields:
        raise ValueError("fields must not be empty")

    unknown_fields = set(fields) - VALID_FIELDS
    if unknown_fields:
        raise ValueError(
            f"unknown field(s): {sorted(unknown_fields)}; "
            f"valid fields are {sorted(VALID_FIELDS)}"
        )


def dedup_entries(
    entries: Iterable[LogEntry],
    fields: tuple[str, ...] = ("level", "message"),
    keep: str = "first",
) -> Iterator[LogEntry]:
    """Yield deduplicated log entries.

    Args:
        entries: Iterable of LogEntry objects.
        fields: Fields used to determine duplicates. Valid values are
            ``'level'``, ``'message'``, and ``'source'``.
        keep: ``'first'`` keeps the first occurrence; ``'last'`` keeps the last.

    Yields:
        Unique LogEntry objects according to the chosen strategy.

    Raises:
        ValueError: If ``keep`` is not ``'first'`` or ``'last'``, or if
            ``fields`` contains an unrecognised field name.
    """
    _validate_dedup_args(fields, keep)

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
