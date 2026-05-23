"""Split a stream of log entries into chunks by count or size."""

from __future__ import annotations

from typing import Generator, Iterable, List

from logslice.parser import LogEntry


def split_by_count(
    entries: Iterable[LogEntry], chunk_size: int
) -> Generator[List[LogEntry], None, None]:
    """Yield successive lists of *chunk_size* entries.

    Args:
        entries: Iterable of LogEntry objects.
        chunk_size: Maximum number of entries per chunk.  Must be >= 1.

    Yields:
        Non-empty lists of LogEntry objects.

    Raises:
        ValueError: If *chunk_size* is less than 1.
    """
    if chunk_size < 1:
        raise ValueError(f"chunk_size must be >= 1, got {chunk_size}")

    chunk: List[LogEntry] = []
    for entry in entries:
        chunk.append(entry)
        if len(chunk) == chunk_size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk


def split_by_field(
    entries: Iterable[LogEntry], field: str
) -> Generator[tuple[str, List[LogEntry]], None, None]:
    """Group consecutive entries that share the same value for *field*.

    Unlike :func:`logslice.grouper.group_by_field`, this function preserves
    run-length order — a new chunk starts whenever the field value changes.

    Args:
        entries: Iterable of LogEntry objects.
        field: Attribute name on LogEntry (e.g. ``"level"``).

    Yields:
        ``(value, chunk)`` tuples where *value* is the field value and
        *chunk* is the list of consecutive entries sharing that value.
    """
    current_value: str | None = None
    chunk: List[LogEntry] = []

    for entry in entries:
        value = str(getattr(entry, field, "") or "")
        if current_value is None:
            current_value = value
        if value != current_value:
            yield current_value, chunk
            chunk = []
            current_value = value
        chunk.append(entry)

    if chunk and current_value is not None:
        yield current_value, chunk
