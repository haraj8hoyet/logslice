"""Output formatters for log entries."""

import json
from typing import List
from logslice.parser import LogEntry


SUPPORTED_FORMATS = ("text", "json", "csv")


def format_text(entry: LogEntry) -> str:
    """Format a log entry as a plain text line."""
    parts = []
    if entry.timestamp:
        parts.append(entry.timestamp.isoformat())
    if entry.level:
        parts.append(f"[{entry.level}]")
    if entry.message:
        parts.append(entry.message)
    return " ".join(parts) if parts else entry.raw


def format_json(entry: LogEntry) -> str:
    """Format a log entry as a JSON string."""
    data = {
        "timestamp": entry.timestamp.isoformat() if entry.timestamp else None,
        "level": entry.level,
        "message": entry.message,
        "raw": entry.raw,
    }
    if entry.extra:
        data["extra"] = entry.extra
    return json.dumps(data)


def format_csv(entry: LogEntry) -> str:
    """Format a log entry as a CSV row (timestamp,level,message)."""
    def escape(value: str) -> str:
        if value and (',' in value or '"' in value or '\n' in value):
            return '"' + value.replace('"', '""') + '"'
        return value or ""

    ts = entry.timestamp.isoformat() if entry.timestamp else ""
    level = escape(entry.level or "")
    message = escape(entry.message or "")
    return f"{ts},{level},{message}"


def format_entries(entries: List[LogEntry], fmt: str = "text") -> List[str]:
    """Format a list of log entries using the specified format.

    Args:
        entries: List of LogEntry objects to format.
        fmt: One of 'text', 'json', or 'csv'.

    Returns:
        List of formatted strings.

    Raises:
        ValueError: If an unsupported format is specified.
    """
    if fmt not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported format '{fmt}'. Choose from: {SUPPORTED_FORMATS}")

    formatter = {"text": format_text, "json": format_json, "csv": format_csv}[fmt]
    return [formatter(entry) for entry in entries]


def csv_header() -> str:
    """Return the CSV header row."""
    return "timestamp,level,message"
