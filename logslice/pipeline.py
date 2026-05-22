"""High-level pipeline that chains reading, filtering, deduplication, and output."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import IO, Iterable, Iterator

from logslice.parser import LogEntry
from logslice.reader import iter_entries
from logslice.filter import apply_filters
from logslice.dedup import dedup_entries
from logslice.output import write_entries_streaming


def build_pipeline(
    source: Path | IO[str],
    *,
    start: datetime | None = None,
    end: datetime | None = None,
    level: str | None = None,
    pattern: str | None = None,
    dedup: bool = False,
    dedup_fields: tuple[str, ...] = ("level", "message"),
    dedup_keep: str = "first",
) -> Iterator[LogEntry]:
    """Produce a filtered (and optionally deduplicated) stream of log entries.

    Args:
        source: A file path or readable file-like object.
        start: Inclusive lower bound for timestamp filtering.
        end: Inclusive upper bound for timestamp filtering.
        level: Exact log level to keep (case-insensitive).
        pattern: Regex pattern to match against the raw log line.
        dedup: Whether to remove duplicate entries.
        dedup_fields: Fields used for duplicate detection.
        dedup_keep: ``'first'`` or ``'last'`` duplicate retention strategy.

    Yields:
        Processed LogEntry objects.
    """
    if isinstance(source, Path):
        with source.open() as fh:
            entries: Iterable[LogEntry] = list(iter_entries(fh))
    else:
        entries = iter_entries(source)

    filtered = apply_filters(
        entries,
        start=start,
        end=end,
        level=level,
        pattern=pattern,
    )

    if dedup:
        filtered = dedup_entries(filtered, fields=dedup_fields, keep=dedup_keep)

    yield from filtered


def run_pipeline(
    source: Path | IO[str],
    dest: IO[str],
    *,
    fmt: str = "text",
    start: datetime | None = None,
    end: datetime | None = None,
    level: str | None = None,
    pattern: str | None = None,
    dedup: bool = False,
    dedup_fields: tuple[str, ...] = ("level", "message"),
    dedup_keep: str = "first",
    csv_header: bool = True,
) -> int:
    """Run the full pipeline and write results to *dest*.

    Returns the number of entries written.
    """
    entries = build_pipeline(
        source,
        start=start,
        end=end,
        level=level,
        pattern=pattern,
        dedup=dedup,
        dedup_fields=dedup_fields,
        dedup_keep=dedup_keep,
    )
    return write_entries_streaming(entries, dest, fmt=fmt, csv_header=csv_header)
