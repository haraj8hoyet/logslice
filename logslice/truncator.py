"""Truncate or wrap long log message fields for display."""

from typing import Optional
from logslice.parser import LogEntry

_DEFAULT_MAX_LEN = 200
_ELLIPSIS = "..."


def truncate_message(message: str, max_len: int = _DEFAULT_MAX_LEN) -> str:
    """Truncate a message string to at most max_len characters.

    If the message exceeds max_len, it is cut and an ellipsis appended.
    """
    if max_len < len(_ELLIPSIS):
        raise ValueError(f"max_len must be at least {len(_ELLIPSIS)}")
    if len(message) <= max_len:
        return message
    return message[: max_len - len(_ELLIPSIS)] + _ELLIPSIS


def wrap_message(message: str, width: int = 80) -> list[str]:
    """Wrap a message into lines of at most *width* characters.

    Words are not split; if a single word exceeds *width* it occupies its own
    line.
    """
    if width <= 0:
        raise ValueError("width must be positive")
    words = message.split(" ")
    lines: list[str] = []
    current = ""
    for word in words:
        if not current:
            current = word
        elif len(current) + 1 + len(word) <= width:
            current += " " + word
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def truncate_entry(
    entry: LogEntry,
    max_len: int = _DEFAULT_MAX_LEN,
    field: str = "message",
) -> LogEntry:
    """Return a new LogEntry with the specified *field* truncated.

    Only fields present in LogEntry.fields are supported via *field*.
    The special value ``"message"`` truncates ``entry.message``.
    """
    if field == "message":
        new_message = truncate_message(entry.message, max_len)
        return LogEntry(
            raw=entry.raw,
            timestamp=entry.timestamp,
            level=entry.level,
            message=new_message,
            fields=dict(entry.fields),
        )
    if field in entry.fields:
        new_fields = dict(entry.fields)
        new_fields[field] = truncate_message(str(new_fields[field]), max_len)
        return LogEntry(
            raw=entry.raw,
            timestamp=entry.timestamp,
            level=entry.level,
            message=entry.message,
            fields=new_fields,
        )
    return entry
