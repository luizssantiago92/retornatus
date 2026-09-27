"""Run a command and capture an attributable execution record.

The command is spawned directly (``shell=False``). Combined stdout and stderr
are hashed and tailed; callers persist the full bytes beside the Evidence JSON.
"""

from __future__ import annotations

import hashlib
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from retornatus.application.assurance.subject_state import (
    current_git_head,
    worktree_is_dirty,
)

DEFAULT_COMMAND_TIMEOUT_SECONDS = 120.0
OUTPUT_TAIL_MAX_CHARS = 4096


@dataclass(frozen=True)
class CommandCapture:
    """Result of one harness-executed command."""

    argv: list[str]
    exit_code: int | None
    started_at: datetime
    ended_at: datetime
    duration_ms: int
    output_sha256: str
    output_tail: str
    output_bytes: bytes
    timed_out: bool
    git_commit: str | None
    worktree_dirty: bool | None


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _tail(text: str, *, note: str = "") -> str:
    if not note:
        if len(text) <= OUTPUT_TAIL_MAX_CHARS:
            return text
        return text[-OUTPUT_TAIL_MAX_CHARS:]
    room = OUTPUT_TAIL_MAX_CHARS - len(note)
    if room < 0:
        return note[-OUTPUT_TAIL_MAX_CHARS:]
    body = text if len(text) <= room else text[-room:]
    return body + note


def capture_command(
    root: Path,
    argv: list[str],
    *,
    timeout_seconds: float = DEFAULT_COMMAND_TIMEOUT_SECONDS,
) -> CommandCapture:
    """Execute ``argv`` in ``root`` and capture output, timing, and git snapshot.

    Git HEAD and dirty state are taken *before* the command so the record
    describes the tree the command ran against. Non-git directories yield
    ``git_commit=None`` and ``worktree_dirty=None``.

    A timeout or a failure to start the process is still a capture: ``exit_code``
    is None and, for timeouts, ``timed_out`` is True. Callers must not treat
    those as passing.
    """
    if not argv or any(not isinstance(part, str) for part in argv):
        raise ValueError("command must be a non-empty argv list of strings")
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")

    root = root.resolve()
    git_commit = current_git_head(root)
    dirty = worktree_is_dirty(root) if git_commit else None
    started = _utc_now()
    timed_out = False
    exit_code: int | None
    try:
        completed = subprocess.run(
            list(argv),
            cwd=root,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout_seconds,
            check=False,
            shell=False,
        )
        output = completed.stdout or b""
        exit_code = int(completed.returncode)
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        raw = exc.stdout or b""
        output = raw.encode("utf-8", errors="replace") if isinstance(raw, str) else raw
        exit_code = None
    except OSError as exc:
        output = f"[retornatus] failed to start command: {exc}\n".encode("utf-8")
        exit_code = None
    ended = _utc_now()
    duration_ms = max(0, int((ended - started).total_seconds() * 1000))
    text = output.decode("utf-8", errors="replace")
    note = ""
    if timed_out:
        note = f"\n[retornatus] timed out after {timeout_seconds:g}s"
    elif exit_code is None:
        note = "\n[retornatus] command did not exit (startup failure)"
    return CommandCapture(
        argv=list(argv),
        exit_code=exit_code,
        started_at=started,
        ended_at=ended,
        duration_ms=duration_ms,
        output_sha256=hashlib.sha256(output).hexdigest(),
        output_tail=_tail(text, note=note),
        output_bytes=output,
        timed_out=timed_out,
        git_commit=git_commit,
        worktree_dirty=dirty,
    )
