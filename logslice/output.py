"""Output writer for formatted log entries."""

import sys
from typing import IO, Iterable, List, Optional
from logslice.parser import LogEntry
from logslice.formatter import format_entries, csv_header


def write_entries(
    entries: List[LogEntry],
    fmt: str = "text",
    dest: IO = None,
    include_csv_header: bool = True,
) -> int:
    """Write formatted log entries to a file-like object.

    Args:
        entries: Log entries to write.
        fmt: Output format ('text', 'json', 'csv').
        dest: File-like object to write to. Defaults to stdout.
        include_csv_header: Whether to prepend a CSV header row when fmt='csv'.

    Returns:
        Number of entries written.
    """
    if dest is None:
        dest = sys.stdout

    if fmt == "csv" and include_csv_header:
        dest.write(csv_header() + "\n")

    lines = format_entries(entries, fmt=fmt)
    for line in lines:
        dest.write(line + "\n")

    return len(lines)


def write_entries_streaming(
    entries: Iterable[LogEntry],
    fmt: str = "text",
    dest: IO = None,
    include_csv_header: bool = True,
) -> int:
    """Write log entries one at a time (memory-efficient for large files).

    Args:
        entries: Iterable of LogEntry objects.
        fmt: Output format ('text', 'json', 'csv').
        dest: File-like object to write to. Defaults to stdout.
        include_csv_header: Whether to prepend a CSV header row when fmt='csv'.

    Returns:
        Number of entries written.
    """
    if dest is None:
        dest = sys.stdout

    from logslice.formatter import format_text, format_json, format_csv

    formatter_map = {"text": format_text, "json": format_json, "csv": format_csv}
    if fmt not in formatter_map:
        raise ValueError(f"Unsupported format '{fmt}'")

    formatter = formatter_map[fmt]

    if fmt == "csv" and include_csv_header:
        dest.write(csv_header() + "\n")

    count = 0
    for entry in entries:
        dest.write(formatter(entry) + "\n")
        count += 1

    return count
