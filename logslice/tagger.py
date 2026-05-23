"""Tag log entries with user-defined labels based on field patterns."""

from __future__ import annotations

import re
from typing import Callable, Iterable, List, Optional, Sequence, Tuple

from logslice.parser import LogEntry

# A tagger rule: (tag_name, predicate)
TagRule = Tuple[str, Callable[[LogEntry], bool]]


def make_level_rule(tag: str, level: str) -> TagRule:
    """Return a rule that tags entries whose level matches *level* (case-insensitive)."""
    level_upper = level.upper()
    return (tag, lambda e: (e.level or "").upper() == level_upper)


def make_pattern_rule(tag: str, pattern: str, field: str = "message") -> TagRule:
    """Return a rule that tags entries where *field* matches *pattern* (regex)."""
    rx = re.compile(pattern)

    def _pred(entry: LogEntry) -> bool:
        value = entry.fields.get(field, "") if field not in ("message", "level") else getattr(entry, field, "") or ""
        return bool(rx.search(value))

    return (tag, _pred)


def tag_entry(entry: LogEntry, rules: Sequence[TagRule]) -> LogEntry:
    """Apply *rules* to *entry* and return a new entry with a 'tags' field populated.

    Existing tags in ``entry.fields['tags']`` are preserved.
    """
    existing: List[str] = []
    raw = entry.fields.get("tags", "")
    if raw:
        existing = [t.strip() for t in raw.split(",") if t.strip()]

    new_tags = list(existing)
    for tag_name, predicate in rules:
        if tag_name not in new_tags and predicate(entry):
            new_tags.append(tag_name)

    updated_fields = {**entry.fields, "tags": ",".join(new_tags)}
    return LogEntry(
        timestamp=entry.timestamp,
        level=entry.level,
        message=entry.message,
        fields=updated_fields,
        raw=entry.raw,
    )


def tag_entries(
    entries: Iterable[LogEntry],
    rules: Sequence[TagRule],
) -> Iterable[LogEntry]:
    """Lazily apply *rules* to each entry in *entries*."""
    for entry in entries:
        yield tag_entry(entry, rules)


def get_tags(entry: LogEntry) -> List[str]:
    """Return the list of tags attached to *entry* (may be empty)."""
    raw = entry.fields.get("tags", "")
    if not raw:
        return []
    return [t.strip() for t in raw.split(",") if t.strip()]
