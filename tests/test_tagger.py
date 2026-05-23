"""Tests for logslice.tagger."""

from datetime import datetime
from typing import Any, Dict, Optional

import pytest

from logslice.parser import LogEntry
from logslice.tagger import (
    get_tags,
    make_level_rule,
    make_pattern_rule,
    tag_entries,
    tag_entry,
)


def make_entry(
    message: str = "hello",
    level: Optional[str] = "INFO",
    fields: Optional[Dict[str, Any]] = None,
    timestamp: Optional[datetime] = None,
) -> LogEntry:
    return LogEntry(
        timestamp=timestamp,
        level=level,
        message=message,
        fields=fields or {},
        raw=message,
    )


# ---------------------------------------------------------------------------
# make_level_rule
# ---------------------------------------------------------------------------

def test_make_level_rule_matches_same_level():
    rule = make_level_rule("error-tag", "ERROR")
    entry = make_entry(level="ERROR")
    tag, pred = rule
    assert tag == "error-tag"
    assert pred(entry) is True


def test_make_level_rule_case_insensitive():
    _, pred = make_level_rule("warn-tag", "warn")
    assert pred(make_entry(level="WARN")) is True
    assert pred(make_entry(level="warn")) is True


def test_make_level_rule_no_match_different_level():
    _, pred = make_level_rule("error-tag", "ERROR")
    assert pred(make_entry(level="INFO")) is False


# ---------------------------------------------------------------------------
# make_pattern_rule
# ---------------------------------------------------------------------------

def test_make_pattern_rule_matches_message():
    _, pred = make_pattern_rule("db-tag", r"database")
    assert pred(make_entry(message="database connection failed")) is True


def test_make_pattern_rule_no_match():
    _, pred = make_pattern_rule("db-tag", r"database")
    assert pred(make_entry(message="network timeout")) is False


def test_make_pattern_rule_custom_field():
    _, pred = make_pattern_rule("svc-tag", r"auth", field="service")
    entry = make_entry(fields={"service": "auth-service"})
    assert pred(entry) is True


# ---------------------------------------------------------------------------
# tag_entry
# ---------------------------------------------------------------------------

def test_tag_entry_adds_matching_tag():
    rules = [make_level_rule("is-error", "ERROR")]
    entry = make_entry(level="ERROR")
    result = tag_entry(entry, rules)
    assert "is-error" in get_tags(result)


def test_tag_entry_skips_non_matching_rule():
    rules = [make_level_rule("is-error", "ERROR")]
    entry = make_entry(level="INFO")
    result = tag_entry(entry, rules)
    assert get_tags(result) == []


def test_tag_entry_preserves_existing_tags():
    rules = [make_level_rule("is-error", "ERROR")]
    entry = make_entry(level="ERROR", fields={"tags": "legacy"})
    result = tag_entry(entry, rules)
    tags = get_tags(result)
    assert "legacy" in tags
    assert "is-error" in tags


def test_tag_entry_no_duplicate_tags():
    rules = [make_level_rule("is-error", "ERROR"), make_level_rule("is-error", "ERROR")]
    entry = make_entry(level="ERROR")
    result = tag_entry(entry, rules)
    assert get_tags(result).count("is-error") == 1


def test_tag_entry_original_entry_unchanged():
    rules = [make_level_rule("is-error", "ERROR")]
    entry = make_entry(level="ERROR")
    tag_entry(entry, rules)
    assert "tags" not in entry.fields


# ---------------------------------------------------------------------------
# tag_entries
# ---------------------------------------------------------------------------

def test_tag_entries_lazy_applies_to_all():
    rules = [make_pattern_rule("has-timeout", r"timeout")]
    entries = [
        make_entry(message="connection timeout"),
        make_entry(message="all good"),
        make_entry(message="read timeout"),
    ]
    results = list(tag_entries(entries, rules))
    assert "has-timeout" in get_tags(results[0])
    assert get_tags(results[1]) == []
    assert "has-timeout" in get_tags(results[2])
