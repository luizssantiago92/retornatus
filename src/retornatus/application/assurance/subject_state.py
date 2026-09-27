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


def worktree_is_dirty(root: Path) -> bool | None:
    """Whether ``git status --porcelain`` reports changes.

    Returns None when git is unavailable or ``root`` is not a work tree.
    Untracked files count as dirty. A non-git directory is not an error.
    """
    if current_git_head(root) is None:
        return None
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), "status", "--porcelain"],
            check=False,
            capture_output=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    return bool(completed.stdout.strip())


# Recording Evidence writes under these prefixes. They must not, by themselves,
# make a required check look stale at the moment verify reads it back.
_HARNESS_DIRTY_PREFIXES = (
    ".retornatus/changes/",
    ".retornatus/index/",
    ".retornatus/runtime/",
)


def git_toplevel(root: Path) -> Path | None:
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    text = completed.stdout.strip()
    return Path(text) if text else None


def substantive_dirty_paths(root: Path) -> list[str] | None:
    """Uncommitted paths that are not harness bookkeeping.

    ``None`` when git is unavailable. Evidence JSON just written by
    ``evidence run`` / ``verify --run-checks`` is ignored so the act of
    recording does not invalidate the run. Source edits are not ignored.
    """
    if current_git_head(root) is None:
        return None
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), "status", "--porcelain=v1", "-uall", "-z"],
            check=False,
            capture_output=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    raw_paths = _porcelain_z_paths(completed.stdout)
    toplevel = git_toplevel(root)
    locals_ = _paths_under_root(root, toplevel, raw_paths)
    dirty: list[str] = []
    for rel in locals_:
        if _harness_bookkeeping(rel):
            continue
        dirty.append(rel)
    return dirty


def substantive_worktree_clean(root: Path) -> bool | None:
    """True when the only uncommitted paths are harness bookkeeping.

    ``None`` outside git. ``False`` when source (or any other non-bookkeeping
    path) is modified, staged, or untracked.
    """
    paths = substantive_dirty_paths(root)
    if paths is None:
        return None
    return not paths


def subject_repo_relative(root: Path, subject: str) -> str | None:
    """Repo-relative path for a file/dir subject, else None.

    Endpoint-like subjects (``/health``) are not paths unless that file exists
    under ``root``. Deleted tracked files still count.
    """
    text = subject.strip().replace("\\", "/")
    if not text or "://" in text:
        return None
    root_res = root.resolve()
    if text.startswith("/"):
        candidate = (root_res / text.lstrip("/")).resolve()
        try:
            rel = candidate.relative_to(root_res)
        except ValueError:
            return None
        if not candidate.exists():
            return None
        return rel.as_posix()
    if text.startswith("./"):
        text = text[2:]
    if not text:
        return None
    candidate = (root_res / text).resolve()
    try:
        rel = candidate.relative_to(root_res)
    except ValueError:
        return None
    rel_posix = rel.as_posix()
    if candidate.exists() or _git_knows_path(root, rel_posix):
        return rel_posix
    return None


def path_has_uncommitted_changes(root: Path, rel: str) -> bool:
    """True when ``git status`` shows staged, unstaged, or untracked changes."""
    if current_git_head(root) is None:
        return False
    try:
        completed = subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "status",
                "--porcelain=v1",
                "-uall",
                "--",
                rel,
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    if completed.returncode != 0:
        return False
    return bool(completed.stdout.strip())


def subjects_with_uncommitted_changes(root: Path, subjects: list[str]) -> set[str]:
    """Subjects that are repo paths with uncommitted or untracked edits."""
    if current_git_head(root) is None:
        return set()
    dirty: set[str] = set()
    seen: set[str] = set()
    for subject in subjects:
        if subject in seen:
            continue
        seen.add(subject)
        rel = subject_repo_relative(root, subject)
        if rel is None:
            continue
        if path_has_uncommitted_changes(root, rel):
            dirty.add(subject)
    return dirty


def _harness_bookkeeping(rel: str) -> bool:
    norm = rel.replace("\\", "/")
    while norm.startswith("./"):
        norm = norm[2:]
    return any(norm.startswith(prefix) for prefix in _HARNESS_DIRTY_PREFIXES)


def _porcelain_z_paths(blob: bytes) -> list[str]:
    """Parse ``git status --porcelain=v1 -z`` path names (renames yield both)."""
    if not blob:
        return []
    parts = blob.split(b"\0")
    paths: list[str] = []
    index = 0
    while index < len(parts):
        entry = parts[index]
        if not entry:
            index += 1
            continue
        # XY + space + path. Rename/copy: next record is the new path.
        if len(entry) < 3:
            index += 1
            continue
        path = entry[3:].decode("utf-8", errors="replace").replace("\\", "/")
        paths.append(path)
        status = entry[:2]
        if b"R" in status or b"C" in status:
            index += 1
            if index < len(parts) and parts[index]:
                paths.append(parts[index].decode("utf-8", errors="replace").replace("\\", "/"))
        index += 1
    return paths


def _paths_under_root(root: Path, toplevel: Path | None, paths: list[str]) -> list[str]:
    if toplevel is None:
        return paths
    root_res = root.resolve()
    top = toplevel.resolve()
    try:
        prefix = root_res.relative_to(top).as_posix()
    except ValueError:
        return []
    if prefix in {"", "."}:
        return paths
    head = prefix + "/"
    local: list[str] = []
    for path in paths:
        norm = path.replace("\\", "/")
        if norm.startswith(head):
            local.append(norm[len(head) :])
    return local


def _git_knows_path(root: Path, rel: str) -> bool:
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), "ls-files", "--", rel],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return completed.returncode == 0 and bool(completed.stdout.strip())


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
