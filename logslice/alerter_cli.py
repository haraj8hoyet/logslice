"""CLI helpers for the alerter: subparser registration and runner."""

from __future__ import annotations

import argparse
import sys
from typing import List

from logslice.alerter import (
    AlertRule,
    evaluate_rules,
    format_alert_matches,
    make_level_alert,
    make_pattern_alert,
)
from logslice.reader import iter_entries


def add_alert_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the *alert* subcommand on *subparsers*."""
    p = subparsers.add_parser(
        "alert",
        help="Scan a log file and fire alerts on matching entries.",
    )
    p.add_argument("file", help="Log file to scan.")
    p.add_argument(
        "--level",
        dest="levels",
        metavar="LEVEL",
        action="append",
        default=[],
        help="Alert on this log level (repeatable).",
    )
    p.add_argument(
        "--pattern",
        dest="patterns",
        metavar="REGEX",
        action="append",
        default=[],
        help="Alert when message matches this regex (repeatable).",
    )
    p.add_argument(
        "--stop-on-first",
        action="store_true",
        default=False,
        help="Stop after the first alert fires.",
    )
    p.set_defaults(func=_run_alert)


def _build_rules(ns: argparse.Namespace) -> List[AlertRule]:
    rules: List[AlertRule] = []
    for level in ns.levels:
        rules.append(make_level_alert(f"level:{level}", level))
    for i, pat in enumerate(ns.patterns):
        rules.append(make_pattern_alert(f"pattern:{i}", pat))
    return rules


def _run_alert(ns: argparse.Namespace) -> int:
    """Execute the alert subcommand; return exit code."""
    rules = _build_rules(ns)
    if not rules:
        print("No alert rules specified. Use --level or --pattern.", file=sys.stderr)
        return 2

    entries = list(iter_entries(ns.file))
    matches = evaluate_rules(entries, rules, stop_on_first=ns.stop_on_first)
    print(format_alert_matches(matches))
    return 1 if matches else 0
