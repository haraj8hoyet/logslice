"""CLI helpers for the diff subcommand."""

from __future__ import annotations

import argparse
import sys
from typing import List

from logslice.differ import diff_entries, diff_summary, format_diff
from logslice.reader import iter_entries


def add_diff_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the ``diff`` subcommand on *subparsers*."""
    p = subparsers.add_parser(
        "diff",
        help="Compare two log files and show added/removed entries.",
    )
    p.add_argument("left", metavar="FILE_A", help="First (original) log file.")
    p.add_argument("right", metavar="FILE_B", help="Second (modified) log file.")
    p.add_argument(
        "--color",
        action="store_true",
        default=False,
        help="Colorize output (green=added, red=removed).",
    )
    p.add_argument(
        "--summary",
        action="store_true",
        default=False,
        help="Print a summary count instead of individual lines.",
    )
    p.set_defaults(func=_run_diff)


def _run_diff(args: argparse.Namespace) -> int:
    """Execute the diff subcommand; return exit code."""
    try:
        left_entries = list(iter_entries(args.left))
        right_entries = list(iter_entries(args.right))
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    diffs = list(diff_entries(left_entries, right_entries))

    if args.summary:
        counts = diff_summary(diffs)
        print(f"unchanged: {counts['unchanged']}")
        print(f"added:     {counts['added']}")
        print(f"removed:   {counts['removed']}")
    else:
        for line in format_diff(diffs, use_color=args.color):
            print(line)

    has_changes = any(d.kind != "unchanged" for d in diffs)
    return 1 if has_changes else 0
