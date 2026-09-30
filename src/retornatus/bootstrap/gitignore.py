"""Idempotent `.gitignore` rules and tracked private-key warnings.

`retornatus init` appends one delimited block. A later run sees the begin
marker and leaves the file alone, including any lines the user wrote.
"""

from __future__ import annotations

import subprocess
from collections.abc import Sequence
from pathlib import Path

GITIGNORE_BEGIN = "# retornatus-gitignore:begin"
GITIGNORE_END = "# retornatus-gitignore:end"

# Negations stay after the patterns they undo. Public keys are ``.pub`` files;
# ``*.pem`` must not be what makes them un-committable.
GITIGNORE_RULES: tuple[str, ...] = (
    GITIGNORE_BEGIN,
    "# Local index and cache. Canonical Retornatus artifacts stay tracked.",
    ".retornatus/index/",
    ".retornatus/runtime/",
    "# Private keys and local env files. Public keys stay tracked.",
    "*.pem",
    "*.key",
    ".env",
    ".env.*",
    "!.env.example",
    "!.retornatus/keys/*.pub",
    GITIGNORE_END,
)

_PRIVATE_KEY_SUFFIXES = (".pem", ".key")


def gitignore_block(newline: str = "\n") -> str:
    """Return the delimited block, including a trailing newline."""
    return newline.join(GITIGNORE_RULES) + newline


def _block_newline(raw: bytes) -> bytes:
    """Keep a CRLF-only file CRLF. New files and LF files stay LF."""
    if raw and b"\r\n" in raw and b"\n" not in raw.replace(b"\r\n", b""):
        return b"\r\n"
    return b"\n"


def ensure_retornatus_gitignore(root: Path) -> bool:
    """Append the Retornatus block when its begin marker is absent.

    Returns True when the file was created or changed. Bytes outside the
    block are kept, including CRLF. A second call does not append another copy.

    The file is read as bytes. ``Path.read_text`` would turn ``\\r\\n`` into
    ``\\n`` and rewrite the user's lines.
    """
    path = root / ".gitignore"
    if path.is_file():
        raw = path.read_bytes()
    elif path.exists():
        return False
    else:
        raw = b""
    normalized = raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    if GITIGNORE_BEGIN.encode("ascii") in normalized:
        return False
    newline = _block_newline(raw)
    block = gitignore_block(newline.decode("ascii")).encode("ascii")
    if not raw:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(block)
        return True
    prefix = raw
    if not prefix.endswith((b"\n", b"\r")):
        prefix += newline
    if not prefix.endswith(newline + newline):
        prefix += newline
    path.write_bytes(prefix + block)
    return True


def tracked_private_key_files(root: Path) -> list[str]:
    """Repo-relative paths of tracked ``*.pem`` and ``*.key`` files.

    Empty when git is unavailable or ``root`` is not a work tree. The match
    is case-insensitive so ``Secret.PEM`` is included. ``.pub`` files are not.
    """
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z"],
            check=False,
            capture_output=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    if completed.returncode != 0:
        return []
    text = completed.stdout.decode("utf-8", errors="surrogateescape")
    found: list[str] = []
    for name in text.split("\0"):
        if not name:
            continue
        normalized = name.replace("\\", "/")
        if normalized.lower().endswith(_PRIVATE_KEY_SUFFIXES):
            found.append(normalized)
    return found


def tracked_private_key_warnings(paths: Sequence[str]) -> list[str]:
    """Warnings for private-key paths that git already tracks."""
    if not paths:
        return []
    lines = [f"warning: private key file is tracked by git: {path}" for path in paths]
    lines.append(
        "warning: remove tracked *.pem and *.key files from git. "
        "Signing keys are written outside the repository."
    )
    return lines
