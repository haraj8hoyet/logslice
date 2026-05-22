"""Core log entry parser for structured log formats."""

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

# Default pattern: 2024-01-15 12:34:56,789 [LEVEL] logger - message
DEFAULT_LOG_PATTERN = re.compile(
    r"(?P<timestamp>\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}[,.]?\d*)"
    r"\s+\[?(?P<level>[A-Z]+)\]?\s+"
    r"(?P<logger>[\w\.]+)\s+-\s+"
    r"(?P<message>.+)"
)

TIMESTAMP_FORMATS = [
    "%Y-%m-%dT%H:%M:%S,%f",
    "%Y-%m-%dT%H:%M:%S.%f",
    "%Y-%m-%d %H:%M:%S,%f",
    "%Y-%m-%d %H:%M:%S.%f",
    "%Y-%m-%d %H:%M:%S",
]


@dataclass
class LogEntry:
    """Represents a single parsed log entry."""
    raw: str
    timestamp: Optional[datetime] = None
    level: Optional[str] = None
    logger: Optional[str] = None
    message: Optional[str] = None
    extra: dict = field(default_factory=dict)

    def is_valid(self) -> bool:
        return self.timestamp is not None


def parse_timestamp(ts_str: str) -> Optional[datetime]:
    """Try to parse a timestamp string using known formats."""
    for fmt in TIMESTAMP_FORMATS:
        try:
            return datetime.strptime(ts_str, fmt)
        except ValueError:
            continue
    return None


def parse_line(line: str, pattern: re.Pattern = DEFAULT_LOG_PATTERN) -> LogEntry:
    """Parse a single log line into a LogEntry."""
    line = line.rstrip("\n")
    match = pattern.match(line)
    if not match:
        return LogEntry(raw=line)

    groups = match.groupdict()
    timestamp = parse_timestamp(groups.get("timestamp", ""))
    return LogEntry(
        raw=line,
        timestamp=timestamp,
        level=groups.get("level"),
        logger=groups.get("logger"),
        message=groups.get("message"),
    )
