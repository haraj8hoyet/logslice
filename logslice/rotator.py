"""Log file rotation detector and segment splitter."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Iterable, Iterator, List, Optional

from logslice.parser import LogEntry


@dataclass
class RotationSegment:
    """A contiguous slice of log entries belonging to one rotation segment."""

    index: int
    entries: List[LogEntry] = field(default_factory=list)
    earliest: Optional[datetime] = None
    latest: Optional[datetime] = None

    def __len__(self) -> int:  # noqa: D105
        return len(self.entries)


def _update_bounds(
    segment: RotationSegment, ts: Optional[datetime]
) -> None:
    if ts is None:
        return
    if segment.earliest is None or ts < segment.earliest:
        segment.earliest = ts
    if segment.latest is None or ts > segment.latest:
        segment.latest = ts


def detect_rotation(
    entries: Iterable[LogEntry],
    *,
    max_gap_seconds: float = 3600.0,
) -> List[RotationSegment]:
    """Split *entries* into segments whenever a backwards time jump is detected.

    A new segment is also started when the gap between consecutive timestamps
    exceeds *max_gap_seconds* and the next timestamp is earlier than the
    previous one (i.e. the file was rotated and a new file started from zero).

    Parameters
    ----------
    entries:
        Iterable of :class:`~logslice.parser.LogEntry` objects.
    max_gap_seconds:
        Minimum gap (in seconds) that, combined with a timestamp regression,
        triggers a new segment.  Pass ``0`` to split on any backwards jump.
    """
    if max_gap_seconds < 0:
        raise ValueError("max_gap_seconds must be >= 0")

    segments: List[RotationSegment] = []
    current: Optional[RotationSegment] = None
    prev_ts: Optional[datetime] = None

    for entry in entries:
        ts = entry.timestamp
        if current is None:
            current = RotationSegment(index=0)
            segments.append(current)

        if ts is not None and prev_ts is not None:
            gap = (ts - prev_ts).total_seconds()
            if gap < -max_gap_seconds:
                # Backwards jump — start a new segment
                current = RotationSegment(index=len(segments))
                segments.append(current)

        current.entries.append(entry)
        _update_bounds(current, ts)
        if ts is not None:
            prev_ts = ts

    return segments


def iter_segments(
    segments: Iterable[RotationSegment],
) -> Iterator[LogEntry]:
    """Yield all entries from *segments* in segment order."""
    for seg in segments:
        yield from seg.entries


def segment_summary(segments: List[RotationSegment]) -> List[Dict[str, object]]:
    """Return a list of plain dicts summarising each segment."""
    return [
        {
            "index": seg.index,
            "count": len(seg),
            "earliest": seg.earliest.isoformat() if seg.earliest else None,
            "latest": seg.latest.isoformat() if seg.latest else None,
        }
        for seg in segments
    ]
