"""CLI helpers for the replay subcommand."""

import argparse
import sys
from typing import List

from logslice.reader import iter_entries
from logslice.replayer import replay_entries
from logslice.formatter import format_entries


def add_replay_subparser(subparsers: argparse._SubParsersAction) -> None:
    """Register the 'replay' subcommand on *subparsers*."""
    p = subparsers.add_parser(
        "replay",
        help="Replay a log file with timing delays proportional to original timestamps.",
    )
    p.add_argument("file", help="Log file to replay.")
    p.add_argument(
        "--speed",
        type=float,
        default=1.0,
        help="Playback speed multiplier (default: 1.0).",
    )
    p.add_argument(
        "--max-delay",
        type=float,
        default=5.0,
        dest="max_delay",
        help="Maximum sleep between entries in seconds (default: 5.0).",
    )
    p.add_argument(
        "--format",
        choices=["text", "json", "csv"],
        default="text",
        dest="fmt",
        help="Output format (default: text).",
    )
    p.set_defaults(func=_run_replay)


def _run_replay(args: argparse.Namespace) -> int:
    """Execute the replay subcommand; returns an exit code."""
    try:
        source = iter_entries(args.file)
        replayed = replay_entries(
            source,
            speed=args.speed,
            max_delay=args.max_delay,
        )
        for line in format_entries(replayed, fmt=args.fmt):
            print(line)
        return 0
    except (ValueError, OSError) as exc:
        print(f"replay error: {exc}", file=sys.stderr)
        return 1
