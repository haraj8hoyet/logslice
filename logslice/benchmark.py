"""Benchmark utilities: run timed trials over log pipelines."""

from __future__ import annotations

import statistics
from dataclasses import dataclass
from typing import Callable, Iterable

from logslice.parser import LogEntry
from logslice.profiler import profile_iter


@dataclass
class BenchmarkReport:
    trials: int
    mean_seconds: float
    median_seconds: float
    stdev_seconds: float
    min_seconds: float
    max_seconds: float
    mean_throughput: float

    def format(self) -> str:
        lines = [
            f"Trials        : {self.trials}",
            f"Mean          : {self.mean_seconds:.6f}s",
            f"Median        : {self.median_seconds:.6f}s",
            f"Std-dev       : {self.stdev_seconds:.6f}s",
            f"Min / Max     : {self.min_seconds:.6f}s / {self.max_seconds:.6f}s",
            f"Mean throughput: {self.mean_throughput:.1f} entries/sec",
        ]
        return "\n".join(lines)


def run_benchmark(
    entry_factory: Callable[[], Iterable[LogEntry]],
    predicate=None,
    trials: int = 5,
) -> BenchmarkReport:
    """Run *trials* iterations of profile_iter over entries from *entry_factory*.

    *entry_factory* is called fresh each trial so iterators are not exhausted.
    """
    if trials < 1:
        raise ValueError("trials must be >= 1")

    elapsed_times: list[float] = []
    throughputs: list[float] = []

    for _ in range(trials):
        _, prof = profile_iter(entry_factory(), predicate=predicate)
        elapsed_times.append(prof.elapsed_seconds)
        throughputs.append(prof.throughput_per_sec)

    stdev = statistics.stdev(elapsed_times) if len(elapsed_times) > 1 else 0.0

    return BenchmarkReport(
        trials=trials,
        mean_seconds=round(statistics.mean(elapsed_times), 6),
        median_seconds=round(statistics.median(elapsed_times), 6),
        stdev_seconds=round(stdev, 6),
        min_seconds=round(min(elapsed_times), 6),
        max_seconds=round(max(elapsed_times), 6),
        mean_throughput=round(statistics.mean(throughputs), 2),
    )
