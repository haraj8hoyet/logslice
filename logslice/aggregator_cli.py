"""CLI helpers for the aggregate sub-command."""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from logslice.aggregator import aggregate_by_field, format_aggregate, top_groups
from logslice.reader import iter_entries


def add_aggregate_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the *aggregate* sub-command on *subparsers*."""
    p = subparsers.add_parser(
        "aggregate",
        help="Count log entries grouped by a field value.",
    )
    p.add_argument("file", help="Log file to read.")
    p.add_argument(
        "--field",
        default="level",
        help="Field to group by (default: level).",
    )
    p.add_argument(
        "--top",
        type=int,
        default=None,
        metavar="N",
        help="Show only the top N groups by count.",
    )
    p.add_argument(
        "--max-samples",
        type=int,
        default=3,
        dest="max_samples",
        help="Number of sample messages to show per group (default: 3).",
    )
    p.set_defaults(func=_run_aggregate)


def _run_aggregate(args: argparse.Namespace) -> int:
    """Execute the aggregate command; return an exit code."""
    try:
        entries = list(iter_entries(args.file))
    except OSError as exc:
        print(f"logslice aggregate: error reading {args.file!r}: {exc}", file=sys.stderr)
        return 1

    if args.max_samples < 0:
        print("logslice aggregate: --max-samples must be >= 0", file=sys.stderr)
        return 2

    groups = aggregate_by_field(entries, args.field, max_samples=args.max_samples)

    if not groups:
        print("(no entries)")
        return 0

    ranked = top_groups(groups, n=args.top)
    for group in ranked:
        sample_str = "; ".join(group.samples) if group.samples else ""
        key_display = group.key or "(empty)"
        print(f"{key_display:20s}  count={group.count}  samples=[{sample_str}]")

    return 0
