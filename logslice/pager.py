"""Paged terminal output for log entries."""

import os
import sys
from typing import Iterable, Optional

from logslice.formatter import format_entries
from logslice.highlight import highlight_line, strip_ansi


def _terminal_height() -> int:
    """Return the current terminal height, defaulting to 24."""
    try:
        return os.get_terminal_size().lines
    except OSError:
        return 24


def _supports_color(stream) -> bool:
    """Return True if the stream appears to support ANSI color codes."""
    return hasattr(stream, "isatty") and stream.isatty()


def print_paged(
    lines: Iterable[str],
    page_size: Optional[int] = None,
    colorize: bool = True,
    search: Optional[str] = None,
    stream=None,
) -> None:
    """
    Print lines to stream, pausing every `page_size` lines.

    If stream is not a tty or page_size is 0/None and not a tty,
    lines are printed without pausing.
    """
    if stream is None:
        stream = sys.stdout

    use_color = colorize and _supports_color(stream)
    interactive = _supports_color(stream)
    effective_page = page_size if page_size else (_terminal_height() - 1)

    count = 0
    for line in lines:
        display = highlight_line(line, search=search, colorize=use_color)
        stream.write(display + "\n")
        count += 1

        if interactive and count % effective_page == 0:
            try:
                stream.write("-- More -- (press Enter) ")
                stream.flush()
                input()
            except (EOFError, KeyboardInterrupt):
                stream.write("\n")
                break

    stream.flush()


def render_entries(
    entries,
    fmt: str = "text",
    colorize: bool = True,
    search: Optional[str] = None,
    page_size: Optional[int] = None,
    stream=None,
) -> None:
    """Format log entries and send them to paged output."""
    if stream is None:
        stream = sys.stdout

    lines = list(format_entries(entries, fmt=fmt))
    print_paged(lines, page_size=page_size, colorize=colorize, search=search, stream=stream)
