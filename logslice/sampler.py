"""Log entry sampling: take every Nth entry or a random fraction."""

from __future__ import annotations

import random
from typing import Iterable, Iterator, List

from logslice.parser import LogEntry


def sample_nth(entries: Iterable[LogEntry], n: int) -> Iterator[LogEntry]:
    """Yield every *n*-th entry (1-based index).  n must be >= 1."""
    if n < 1:
        raise ValueError(f"n must be >= 1, got {n}")
    for idx, entry in enumerate(entries, start=1):
        if idx % n == 0:
            yield entry


def sample_fraction(
    entries: Iterable[LogEntry],
    fraction: float,
    seed: int | None = None,
) -> Iterator[LogEntry]:
    """Yield each entry with probability *fraction* (0.0 – 1.0)."""
    if not 0.0 < fraction <= 1.0:
        raise ValueError(f"fraction must be in (0, 1], got {fraction}")
    rng = random.Random(seed)
    for entry in entries:
        if rng.random() < fraction:
            yield entry


def sample_head(entries: Iterable[LogEntry], n: int) -> List[LogEntry]:
    """Return the first *n* entries."""
    if n < 0:
        raise ValueError(f"n must be >= 0, got {n}")
    result: List[LogEntry] = []
    for entry in entries:
        if len(result) >= n:
            break
        result.append(entry)
    return result


def sample_tail(entries: Iterable[LogEntry], n: int) -> List[LogEntry]:
    """Return the last *n* entries (buffers the full stream)."""
    if n < 0:
        raise ValueError(f"n must be >= 0, got {n}")
    from collections import deque
    buf: deque[LogEntry] = deque(maxlen=n)
    for entry in entries:
        buf.append(entry)
    return list(buf)
