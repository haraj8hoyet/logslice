"""Annotate log entries with extra metadata fields derived from existing content."""

from __future__ import annotations

import re
from typing import Callable, Dict, Iterable, List, Optional

from logslice.parser import LogEntry
from logslice.transform import _replace_entry


AnnotatorFn = Callable[[LogEntry], Optional[Dict[str, str]]]


def annotate_with_regex(
    entry: LogEntry,
    pattern: str,
    field_map: Dict[str, str],
) -> Optional[Dict[str, str]]:
    """Return extra fields by matching *pattern* against the entry message.

    *field_map* maps regex group names to the field names that should be added
    to the entry.  Returns ``None`` when the pattern does not match.
    """
    match = re.search(pattern, entry.message or "")
    if not match:
        return None
    result: Dict[str, str] = {}
    for group_name, field_name in field_map.items():
        value = match.groupdict().get(group_name)
        if value is not None:
            result[field_name] = value
    return result or None


def annotate_entry(
    entry: LogEntry,
    annotators: List[AnnotatorFn],
) -> LogEntry:
    """Apply every annotator in *annotators* to *entry*, merging returned fields.

    Each annotator receives the (possibly already-updated) entry so later
    annotators can build on earlier ones.
    """
    extra: Dict[str, str] = dict(entry.extra or {})
    current = entry
    for fn in annotators:
        additions = fn(current)
        if additions:
            extra.update(additions)
            current = _replace_entry(current, extra=extra)
    return current


def annotate_entries(
    entries: Iterable[LogEntry],
    annotators: List[AnnotatorFn],
) -> Iterable[LogEntry]:
    """Yield each entry after running all *annotators* over it."""
    for entry in entries:
        yield annotate_entry(entry, annotators)


def make_regex_annotator(
    pattern: str,
    field_map: Dict[str, str],
) -> AnnotatorFn:
    """Return a reusable annotator function for the given pattern and field map."""
    def _annotator(entry: LogEntry) -> Optional[Dict[str, str]]:
        return annotate_with_regex(entry, pattern, field_map)
    return _annotator
