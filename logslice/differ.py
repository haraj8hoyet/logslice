"""Diff two streams of log entries, reporting added, removed, or changed lines."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Iterator, List, Literal, Tuple

from logslice.parser import LogEntry

DiffKind = Literal["added", "removed", "unchanged"]


@dataclass(frozen=True)
class DiffEntry:
    kind: DiffKind
    entry: LogEntry


def _entry_sig(entry: LogEntry) -> Tuple[str | None, str, str]:
    """Return a comparable signature for a log entry."""
    ts = entry.timestamp.isoformat() if entry.timestamp else None
    return (ts, entry.level or "", entry.message or "")


def diff_entries(
    left: Iterable[LogEntry],
    right: Iterable[LogEntry],
) -> Iterator[DiffEntry]:
    """Yield DiffEntry objects comparing two ordered entry streams.

    Entries present only in *left* are marked ``removed``.
    Entries present only in *right* are marked ``added``.
    Entries whose signature matches in both are marked ``unchanged``.
    """
    left_list: List[LogEntry] = list(left)
    right_list: List[LogEntry] = list(right)

    left_sigs = {_entry_sig(e): e for e in left_list}
    right_sigs = {_entry_sig(e): e for e in right_list}

    seen: set = set()

    for entry in left_list:
        sig = _entry_sig(entry)
        if sig in right_sigs:
            yield DiffEntry(kind="unchanged", entry=entry)
        else:
            yield DiffEntry(kind="removed", entry=entry)
        seen.add(sig)

    for entry in right_list:
        sig = _entry_sig(entry)
        if sig not in seen:
            yield DiffEntry(kind="added", entry=entry)


def diff_summary(diffs: Iterable[DiffEntry]) -> dict:
    """Return a dict with counts for each diff kind."""
    counts: dict = {"added": 0, "removed": 0, "unchanged": 0}
    for d in diffs:
        counts[d.kind] += 1
    return counts


def format_diff(diffs: Iterable[DiffEntry], use_color: bool = False) -> Iterator[str]:
    """Yield human-readable lines for each diff entry."""
    prefix_map: dict = {"added": "+ ", "removed": "- ", "unchanged": "  "}
    color_map: dict = {"added": "\033[32m", "removed": "\033[31m", "unchanged": ""}
    reset = "\033[0m"

    for d in diffs:
        prefix = prefix_map[d.kind]
        line = d.entry.raw or d.entry.message or ""
        if use_color and d.kind != "unchanged":
            yield f"{color_map[d.kind]}{prefix}{line}{reset}"
        else:
            yield f"{prefix}{line}"
