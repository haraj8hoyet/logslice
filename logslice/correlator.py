"""Correlate log entries across streams by matching field values or time proximity."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Iterable, List, Optional, Tuple

from logslice.parser import LogEntry


@dataclass
class CorrelatedGroup:
    """A group of entries from multiple streams that share a correlation key."""

    key: str
    entries: List[Tuple[str, LogEntry]] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.entries)

    @property
    def stream_names(self) -> List[str]:
        return [name for name, _ in self.entries]


def correlate_by_field(
    streams: Dict[str, Iterable[LogEntry]],
    field_name: str,
) -> List[CorrelatedGroup]:
    """Group entries from multiple named streams by a shared field value.

    Args:
        streams: Mapping of stream name -> iterable of LogEntry.
        field_name: The extra field key to correlate on.

    Returns:
        List of CorrelatedGroup, one per unique field value seen.
    """
    groups: Dict[str, CorrelatedGroup] = {}
    for stream_name, entries in streams.items():
        for entry in entries:
            value = entry.extra.get(field_name, "") if entry.extra else ""
            if value not in groups:
                groups[value] = CorrelatedGroup(key=value)
            groups[value].entries.append((stream_name, entry))
    return list(groups.values())


def correlate_by_time(
    streams: Dict[str, Iterable[LogEntry]],
    window: timedelta = timedelta(seconds=1),
) -> List[CorrelatedGroup]:
    """Group entries from multiple streams that fall within the same time window.

    Entries without a timestamp are skipped.

    Args:
        streams: Mapping of stream name -> iterable of LogEntry.
        window: Maximum time difference to consider entries correlated.

    Returns:
        List of CorrelatedGroup keyed by bucket start timestamp string.
    """
    all_entries: List[Tuple[str, LogEntry]] = []
    for stream_name, entries in streams.items():
        for entry in entries:
            if entry.timestamp is not None:
                all_entries.append((stream_name, entry))

    all_entries.sort(key=lambda t: t[1].timestamp)  # type: ignore[arg-type]

    groups: List[CorrelatedGroup] = []
    bucket_start: Optional[datetime] = None
    current_group: Optional[CorrelatedGroup] = None

    for stream_name, entry in all_entries:
        ts: datetime = entry.timestamp  # type: ignore[assignment]
        if bucket_start is None or (ts - bucket_start) > window:
            bucket_start = ts
            current_group = CorrelatedGroup(key=ts.isoformat())
            groups.append(current_group)
        current_group.entries.append((stream_name, entry))  # type: ignore[union-attr]

    return groups
