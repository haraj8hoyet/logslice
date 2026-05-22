"""File reader that streams parsed log entries from a file or stdin."""

import sys
from pathlib import Path
from typing import Iterator, Optional, Union

from logslice.parser import LogEntry, parse_line
import re


def iter_entries(
    source: Union[str, Path, None] = None,
    pattern: Optional[re.Pattern] = None,
) -> Iterator[LogEntry]:
    """
    Stream LogEntry objects from a file path or stdin.

    Args:
        source: Path to a log file. If None, reads from stdin.
        pattern: Optional compiled regex to override the default parser pattern.
    """
    kwargs = {"pattern": pattern} if pattern else {}

    if source is None:
        for line in sys.stdin:
            yield parse_line(line, **kwargs)
        return

    path = Path(source)
    if not path.exists():
        raise FileNotFoundError(f"Log file not found: {path}")
    if not path.is_file():
        raise ValueError(f"Path is not a file: {path}")

    with path.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            yield parse_line(line, **kwargs)


def count_entries(source: Union[str, Path, None] = None) -> int:
    """Count total parseable (valid) log entries in a file."""
    return sum(1 for e in iter_entries(source) if e.is_valid())
