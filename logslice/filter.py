"""Filtering utilities for log entries by time range and field patterns."""

import re
from datetime import datetime
from typing import Iterable, Iterator, Optional

from logslice.parser import LogEntry


def filter_by_time(
    entries: Iterable[LogEntry],
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
) -> Iterator[LogEntry]:
    """Yield entries whose timestamps fall within [start, end]."""
    for entry in entries:
        if not entry.is_valid():
            continue
        if start and entry.timestamp < start:
            continue
        if end and entry.timestamp > end:
            continue
        yield entry


def filter_by_level(
    entries: Iterable[LogEntry],
    levels: Iterable[str],
) -> Iterator[LogEntry]:
    """Yield entries matching any of the given log levels (case-insensitive)."""
    level_set = {lvl.upper() for lvl in levels}
    for entry in entries:
        if entry.level and entry.level.upper() in level_set:
            yield entry


def filter_by_pattern(
    entries: Iterable[LogEntry],
    pattern: str,
    field: str = "message",
) -> Iterator[LogEntry]:
    """Yield entries where the given field matches the regex pattern."""
    compiled = re.compile(pattern)
    for entry in entries:
        value = getattr(entry, field, None)
        if value and compiled.search(str(value)):
            yield entry


def apply_filters(
    entries: Iterable[LogEntry],
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    levels: Optional[Iterable[str]] = None,
    pattern: Optional[str] = None,
    pattern_field: str = "message",
) -> Iterator[LogEntry]:
    """Apply all active filters in sequence."""
    result = iter(entries)
    if start or end:
        result = filter_by_time(result, start=start, end=end)
    if levels:
        result = filter_by_level(result, levels)
    if pattern:
        result = filter_by_pattern(result, pattern, field=pattern_field)
    return result
