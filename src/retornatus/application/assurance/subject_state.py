"""Subject-state helpers — derive Evidence freshness from repo state when possible.

Minimal mechanism:
- ``commit:<sha>`` when git is available
- Prefer last commit touching a file subject when the subject is a repo path
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
    # Allow commit:<sha> or commit:<sha>|review:...
    core = subject_state.split("|", 1)[0].strip()
    if core.startswith(COMMIT_PREFIX):
        return core[len(COMMIT_PREFIX) :].strip() or None
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


def _normalize_repo_path(root: Path, subject: str) -> Path | None:
    """Return absolute path if subject looks like a file/dir under root."""
    cleaned = subject.strip().lstrip("./")
    if not cleaned or cleaned.startswith("/") or "://" in cleaned:
        # Absolute FS paths outside repo or URLs/endpoints are not path subjects
        if cleaned.startswith("/") and not (root / cleaned.lstrip("/")).exists():
            # endpoint-like /health
            return None
        if cleaned.startswith("/"):
            candidate = Path(cleaned)
            try:
                candidate.relative_to(root.resolve())
            except ValueError:
                return None
            return candidate if candidate.exists() else None
    candidate = (root / cleaned).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        return None
    if candidate.exists():
        return candidate
    return None


def git_commit_for_path(root: Path, rel_or_abs: Path) -> str | None:
    """Last commit that touched a path; falls back to None if untracked/unavailable."""
    root = root.resolve()
    try:
        rel = rel_or_abs.resolve().relative_to(root)
    except ValueError:
        return None
    try:
        completed = subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "log",
                "-1",
                "--format=%H",
                "--",
                str(rel),
            ],
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


def resolve_subject_commit(root: Path, subject: str) -> str | None:
    """
    Resolve the commit that currently establishes ``subject``.

    File/dir subjects → last commit touching that path.
    Otherwise → HEAD (repo-wide observation).
    """
    path = _normalize_repo_path(root, subject)
    if path is not None:
        return git_commit_for_path(root, path) or current_git_head(root)
    return current_git_head(root)


def capture_subject_state(
    root: Path,
    *,
    explicit: str | None = None,
    use_git: bool = True,
    subject: str | None = None,
) -> str | None:
    """
    Resolve subject_state for new Evidence.

    Preference: explicit → path-aware commit:<sha> → HEAD commit:<sha> → None.
    """
    if explicit:
        return explicit
    if use_git:
        if subject:
            sha = resolve_subject_commit(root, subject)
        else:
            sha = current_git_head(root)
        if sha:
            return format_commit_state(sha)
    return None


def derive_current_subject_states(
    root: Path,
    evidence: list[Evidence],
) -> dict[str, str]:
    """
    Build current_subject_states map for Assurance freshness checks.

    For Evidence recorded as commit:<sha>:
    - file/dir subjects → compare against last commit touching that path
    - other subjects → compare against HEAD
    """
    if not current_git_head(root):
        return {}
    states: dict[str, str] = {}
    for ev in evidence:
        if not parse_commit_state(ev.subject_state):
            continue
        sha = resolve_subject_commit(root, ev.subject)
        if sha:
            states[ev.subject] = format_commit_state(sha)
    return states
