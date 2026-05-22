"""Simple disk-backed index cache using JSON so rebuilds are avoided."""

from __future__ import annotations

import json
import os
from typing import Optional

from logslice.indexer import LogIndex

_CACHE_SUFFIX = ".logslice-index.json"


def _cache_path(log_path: str) -> str:
    return log_path + _CACHE_SUFFIX


def _mtime(path: str) -> float:
    return os.path.getmtime(path)


def save_index(index: LogIndex) -> str:
    """Serialize *index* to a sidecar JSON file next to the log.

    Returns the path of the written cache file.
    """
    cache = _cache_path(index.path)
    payload = {
        "path": index.path,
        "mtime": _mtime(index.path),
        "offsets": index.offsets,
        "timestamps": index.timestamps,
    }
    with open(cache, "w", encoding="utf-8") as fh:
        json.dump(payload, fh)
    return cache


def load_index(log_path: str) -> Optional[LogIndex]:
    """Load a cached index for *log_path* if it exists and is still valid.

    Returns ``None`` when the cache is missing or stale.
    """
    cache = _cache_path(log_path)
    if not os.path.exists(cache):
        return None
    try:
        with open(cache, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
    except (json.JSONDecodeError, OSError):
        return None

    if payload.get("path") != log_path:
        return None
    if payload.get("mtime") != _mtime(log_path):
        return None

    return LogIndex(
        path=log_path,
        offsets=payload["offsets"],
        timestamps=payload["timestamps"],
    )


def get_or_build_index(log_path: str, encoding: str = "utf-8") -> LogIndex:
    """Return a cached index or build (and cache) a fresh one."""
    from logslice.indexer import build_index  # local import avoids cycles

    index = load_index(log_path)
    if index is not None:
        return index
    index = build_index(log_path, encoding=encoding)
    try:
        save_index(index)
    except OSError:
        pass  # cache write failure is non-fatal
    return index
