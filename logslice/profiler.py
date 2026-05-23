"""Profiler: measure and report parsing/filtering performance metrics."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Iterable, Iterator

from logslice.parser import LogEntry


@dataclass
class ProfileResult:
    elapsed_seconds: float
    entries_processed: int
    entries_yielded: int
    throughput_per_sec: float
    skipped: int

    def summary(self) -> str:
        return (
            f"Processed {self.entries_processed} entries in "
            f"{self.elapsed_seconds:.4f}s "
            f"({self.throughput_per_sec:.1f} entries/sec), "
            f"yielded {self.entries_yielded}, "
            f"skipped {self.skipped}"
        )


def profile_iter(
    source: Iterable[LogEntry],
    predicate=None,
) -> tuple[list[LogEntry], ProfileResult]:
    """Consume *source*, optionally filtering with *predicate*.

    Returns (matched_entries, ProfileResult).
    """
    start = time.perf_counter()
    processed = 0
    yielded = 0
    results: list[LogEntry] = []

    for entry in source:
        processed += 1
        if predicate is None or predicate(entry):
            results.append(entry)
            yielded += 1

    elapsed = time.perf_counter() - start
    throughput = processed / elapsed if elapsed > 0 else float("inf")
    skipped = processed - yielded

    result = ProfileResult(
        elapsed_seconds=round(elapsed, 6),
        entries_processed=processed,
        entries_yielded=yielded,
        throughput_per_sec=round(throughput, 2),
        skipped=skipped,
    )
    return results, result


def profile_iter_streaming(
    source: Iterable[LogEntry],
    predicate=None,
) -> Iterator[tuple[LogEntry, float]]:
    """Yield (entry, cumulative_elapsed) for each matched entry."""
    start = time.perf_counter()
    for entry in source:
        if predicate is None or predicate(entry):
            yield entry, round(time.perf_counter() - start, 6)
