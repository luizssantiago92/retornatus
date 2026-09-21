"""Subject-state helpers — derive Evidence freshness from repo state when possible.

Minimal mechanism: prefer ``commit:<sha>`` when git is available.
No universal hashing infrastructure.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from retornatus.domain.models import Evidence


COMMIT_PREFIX = "commit:"


def format_commit_state(sha: str) -> str:
    sha = sha.strip()
    if sha.startswith(COMMIT_PREFIX):
        return sha
    return f"{COMMIT_PREFIX}{sha}"


def parse_commit_state(subject_state: str | None) -> str | None:
    if not subject_state:
        return None
    if subject_state.startswith(COMMIT_PREFIX):
        return subject_state[len(COMMIT_PREFIX) :].strip() or None
    return None


def current_git_head(root: Path) -> str | None:
    """Return HEAD sha when ``root`` is inside a git work tree; else None."""
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    sha = completed.stdout.strip()
    return sha or None


def capture_subject_state(
    root: Path,
    *,
    explicit: str | None = None,
    use_git: bool = True,
) -> str | None:
    """
    Resolve subject_state for new Evidence.

    Preference: explicit → git HEAD as commit:<sha> → None.
    """
    if explicit:
        return explicit
    if use_git:
        head = current_git_head(root)
        if head:
            return format_commit_state(head)
    return None


def derive_current_subject_states(
    root: Path,
    evidence: list[Evidence],
) -> dict[str, str]:
    """
    Build current_subject_states map for Assurance freshness checks.

    For Evidence recorded as commit:<sha>, current state is commit:<HEAD>.
    Subjects without commit-based Evidence are omitted (freshness unknown → keep).
    """
    head = current_git_head(root)
    if not head:
        return {}
    current = format_commit_state(head)
    states: dict[str, str] = {}
    for ev in evidence:
        if parse_commit_state(ev.subject_state):
            states[ev.subject] = current
    return states
