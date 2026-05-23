"""Chunk a log file on disk by byte-offset ranges.

Useful for parallel processing: callers can divide a large file into
roughly equal byte-range slices and process each slice independently.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Iterable, List


@dataclass(frozen=True)
class FileChunk:
    """A byte-range slice of a file."""

    path: str
    start: int  # inclusive byte offset
    end: int    # exclusive byte offset (or -1 for EOF)

    def __len__(self) -> int:  # pragma: no cover
        if self.end == -1:
            return max(0, os.path.getsize(self.path) - self.start)
        return max(0, self.end - self.start)


def compute_chunks(path: str, num_chunks: int) -> List[FileChunk]:
    """Divide *path* into *num_chunks* roughly equal :class:`FileChunk` objects.

    Each chunk boundary is snapped forward to the next newline so that no
    log line is split across two chunks.

    Args:
        path: Path to the log file.
        num_chunks: Desired number of chunks.  Clamped to the number of
            lines if the file is very small.  Must be >= 1.

    Returns:
        List of :class:`FileChunk` instances covering the whole file.

    Raises:
        ValueError: If *num_chunks* < 1.
        FileNotFoundError: If *path* does not exist.
    """
    if num_chunks < 1:
        raise ValueError(f"num_chunks must be >= 1, got {num_chunks}")

    file_size = os.path.getsize(path)
    if file_size == 0:
        return [FileChunk(path=path, start=0, end=-1)]

    approx_size = max(1, file_size // num_chunks)
    chunks: List[FileChunk] = []
    start = 0

    with open(path, "rb") as fh:
        while start < file_size:
            target = start + approx_size
            if target >= file_size:
                chunks.append(FileChunk(path=path, start=start, end=-1))
                break
            # Snap to next newline
            fh.seek(target)
            fh.readline()  # consume partial line
            end = fh.tell()
            chunks.append(FileChunk(path=path, start=start, end=end))
            start = end

    return chunks


def iter_chunk_lines(chunk: FileChunk) -> Iterable[str]:
    """Yield decoded text lines belonging to *chunk*.

    Args:
        chunk: A :class:`FileChunk` describing the byte range to read.

    Yields:
        Stripped text lines within the chunk's byte range.
    """
    end = chunk.end
    with open(chunk.path, "rb") as fh:
        fh.seek(chunk.start)
        while True:
            pos = fh.tell()
            if end != -1 and pos >= end:
                break
            raw = fh.readline()
            if not raw:
                break
            yield raw.decode("utf-8", errors="replace").rstrip("\n")
