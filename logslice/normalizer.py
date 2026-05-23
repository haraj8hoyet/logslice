"""Normalize log entries: standardize levels, strip whitespace, unify timestamps."""

from __future__ import annotations

from typing import Iterable, Iterator, Optional

from logslice.parser import LogEntry
from logslice.transform import _replace_entry

_LEVEL_ALIASES: dict[str, str] = {
    "warn": "WARNING",
    "warning": "WARNING",
    "err": "ERROR",
    "error": "ERROR",
    "crit": "CRITICAL",
    "critical": "CRITICAL",
    "info": "INFO",
    "information": "INFO",
    "dbg": "DEBUG",
    "debug": "DEBUG",
    "fatal": "CRITICAL",
    "trace": "DEBUG",
}


def normalize_level_field(entry: LogEntry) -> LogEntry:
    """Return a new entry with the level field standardized to uppercase canonical form."""
    if entry.level is None:
        return entry
    key = entry.level.strip().lower()
    canonical = _LEVEL_ALIASES.get(key, entry.level.strip().upper())
    return _replace_entry(entry, level=canonical)


def strip_message(entry: LogEntry) -> LogEntry:
    """Return a new entry with leading/trailing whitespace removed from the message."""
    if entry.message is None:
        return entry
    return _replace_entry(entry, message=entry.message.strip())


def normalize_entry(entry: LogEntry, *, standardize_level: bool = True, strip_whitespace: bool = True) -> LogEntry:
    """Apply all normalization steps to a single entry.

    Parameters
    ----------
    entry:
        The source log entry.
    standardize_level:
        When *True* the level field is mapped to a canonical uppercase value.
    strip_whitespace:
        When *True* leading/trailing whitespace is removed from the message.
    """
    if standardize_level:
        entry = normalize_level_field(entry)
    if strip_whitespace:
        entry = strip_message(entry)
    return entry


def normalize_entries(
    entries: Iterable[LogEntry],
    *,
    standardize_level: bool = True,
    strip_whitespace: bool = True,
) -> Iterator[LogEntry]:
    """Yield normalized versions of every entry in *entries*."""
    for entry in entries:
        yield normalize_entry(entry, standardize_level=standardize_level, strip_whitespace=strip_whitespace)
