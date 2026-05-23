"""Tests for logslice.validator."""

from datetime import datetime
from logslice.parser import LogEntry
from logslice.validator import (
    ValidationResult,
    validate_entry,
    validate_entries,
    filter_valid,
    KNOWN_LEVELS,
)


def make_entry(
    message: str = "something happened",
    level: str = "INFO",
    timestamp: datetime | None = datetime(2024, 6, 1, 10, 0, 0),
    fields: dict | None = None,
) -> LogEntry:
    return LogEntry(
        raw=message,
        timestamp=timestamp,
        level=level,
        message=message,
        fields=fields or {},
    )


# --- validate_entry ---

def test_validate_entry_all_good():
    result = validate_entry(make_entry())
    assert result.valid
    assert result.errors == []


def test_validate_entry_missing_timestamp_when_required():
    entry = make_entry(timestamp=None)
    result = validate_entry(entry, require_timestamp=True)
    assert not result.valid
    assert any("timestamp" in e for e in result.errors)


def test_validate_entry_timestamp_present_when_required():
    result = validate_entry(make_entry(), require_timestamp=True)
    assert result.valid


def test_validate_entry_missing_level_when_required():
    entry = make_entry(level="")
    result = validate_entry(entry, require_level=True)
    assert not result.valid
    assert any("level" in e for e in result.errors)


def test_validate_entry_unknown_level_flagged():
    entry = make_entry(level="VERBOSE")
    result = validate_entry(entry)
    assert not result.valid
    assert any("unknown level" in e for e in result.errors)


def test_validate_entry_custom_known_levels():
    entry = make_entry(level="VERBOSE")
    result = validate_entry(entry, known_levels={"VERBOSE", "INFO"})
    assert result.valid


def test_validate_entry_message_too_short():
    entry = make_entry(message="")
    result = validate_entry(entry, min_message_len=1)
    assert not result.valid
    assert any("short" in e for e in result.errors)


def test_validate_entry_multiple_errors_collected():
    entry = make_entry(message="", timestamp=None, level="")
    result = validate_entry(
        entry,
        require_timestamp=True,
        require_level=True,
        min_message_len=1,
    )
    assert len(result.errors) >= 2


def test_validate_entry_known_levels_contains_common_levels():
    """Ensure KNOWN_LEVELS includes the most commonly used log levels."""
    for level in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
        assert level in KNOWN_LEVELS, f"Expected {level!r} in KNOWN_LEVELS"


# --- validate_entries ---

def test_validate_entries_yields_one_per_entry():
    entries = [make_entry(), make_entry(level="BAD"), make_entry()]
    results = list(validate_entries(entries))
    assert len(results) == 3


def test_validate_entries_result_types():
    results = list(validate_entries([make_entry()]))
    assert isinstance(results[0], ValidationResult)


# --- filter_valid ---

def test_filter_valid_removes_invalid():
    entries = [
        make_entry(),
        make_entry(timestamp=None),
        make_entry(),
    ]
    valid = list(filter_valid(entries, require_timestamp=True))
    assert len(valid) == 2


def test_filter_valid_empty_input():
    assert list(filter_valid([], require_timestamp=True)) == []
