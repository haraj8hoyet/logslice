"""Tests for logslice.highlight module."""

import pytest
from logslice.highlight import (
    colorize_level,
    highlight_pattern,
    highlight_line,
    strip_ansi,
    RESET,
    BOLD,
    LEVEL_COLORS,
)


def test_colorize_level_known_level():
    result = colorize_level("ERROR")
    assert "ERROR" in result
    assert LEVEL_COLORS["ERROR"] in result
    assert RESET in result


def test_colorize_level_unknown_returns_plain():
    result = colorize_level("VERBOSE")
    assert result == "VERBOSE"


def test_colorize_level_case_insensitive():
    result = colorize_level("warning")
    assert "WARNING" in result.upper() or "warning" in result
    assert RESET in result


def test_highlight_pattern_basic():
    result = highlight_pattern("hello world", "world")
    assert "world" in result
    assert RESET in result


def test_highlight_pattern_empty_pattern_returns_original():
    text = "no change here"
    result = highlight_pattern(text, "")
    assert result == text


def test_highlight_pattern_case_insensitive():
    result = highlight_pattern("Hello World", "hello")
    assert RESET in result
    assert "Hello" in result


def test_highlight_pattern_no_match_returns_original():
    text = "nothing matches"
    result = highlight_pattern(text, "xyz")
    assert result == text


def test_highlight_line_no_search_no_color():
    line = "2024-01-01 INFO some message"
    result = highlight_line(line, colorize=False)
    assert result == line


def test_highlight_line_with_search():
    line = "2024-01-01 ERROR disk full"
    result = highlight_line(line, search="disk", colorize=True)
    assert "disk" in result
    assert RESET in result


def test_highlight_line_colorize_true_adds_ansi():
    line = "2024-01-01 ERROR something failed"
    result = highlight_line(line, colorize=True)
    assert RESET in result


def test_strip_ansi_removes_codes():
    colored = f"\033[31m\033[1mERROR\033[0m plain text"
    result = strip_ansi(colored)
    assert result == "ERROR plain text"


def test_strip_ansi_plain_text_unchanged():
    text = "plain log line"
    assert strip_ansi(text) == text


def test_highlight_then_strip_round_trip():
    original = "2024-01-01 WARNING low memory"
    highlighted = highlight_line(original, search="memory", colorize=True)
    stripped = strip_ansi(highlighted)
    assert "WARNING" in stripped
    assert "memory" in stripped
    assert "\033" not in stripped
