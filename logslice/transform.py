"""Field-level transformations applied to LogEntry streams."""

from __future__ import annotations

import re
from typing import Callable, Iterable, Iterator

from logslice.parser import LogEntry


def _replace_entry(
    entry: LogEntry,
    *,
    message: str | None = None,
    level: str | None = None,
    fields: dict | None = None,
) -> LogEntry:
    """Return a shallow copy of *entry* with selected fields overridden."""
    return LogEntry(
        raw=entry.raw,
        message=message if message is not None else entry.message,
        level=level if level is not None else entry.level,
        timestamp=entry.timestamp,
        fields=fields if fields is not None else entry.fields,
    )


def normalize_level(entries: Iterable[LogEntry]) -> Iterator[LogEntry]:
    """Upper-case every entry's *level* field."""
    for entry in entries:
        new_level = entry.level.upper() if entry.level else entry.level
        yield _replace_entry(entry, level=new_level)


def redact_pattern(
    entries: Iterable[LogEntry],
    pattern: str,
    replacement: str = "***",
) -> Iterator[LogEntry]:
    """Replace all occurrences of *pattern* in *message* with *replacement*."""
    rx = re.compile(pattern)
    for entry in entries:
        new_msg = rx.sub(replacement, entry.message) if entry.message else entry.message
        yield _replace_entry(entry, message=new_msg)


def add_field(
    entries: Iterable[LogEntry],
    key: str,
    value_fn: Callable[[LogEntry], object],
) -> Iterator[LogEntry]:
    """Attach a computed field *key* to every entry's fields dict."""
    for entry in entries:
        new_fields = dict(entry.fields or {})
        new_fields[key] = value_fn(entry)
        yield _replace_entry(entry, fields=new_fields)


def drop_field(
    entries: Iterable[LogEntry],
    key: str,
) -> Iterator[LogEntry]:
    """Remove *key* from every entry's fields dict (no-op if absent)."""
    for entry in entries:
        new_fields = {k: v for k, v in (entry.fields or {}).items() if k != key}
        yield _replace_entry(entry, fields=new_fields)
