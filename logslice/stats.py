"""Statistics and summary reporting for log entries."""

from collections import Counter
from dataclasses import dataclass, field
from typing import Iterable, Dict, List, Optional

from logslice.parser import LogEntry


@dataclass
class LogStats:
    total: int = 0
    by_level: Dict[str, int] = field(default_factory=dict)
    earliest: Optional[str] = None
    latest: Optional[str] = None
    top_sources: List[tuple] = field(default_factory=list)
    unparsed: int = 0


def compute_stats(entries: Iterable[LogEntry], top_n: int = 5) -> LogStats:
    """Compute summary statistics over an iterable of LogEntry objects."""
    level_counter: Counter = Counter()
    source_counter: Counter = Counter()
    earliest = None
    latest = None
    total = 0
    unparsed = 0

    for entry in entries:
        total += 1

        if not entry.timestamp:
            unparsed += 1

        level = (entry.fields.get("level") or "").upper() if entry.fields else ""
        if level:
            level_counter[level] += 1
        else:
            level_counter["UNKNOWN"] += 1

        source = entry.fields.get("source") if entry.fields else None
        if source:
            source_counter[source] += 1

        if entry.timestamp:
            ts = entry.timestamp.isoformat()
            if earliest is None or ts < earliest:
                earliest = ts
            if latest is None or ts > latest:
                latest = ts

    return LogStats(
        total=total,
        by_level=dict(level_counter),
        earliest=earliest,
        latest=latest,
        top_sources=source_counter.most_common(top_n),
        unparsed=unparsed,
    )


def format_stats(stats: LogStats) -> str:
    """Render a LogStats object as a human-readable summary string."""
    lines = [
        f"Total entries : {stats.total}",
        f"Unparsed      : {stats.unparsed}",
        f"Earliest      : {stats.earliest or 'n/a'}",
        f"Latest        : {stats.latest or 'n/a'}",
        "Levels        :",
    ]
    for level, count in sorted(stats.by_level.items()):
        lines.append(f"  {level:<10} {count}")
    if stats.top_sources:
        lines.append("Top sources   :")
        for src, count in stats.top_sources:
            lines.append(f"  {src:<20} {count}")
    return "\n".join(lines)
