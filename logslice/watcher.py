"""Tail-style log watcher: yields new LogEntry objects as lines are appended."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Generator, Optional

from logslice.parser import LogEntry, parse_line


def _open_at_end(path: Path):
    """Open *path* and seek to the end so only new lines are read."""
    fh = open(path, "r", encoding="utf-8", errors="replace")
    fh.seek(0, 2)  # SEEK_END
    return fh


def tail_file(
    path: str | Path,
    *,
    poll_interval: float = 0.25,
    max_iterations: Optional[int] = None,
) -> Generator[LogEntry, None, None]:
    """Yield LogEntry objects for every new line appended to *path*.

    Parameters
    ----------
    path:
        Path to the log file to watch.
    poll_interval:
        Seconds to sleep between read attempts when no data is available.
    max_iterations:
        If given, stop after this many poll loops (useful for testing).
    """
    path = Path(path)
    fh = _open_at_end(path)
    iterations = 0
    try:
        while True:
            line = fh.readline()
            if line:
                entry = parse_line(line.rstrip("\n"))
                yield entry
            else:
                if max_iterations is not None:
                    iterations += 1
                    if iterations >= max_iterations:
                        break
                time.sleep(poll_interval)
    finally:
        fh.close()


def collect_tail(
    path: str | Path,
    lines_to_append: list[str],
    *,
    poll_interval: float = 0.05,
) -> list[LogEntry]:
    """Helper used in tests: append *lines_to_append* to *path* and collect results.

    Writes lines one by one between ticks so tail_file can observe them.
    Returns the collected entries.
    """
    import threading

    path = Path(path)
    results: list[LogEntry] = []

    def _writer():
        time.sleep(poll_interval * 2)
        with open(path, "a", encoding="utf-8") as f:
            for line in lines_to_append:
                f.write(line + "\n")
                f.flush()
                time.sleep(poll_interval)

    t = threading.Thread(target=_writer, daemon=True)
    t.start()

    for entry in tail_file(path, poll_interval=poll_interval, max_iterations=len(lines_to_append) + 4):
        results.append(entry)

    t.join(timeout=5)
    return results
