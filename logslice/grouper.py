"""Group log entries by a field value or time bucket."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Iterable, List, Optional

from logslice.parser import LogEntry


def group_by_field(entries: Iterable[LogEntry], field: str) -> Dict[str, List[LogEntry]]:
    """Group entries by *field* value.  Missing field maps to key ''."""
    groups: Dict[str, List[LogEntry]] = defaultdict(list)
    for entry in entries:
        key = entry.fields.get(field, "") if entry.fields else ""
        if field == "level":
            key = entry.level or ""
        groups[key].append(entry)
    return dict(groups)


def group_by_time_bucket(
    entries: Iterable[LogEntry],
    bucket_seconds: int = 60,
) -> Dict[datetime, List[LogEntry]]:
    """Group entries into fixed-width time buckets.

    Entries without a timestamp are collected under key *None* (omitted from
    the returned dict; callers that need them should pre-filter).
    """
    if bucket_seconds <= 0:
        raise ValueError(f"bucket_seconds must be > 0, got {bucket_seconds}")

    groups: Dict[datetime, List[LogEntry]] = defaultdict(list)
    delta = timedelta(seconds=bucket_seconds)

    for entry in entries:
        if entry.timestamp is None:
            continue
        # Floor to nearest bucket
        epoch = datetime(1970, 1, 1)
        elapsed = (entry.timestamp.replace(tzinfo=None) - epoch).total_seconds()
        bucket_index = int(elapsed // bucket_seconds)
        bucket_start = epoch + delta * bucket_index
        groups[bucket_start].append(entry)

    return dict(groups)


def sorted_groups(
    groups: Dict[str, List[LogEntry]],
    by_count: bool = False,
) -> List[tuple[str, List[LogEntry]]]:
    """Return groups as a sorted list of (key, entries) pairs."""
    items = list(groups.items())
    if by_count:
        items.sort(key=lambda kv: len(kv[1]), reverse=True)
    else:
        items.sort(key=lambda kv: kv[0])
    return items
