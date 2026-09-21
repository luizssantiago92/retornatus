"""Optimistic concurrency via content hash (PRD §57)."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path


class ConcurrencyConflict(Exception):
    """Raised when the on-disk artifact changed since it was read."""


@dataclass(frozen=True)
class ArtifactRevision:
    """Snapshot fingerprint used for compare-and-swap writes."""

    path: Path
    content_hash: str | None  # None when the file did not exist at read time

    @property
    def exists(self) -> bool:
        return self.content_hash is not None


def hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_revision(path: Path) -> tuple[bytes | None, ArtifactRevision]:
    if not path.is_file():
        return None, ArtifactRevision(path=path, content_hash=None)
    data = path.read_bytes()
    return data, ArtifactRevision(path=path, content_hash=hash_bytes(data))


def assert_unchanged(expected: ArtifactRevision) -> None:
    """Verify the file still matches the expected revision."""
    current_data, current = read_revision(expected.path)
    del current_data
    if current.content_hash != expected.content_hash:
        raise ConcurrencyConflict(
            f"Concurrent modification detected for {expected.path}"
        )
