"""Validate LogEntry objects against configurable rules."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Optional
from logslice.parser import LogEntry

KNOWN_LEVELS = {"DEBUG", "INFO", "WARNING", "WARN", "ERROR", "CRITICAL", "FATAL"}


@dataclass
class ValidationResult:
    entry: LogEntry
    errors: list[str] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        return len(self.errors) == 0


def validate_entry(
    entry: LogEntry,
    require_timestamp: bool = False,
    require_level: bool = False,
    known_levels: Optional[set[str]] = None,
    min_message_len: int = 1,
) -> ValidationResult:
    """Validate a single LogEntry and return a ValidationResult."""
    errors: list[str] = []

    if require_timestamp and entry.timestamp is None:
        errors.append("missing timestamp")

    if require_level and not entry.level:
        errors.append("missing level")

    if entry.level:
        levels = known_levels if known_levels is not None else KNOWN_LEVELS
        if entry.level.upper() not in levels:
            errors.append(f"unknown level: {entry.level!r}")

    if len(entry.message.strip()) < min_message_len:
        errors.append(f"message too short (min {min_message_len})")

    return ValidationResult(entry=entry, errors=errors)


def validate_entries(
    entries: Iterable[LogEntry],
    **kwargs,
) -> Iterable[ValidationResult]:
    """Yield a ValidationResult for every entry."""
    for entry in entries:
        yield validate_entry(entry, **kwargs)


def filter_valid(
    entries: Iterable[LogEntry],
    **kwargs,
) -> Iterable[LogEntry]:
    """Yield only entries that pass all validation rules."""
    for result in validate_entries(entries, **kwargs):
        if result.valid:
            yield result.entry
