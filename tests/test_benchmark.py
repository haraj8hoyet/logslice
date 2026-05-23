"""Tests for logslice.benchmark."""

from __future__ import annotations

from datetime import datetime

import pytest

from logslice.parser import LogEntry
from logslice.benchmark import BenchmarkReport, run_benchmark


def make_entry(msg: str = "test", level: str = "INFO") -> LogEntry:
    return LogEntry(
        timestamp=datetime(2024, 6, 1, 0, 0, 0),
        level=level,
        message=msg,
        raw=f"2024-06-01 00:00:00 {level} {msg}",
        extra={},
    )


def _factory(n: int = 20):
    def _make():
        return (make_entry(f"msg{i}") for i in range(n))
    return _make


def test_run_benchmark_returns_report():
    report = run_benchmark(_factory(10), trials=3)
    assert isinstance(report, BenchmarkReport)
    assert report.trials == 3


def test_run_benchmark_mean_positive():
    report = run_benchmark(_factory(5), trials=2)
    assert report.mean_seconds >= 0.0
    assert report.mean_throughput > 0.0


def test_run_benchmark_min_lte_max():
    report = run_benchmark(_factory(10), trials=4)
    assert report.min_seconds <= report.max_seconds


def test_run_benchmark_with_predicate():
    entries = [make_entry(f"m{i}", "ERROR" if i % 2 == 0 else "INFO") for i in range(20)]
    report = run_benchmark(lambda: iter(entries), predicate=lambda e: e.level == "ERROR", trials=3)
    assert report.trials == 3
    assert report.mean_throughput > 0


def test_run_benchmark_invalid_trials_raises():
    with pytest.raises(ValueError, match="trials"):
        run_benchmark(_factory(5), trials=0)


def test_benchmark_report_format_contains_fields():
    report = BenchmarkReport(
        trials=5,
        mean_seconds=0.001234,
        median_seconds=0.001100,
        stdev_seconds=0.000050,
        min_seconds=0.001000,
        max_seconds=0.001500,
        mean_throughput=8100.5,
    )
    text = report.format()
    assert "5" in text
    assert "0.001234" in text
    assert "8100.5" in text


def test_run_benchmark_single_trial_stdev_zero():
    report = run_benchmark(_factory(5), trials=1)
    assert report.stdev_seconds == 0.0
    assert report.min_seconds == report.max_seconds
