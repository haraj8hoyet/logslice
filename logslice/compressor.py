"""Utilities for compressing and decompressing log entry streams."""

import gzip
import io
import json
from typing import Iterable, Iterator, List

from logslice.parser import LogEntry


def _entry_to_dict(entry: LogEntry) -> dict:
    return {
        "timestamp": entry.timestamp.isoformat() if entry.timestamp else None,
        "level": entry.level,
        "message": entry.message,
        "raw": entry.raw,
        "fields": entry.fields,
    }


def _dict_to_entry(d: dict) -> LogEntry:
    from datetime import datetime

    ts = d.get("timestamp")
    parsed_ts = datetime.fromisoformat(ts) if ts else None
    return LogEntry(
        timestamp=parsed_ts,
        level=d.get("level", ""),
        message=d.get("message", ""),
        raw=d.get("raw", ""),
        fields=d.get("fields") or {},
    )


def compress_entries(entries: Iterable[LogEntry]) -> bytes:
    """Serialize and gzip-compress a sequence of LogEntry objects.

    Returns raw compressed bytes suitable for storage or transmission.
    """
    records = [_entry_to_dict(e) for e in entries]
    payload = json.dumps(records, separators=(",", ":")).encode("utf-8")
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb") as gz:
        gz.write(payload)
    return buf.getvalue()


def decompress_entries(data: bytes) -> List[LogEntry]:
    """Decompress gzip bytes and deserialize back into LogEntry objects."""
    buf = io.BytesIO(data)
    with gzip.GzipFile(fileobj=buf, mode="rb") as gz:
        payload = gz.read()
    records = json.loads(payload.decode("utf-8"))
    return [_dict_to_entry(r) for r in records]


def iter_decompressed(data: bytes) -> Iterator[LogEntry]:
    """Yield LogEntry objects from compressed bytes one at a time."""
    for entry in decompress_entries(data):
        yield entry


def compress_to_file(entries: Iterable[LogEntry], path: str) -> int:
    """Write compressed entries to *path*. Returns number of entries written."""
    collected = list(entries)
    data = compress_entries(collected)
    with open(path, "wb") as fh:
        fh.write(data)
    return len(collected)


def decompress_from_file(path: str) -> List[LogEntry]:
    """Read and decompress entries from *path*."""
    with open(path, "rb") as fh:
        data = fh.read()
    return decompress_entries(data)
