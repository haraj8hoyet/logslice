"""CLI helper: --profile flag support for logslice commands."""

from __future__ import annotations

import sys
from typing import Iterable

from logslice.parser import LogEntry
from logslice.profiler import ProfileResult, profile_iter


def run_with_profile(
    source: Iterable[LogEntry],
    predicate=None,
    *,
    enabled: bool = True,
    output_file=None,
) -> list[LogEntry]:
    """Run *source* through profile_iter and optionally print a summary.

    Parameters
    ----------
    source:
        Iterable of LogEntry objects to consume.
    predicate:
        Optional filter function applied to each entry.
    enabled:
        When False, entries are collected without profiling output.
    output_file:
        File-like object to write the profile summary to (default: stderr).

    Returns
    -------
    list[LogEntry]
        Matched entries after applying *predicate*.
    """
    if output_file is None:
        output_file = sys.stderr

    entries, prof = profile_iter(source, predicate=predicate)

    if enabled:
        output_file.write("[profile] " + prof.summary() + "\n")

    return entries


def format_profile_result(prof: ProfileResult) -> str:
    """Return a one-line human-readable profile summary."""
    return prof.summary()


def add_profile_argument(parser) -> None:
    """Add --profile flag to an argparse.ArgumentParser."""
    parser.add_argument(
        "--profile",
        action="store_true",
        default=False,
        help="Print profiling information (throughput, elapsed time) to stderr.",
    )
