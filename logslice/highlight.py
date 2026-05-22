"""Terminal color highlighting for log output."""

import re
from typing import Optional

# ANSI escape codes
RESET = "\033[0m"
BOLD = "\033[1m"

LEVEL_COLORS = {
    "DEBUG": "\033[36m",    # Cyan
    "INFO": "\033[32m",     # Green
    "WARNING": "\033[33m",  # Yellow
    "WARN": "\033[33m",     # Yellow
    "ERROR": "\033[31m",    # Red
    "CRITICAL": "\033[35m", # Magenta
    "FATAL": "\033[35m",    # Magenta
}


def colorize_level(level: str) -> str:
    """Wrap a log level string in its corresponding ANSI color."""
    color = LEVEL_COLORS.get(level.upper(), "")
    if not color:
        return level
    return f"{color}{BOLD}{level}{RESET}"


def highlight_pattern(text: str, pattern: str, color: str = "\033[43m") -> str:
    """Highlight all occurrences of pattern in text with a background color."""
    if not pattern:
        return text
    try:
        highlighted = re.sub(
            f"({re.escape(pattern)})",
            f"{color}\\1{RESET}",
            text,
            flags=re.IGNORECASE,
        )
        return highlighted
    except re.error:
        return text


def highlight_line(line: str, search: Optional[str] = None, colorize: bool = True) -> str:
    """Apply level colorization and optional pattern highlighting to a log line."""
    if not colorize:
        return line

    result = line

    # Colorize known log levels in-line
    for level, color in LEVEL_COLORS.items():
        pattern = re.compile(rf"\b({re.escape(level)})\b")
        result = pattern.sub(f"{color}{BOLD}\\1{RESET}", result)
        break  # Only replace the first matched level to avoid double-coloring

    if search:
        result = highlight_pattern(result, search)

    return result


def strip_ansi(text: str) -> str:
    """Remove all ANSI escape sequences from a string."""
    ansi_escape = re.compile(r"\033\[[0-9;]*m")
    return ansi_escape.sub("", text)
