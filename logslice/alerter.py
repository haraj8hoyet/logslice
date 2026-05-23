"""Alert rules that fire when log entries match defined conditions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable, List, Optional

from logslice.parser import LogEntry


@dataclass
class AlertRule:
    """A named rule with a predicate and optional description."""

    name: str
    predicate: Callable[[LogEntry], bool]
    description: str = ""


@dataclass
class AlertMatch:
    """A single rule-entry match produced during evaluation."""

    rule: AlertRule
    entry: LogEntry

    def __str__(self) -> str:
        ts = entry.timestamp.isoformat() if (entry := self.entry).timestamp else "no-ts"
        return f"[ALERT:{self.rule.name}] {ts} {entry.level or '-'} {entry.message}"


def make_level_alert(name: str, level: str, description: str = "") -> AlertRule:
    """Create an alert rule that fires when entry.level matches *level* (case-insensitive)."""
    upper = level.upper()
    return AlertRule(
        name=name,
        predicate=lambda e: (e.level or "").upper() == upper,
        description=description or f"Fires on level={level}",
    )


def make_pattern_alert(name: str, pattern: str, description: str = "") -> AlertRule:
    """Create an alert rule that fires when *pattern* appears in entry.message."""
    import re

    rx = re.compile(pattern)
    return AlertRule(
        name=name,
        predicate=lambda e: bool(rx.search(e.message)),
        description=description or f"Fires on pattern={pattern!r}",
    )


def evaluate_rules(
    entries: Iterable[LogEntry],
    rules: List[AlertRule],
    *,
    stop_on_first: bool = False,
) -> List[AlertMatch]:
    """Evaluate *rules* against every entry; return all matches.

    If *stop_on_first* is True, return after the first match across all rules.
    """
    matches: List[AlertMatch] = []
    for entry in entries:
        for rule in rules:
            if rule.predicate(entry):
                matches.append(AlertMatch(rule=rule, entry=entry))
                if stop_on_first:
                    return matches
    return matches


def format_alert_matches(matches: Iterable[AlertMatch]) -> str:
    """Return a human-readable summary of alert matches."""
    lines = [str(m) for m in matches]
    if not lines:
        return "No alerts fired."
    return "\n".join(lines)
