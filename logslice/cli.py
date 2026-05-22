"""Command-line interface for logslice."""

import argparse
import sys
from datetime import datetime
from typing import Optional

from logslice.reader import iter_entries
from logslice.filter import apply_filters
from logslice.output import write_entries


def parse_datetime(value: str) -> Optional[datetime]:
    """Parse a datetime string from CLI argument."""
    formats = [
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise argparse.ArgumentTypeError(
        f"Cannot parse datetime: '{value}'. "
        "Expected formats: YYYY-MM-DDTHH:MM:SS, YYYY-MM-DD HH:MM:SS, YYYY-MM-DD"
    )


def build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser."""
    parser = argparse.ArgumentParser(
        prog="logslice",
        description="Fast log file parser — extract and filter structured log entries.",
    )
    parser.add_argument("file", nargs="?", default="-",
                        help="Log file to read (default: stdin)")
    parser.add_argument("--start", type=parse_datetime, metavar="DATETIME",
                        help="Include entries at or after this timestamp")
    parser.add_argument("--end", type=parse_datetime, metavar="DATETIME",
                        help="Include entries at or before this timestamp")
    parser.add_argument("--level", metavar="LEVEL",
                        help="Filter by log level (e.g. ERROR, WARN)")
    parser.add_argument("--pattern", metavar="REGEX",
                        help="Filter by regex pattern in message field")
    parser.add_argument("--format", dest="fmt", default="text",
                        choices=["text", "json", "csv"],
                        help="Output format (default: text)")
    parser.add_argument("--no-header", action="store_true",
                        help="Suppress CSV header row")
    parser.add_argument("--count", action="store_true",
                        help="Print only the count of matched entries")
    return parser


def main(argv=None) -> int:
    """Entry point for the logslice CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)

    source = args.file
    entries = iter_entries(source)
    filtered = apply_filters(
        entries,
        start=args.start,
        end=args.end,
        level=args.level,
        pattern=args.pattern,
    )

    if args.count:
        total = sum(1 for _ in filtered)
        print(total)
        return 0

    write_entries(
        filtered,
        fmt=args.fmt,
        stream=sys.stdout,
        csv_header=not args.no_header,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
