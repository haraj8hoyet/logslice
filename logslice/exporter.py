"""Export log summaries and entry batches to external formats."""

from __future__ import annotations

import csv
import io
import json
from typing import IO, Iterable

from logslice.parser import LogEntry
from logslice.summarizer import LogSummary, format_summary, summarize


def export_summary_json(entries: Iterable[LogEntry], fp: IO[str], top_n: int = 5) -> None:
    """Write a JSON summary of entries to *fp*."""
    summary = summarize(entries, top_n=top_n)
    payload = {
        "total": summary.total,
        "unique_levels": summary.unique_levels,
        "first_timestamp": summary.first_timestamp,
        "last_timestamp": summary.last_timestamp,
        "top_levels": [dict(level=l, count=c) for l, c in summary.top_levels],
        "top_messages": [dict(message=m, count=c) for m, c in summary.top_messages],
    }
    json.dump(payload, fp, indent=2)
    fp.write("\n")


def export_summary_text(entries: Iterable[LogEntry], fp: IO[str], top_n: int = 5) -> None:
    """Write a plain-text summary of entries to *fp*."""
    summary = summarize(entries, top_n=top_n)
    fp.write(format_summary(summary))
    fp.write("\n")


def export_entries_csv(
    entries: Iterable[LogEntry],
    fp: IO[str],
    fields: tuple[str, ...] = ("timestamp", "level", "message"),
) -> None:
    """Write entries as CSV rows to *fp* with a header row."""
    writer = csv.writer(fp)
    writer.writerow(fields)
    for entry in entries:
        row = []
        for f in fields:
            if f == "timestamp":
                row.append(str(entry.timestamp) if entry.timestamp is not None else "")
            elif f == "level":
                row.append(entry.level or "")
            elif f == "message":
                row.append(entry.message or "")
            else:
                row.append(entry.fields.get(f, ""))
        writer.writerow(row)


def summary_to_string(summary: LogSummary) -> str:
    """Return a formatted summary as a string (convenience wrapper)."""
    buf = io.StringIO()
    buf.write(format_summary(summary))
    return buf.getvalue()
