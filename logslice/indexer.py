"""Build and query a simple byte-offset index over a log file for fast seeking."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from logslice.parser import parse_timestamp


@dataclass
class LogIndex:
    """Maps parsed timestamps (as isoformat strings) to byte offsets in a file."""

    offsets: List[int] = field(default_factory=list)
    timestamps: List[Optional[str]] = field(default_factory=list)
    path: str = ""

    def __len__(self) -> int:
        return len(self.offsets)


def build_index(path: str, encoding: str = "utf-8") -> LogIndex:
    """Scan *path* line-by-line and record the byte offset of every line.

    Lines whose timestamp cannot be parsed are still indexed with
    ``timestamp=None`` so that the offset list stays aligned with lines.

    Raises:
        FileNotFoundError: If *path* does not exist.
        PermissionError: If the file cannot be opened for reading.
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Log file not found: {path!r}")
    index = LogIndex(path=path)
    with open(path, "rb") as fh:
        while True:
            offset = fh.tell()
            raw = fh.readline()
            if not raw:
                break
            line = raw.decode(encoding, errors="replace").rstrip("\n")
            ts = parse_timestamp(line)
            index.offsets.append(offset)
            index.timestamps.append(ts.isoformat() if ts else None)
    return index


def seek_to_offset(path: str, offset: int, encoding: str = "utf-8"):
    """Return an open text file handle seeked to *offset*."""
    fh = open(path, "r", encoding=encoding, errors="replace")  # noqa: WPS515
    fh.seek(offset)
    return fh


def find_offsets_in_range(
    index: LogIndex,
    start: Optional[str] = None,
    end: Optional[str] = None,
) -> List[int]:
    """Return byte offsets whose timestamps fall within [start, end].

    *start* and *end* should be ISO-format strings (or ``None`` for open range).
    Lines with ``None`` timestamps are always included.
    """
    result: List[int] = []
    for offset, ts in zip(index.offsets, index.timestamps):
        if ts is None:
            result.append(offset)
            continue
        if start and ts < start:
            continue
        if end and ts > end:
            continue
        result.append(offset)
    return result
