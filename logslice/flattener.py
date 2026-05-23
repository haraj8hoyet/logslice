"""Flatten nested extra fields in LogEntry into dot-notation keys."""

from typing import Any, Dict, Iterator
from logslice.parser import LogEntry


def _flatten_dict(
    obj: Any,
    prefix: str = "",
    sep: str = ".",
) -> Dict[str, Any]:
    """Recursively flatten a nested dict into dot-notation keys."""
    items: Dict[str, Any] = {}
    if isinstance(obj, dict):
        for key, value in obj.items():
            full_key = f"{prefix}{sep}{key}" if prefix else key
            if isinstance(value, dict):
                items.update(_flatten_dict(value, prefix=full_key, sep=sep))
            else:
                items[full_key] = value
    else:
        items[prefix] = obj
    return items


def flatten_entry(entry: LogEntry, sep: str = ".") -> LogEntry:
    """Return a new LogEntry with nested extra fields flattened.

    Only the ``extra`` dict is affected; top-level fields (timestamp,
    level, message, raw) are preserved unchanged.

    Args:
        entry: The source log entry.
        sep:   Separator used when joining nested key names.

    Returns:
        A new LogEntry whose ``extra`` contains only flat keys.
    """
    flat_extra = _flatten_dict(entry.extra, sep=sep)
    return LogEntry(
        timestamp=entry.timestamp,
        level=entry.level,
        message=entry.message,
        extra=flat_extra,
        raw=entry.raw,
    )


def flatten_entries(
    entries: Iterator[LogEntry],
    sep: str = ".",
) -> Iterator[LogEntry]:
    """Lazily flatten every entry in *entries*.

    Args:
        entries: Iterable of LogEntry objects.
        sep:     Separator forwarded to :func:`flatten_entry`.

    Yields:
        Flattened LogEntry objects.
    """
    for entry in entries:
        yield flatten_entry(entry, sep=sep)
