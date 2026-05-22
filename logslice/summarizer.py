"""Summarize log entries into human-readable digest reports."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Iterable, List, Optional

from logslice.parser import LogEntry


@dataclass
class LogSummary:
    total: int = 0
    top_levels: List[tuple] = field(default_factory=list)
    top_messages: List[tuple] = field(default_factory=list)
    first_timestamp: Optional[str] = None
    last_timestamp: Optional[str] = None
    unique_levels: int = 0


def summarize(entries: Iterable[LogEntry], top_n: int = 5) -> LogSummary:
    """Compute a summary from an iterable of log entries."""
    level_counter: Counter = Counter()
    message_counter: Counter = Counter()
    timestamps = []
    total = 0

    for entry in entries:
        total += 1
        level = (entry.level or "UNKNOWN").upper()
        level_counter[level] += 1
        if entry.message:
            message_counter[entry.message] += 1
        if entry.timestamp is not None:
            timestamps.append(entry.timestamp)

    summary = LogSummary(
        total=total,
        top_levels=level_counter.most_common(top_n),
        top_messages=message_counter.most_common(top_n),
        unique_levels=len(level_counter),
    )

    if timestamps:
        summary.first_timestamp = str(min(timestamps))
        summary.last_timestamp = str(max(timestamps))

    return summary


def format_summary(summary: LogSummary) -> str:
    """Render a LogSummary as a plain-text report."""
    lines = [
        f"Total entries : {summary.total}",
        f"Unique levels : {summary.unique_levels}",
    ]

    if summary.first_timestamp:
        lines.append(f"First entry   : {summary.first_timestamp}")
    if summary.last_timestamp:
        lines.append(f"Last entry    : {summary.last_timestamp}")

    if summary.top_levels:
        lines.append("Top levels:")
        for lvl, cnt in summary.top_levels:
            lines.append(f"  {lvl:<10} {cnt}")

    if summary.top_messages:
        lines.append("Top messages:")
        for msg, cnt in summary.top_messages:
            short = msg[:60] + "..." if len(msg) > 60 else msg
            lines.append(f"  [{cnt:>4}x] {short}")

    return "\n".join(lines)
