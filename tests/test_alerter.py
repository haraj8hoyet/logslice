"""Tests for logslice.alerter."""

from datetime import datetime

import pytest

from logslice.parser import LogEntry
from logslice.alerter import (
    AlertRule,
    AlertMatch,
    make_level_alert,
    make_pattern_alert,
    evaluate_rules,
    format_alert_matches,
)


def make_entry(
    message: str = "hello",
    level: str | None = "INFO",
    timestamp: datetime | None = None,
) -> LogEntry:
    return LogEntry(
        raw=f"{level} {message}",
        timestamp=timestamp,
        level=level,
        message=message,
        fields={},
    )


# --- make_level_alert ---

def test_make_level_alert_fires_on_matching_level():
    rule = make_level_alert("err-alert", "ERROR")
    entry = make_entry(level="ERROR", message="boom")
    assert rule.predicate(entry) is True


def test_make_level_alert_case_insensitive():
    rule = make_level_alert("warn-alert", "warn")
    entry = make_entry(level="WARN")
    assert rule.predicate(entry) is True


def test_make_level_alert_no_fire_different_level():
    rule = make_level_alert("err-alert", "ERROR")
    entry = make_entry(level="INFO")
    assert rule.predicate(entry) is False


# --- make_pattern_alert ---

def test_make_pattern_alert_fires_on_match():
    rule = make_pattern_alert("oom", r"out of memory")
    entry = make_entry(message="process out of memory killed")
    assert rule.predicate(entry) is True


def test_make_pattern_alert_no_fire_no_match():
    rule = make_pattern_alert("oom", r"out of memory")
    entry = make_entry(message="everything is fine")
    assert rule.predicate(entry) is False


# --- evaluate_rules ---

def test_evaluate_rules_returns_all_matches():
    rules = [
        make_level_alert("err", "ERROR"),
        make_pattern_alert("crash", "crash"),
    ]
    entries = [
        make_entry(level="ERROR", message="crash detected"),
        make_entry(level="INFO", message="all good"),
        make_entry(level="INFO", message="crash again"),
    ]
    matches = evaluate_rules(entries, rules)
    # first entry matches both rules; third matches pattern rule
    assert len(matches) == 3


def test_evaluate_rules_stop_on_first():
    rules = [make_level_alert("err", "ERROR")]
    entries = [make_entry(level="ERROR"), make_entry(level="ERROR")]
    matches = evaluate_rules(entries, rules, stop_on_first=True)
    assert len(matches) == 1


def test_evaluate_rules_no_matches_returns_empty():
    rules = [make_level_alert("err", "ERROR")]
    entries = [make_entry(level="INFO"), make_entry(level="DEBUG")]
    assert evaluate_rules(entries, rules) == []


# --- format_alert_matches ---

def test_format_alert_matches_empty_returns_no_alerts():
    assert format_alert_matches([]) == "No alerts fired."


def test_format_alert_matches_contains_rule_name():
    rule = make_level_alert("my-rule", "ERROR")
    entry = make_entry(level="ERROR", message="oops")
    match = AlertMatch(rule=rule, entry=entry)
    result = format_alert_matches([match])
    assert "my-rule" in result
    assert "oops" in result
