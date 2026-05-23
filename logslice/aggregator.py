"""Aggregate log entries by a field, computing counts and message samples."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional

from logslice.parser import LogEntry


@dataclass
class AggregateGroup:
    key: str
    count: int = 0
    samples: List[str] = field(default_factory=list)
    max_samples: int = 3

    def add(self, entry: LogEntry) -> None:
        self.count += 1
        if len(self.samples) < self.max_samples:
            self.samples.append(entry.message)

    def __repr__(self) -> str:  # pragma: no cover
        return f"AggregateGroup(key={self.key!r}, count={self.count})"


def aggregate_by_field(
    entries: Iterable[LogEntry],
    field_name: str,
    max_samples: int = 3,
) -> Dict[str, AggregateGroup]:
    """Group entries by *field_name* and count occurrences.

    The field is looked up first in ``extra``, then as a top-level attribute
    (``level``, ``message``).  Missing fields map to an empty-string key.
    """
    if max_samples < 0:
        raise ValueError("max_samples must be >= 0")

    groups: Dict[str, AggregateGroup] = defaultdict(
        lambda: AggregateGroup(key="", max_samples=max_samples)
    )

    for entry in entries:
        value = _get_field(entry, field_name)
        if value not in groups:
            groups[value] = AggregateGroup(key=value, max_samples=max_samples)
        groups[value].add(entry)

    return dict(groups)


def top_groups(
    groups: Dict[str, AggregateGroup],
    n: Optional[int] = None,
) -> List[AggregateGroup]:
    """Return groups sorted by count descending, optionally limited to *n*."""
    sorted_groups = sorted(groups.values(), key=lambda g: g.count, reverse=True)
    return sorted_groups[:n] if n is not None else sorted_groups


def format_aggregate(groups: Dict[str, AggregateGroup]) -> str:
    """Return a human-readable summary of aggregated groups."""
    lines: List[str] = []
    for group in top_groups(groups):
        sample_str = "; ".join(group.samples)
        lines.append(f"{group.key or '(empty)':20s}  count={group.count}  samples=[{sample_str}]")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_field(entry: LogEntry, field_name: str) -> str:
    if field_name in entry.extra:
        return str(entry.extra[field_name])
    value = getattr(entry, field_name, None)
    if value is None:
        return ""
    return str(value)
