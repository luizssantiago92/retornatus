"""Omission gate and the dependency-bot exemption.

The gate fails when a diff changes code and touches no Change. A configured
bot may pass when every changed file matches the manifest allow-list. That
pass prints a warning. It is not silent.

The author is an argument. Callers pass ``pull_request.user.login`` or
``--pr-author``. This module does not read a title, body, or commit message.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from retornatus.application.assurance.settings import load_project_config
from retornatus.application.governance.diff import changed_paths, git_available
from retornatus.application.governance.globs import glob_match, normalize_repo_path
from retornatus.domain.errors import UsageError

# Historical omission paths from the Action's ``case`` patterns.
# Bash ``*`` matches across slashes, so a nested file under these trees counts.
_CODE_TREES: tuple[str, ...] = ("src/", "tests/", "scripts/", "templates/")
_CODE_FILES: frozenset[str] = frozenset({"pyproject.toml", "uv.lock"})

DEFAULT_BOT_AUTHORS: tuple[str, ...] = ("dependabot[bot]", "renovate[bot]")

# ``**`` matches any directory. A single ``*`` does not cross ``/``.
DEFAULT_BOT_PATHS: tuple[str, ...] = (
    "**/pyproject.toml",
    "**/uv.lock",
    "**/poetry.lock",
    "**/requirements*.txt",
    "**/package.json",
    "**/package-lock.json",
    "**/pnpm-lock.yaml",
    "**/yarn.lock",
    "**/Cargo.toml",
    "**/Cargo.lock",
    "**/go.mod",
    "**/go.sum",
    ".github/workflows/*.yml",
    ".github/workflows/*.yaml",
)

_CHANGE_IN_DIFF = ".retornatus/changes/"
_TABLE = "[governance.omission.bot_exemption]"


@dataclass(frozen=True)
class BotExemptionSettings:
    """``[governance.omission.bot_exemption]``. Missing keys keep the defaults."""

    enabled: bool
    authors: tuple[str, ...]
    paths: tuple[str, ...]


@dataclass(frozen=True)
class ExemptionDecision:
    """Whether this author and file list qualify. ``notice`` is empty when not."""

    exempted: bool
    notice: str


@dataclass(frozen=True)
class OmissionReport:
    passed: bool
    messages: tuple[str, ...]


def path_counts_as_code(path: str) -> bool:
    """True when ``path`` is one of the paths that trigger the omission gate.

    The trees match the Action's old ``src/*`` patterns, including nested
    files. ``src2/app.py`` does not count, because the prefix includes ``/``.
    """
    norm = normalize_repo_path(path)
    if norm in _CODE_FILES:
        return True
    return any(norm.startswith(prefix) for prefix in _CODE_TREES)


def load_bot_exemption(root: Path) -> BotExemptionSettings:
    """Read the exemption table. A missing table is enabled with the defaults."""
    governance = load_project_config(root).get("governance")
    if governance is None:
        return _defaults()
    if not isinstance(governance, dict):
        raise UsageError("Invalid [governance]: expected a table")
    omission = governance.get("omission")
    if omission is None:
        return _defaults()
    if not isinstance(omission, dict):
        raise UsageError("Invalid [governance.omission]: expected a table")
    table = omission.get("bot_exemption")
    if table is None:
        return _defaults()
    if not isinstance(table, dict):
        raise UsageError(f"Invalid {_TABLE}: expected a table")
    return BotExemptionSettings(
        enabled=_enabled(table),
        authors=_strings(table, "authors", DEFAULT_BOT_AUTHORS),
        paths=_strings(table, "paths", DEFAULT_BOT_PATHS),
    )


def normalize_author(author: str) -> str:
    """Strip surrounding spaces. Control characters are rejected before that strip.

    A trailing newline must not turn ``dependabot[bot]\\n`` into a listed login.
    """
    if any(ord(char) < 32 or char == "\x7f" for char in author):
        raise UsageError("--pr-author contains control characters")
    text = author.strip()
    if len(text) > 256:
        raise UsageError("--pr-author is too long")
    return text


def evaluate_bot_exemption(
    changed_files: Sequence[str],
    *,
    author: str,
    settings: BotExemptionSettings,
) -> ExemptionDecision:
    """Exempt only an enabled, listed author when every file matches.

    An empty file list is not an exemption. Author comparison is exact after
    stripping surrounding whitespace.
    """
    login = normalize_author(author)
    if not settings.enabled or not login or login not in settings.authors or not changed_files:
        return ExemptionDecision(False, "")
    if not all(_path_allowed(path, settings.paths) for path in changed_files):
        return ExemptionDecision(False, "")
    return ExemptionDecision(True, _notice(login, changed_files))


def assess_omission(
    root: Path,
    *,
    base: str | None = None,
    staged: bool = False,
    author: str = "",
    declared_change: str | None = None,
) -> OmissionReport:
    """Decide the omission gate for one diff.

    A supplied Change id skips the gate, matching a workflow that already
    named the Change. Otherwise a code path with no Change in the diff fails,
    unless :func:`evaluate_bot_exemption` applies.
    """
    login = normalize_author(author)
    if (declared_change or "").strip():
        return OmissionReport(True, ("Omission skipped: a Change id was supplied.",))
    if not git_available(root):
        return OmissionReport(False, ("Not a git work tree; omission gate needs a diff",))
    paths = changed_paths(root, base=base, staged=staged)
    if _touched_change_ids(paths):
        return OmissionReport(True, ("Omission not triggered: a Change is in the diff.",))
    if not any(path_counts_as_code(path) for path in paths):
        return OmissionReport(True, ("Omission not triggered.",))
    decision = evaluate_bot_exemption(
        paths,
        author=login,
        settings=load_bot_exemption(root),
    )
    if decision.exempted:
        return OmissionReport(True, (f"WARN {decision.notice}",))
    return OmissionReport(False, ("Code changed but no .retornatus Change was touched.",))


def _defaults() -> BotExemptionSettings:
    return BotExemptionSettings(True, DEFAULT_BOT_AUTHORS, DEFAULT_BOT_PATHS)


def _enabled(table: dict[str, Any]) -> bool:
    if "enabled" not in table:
        return True
    value = table["enabled"]
    if isinstance(value, bool):
        return value
    raise UsageError(f"Invalid {_TABLE} enabled: expected true or false")


def _strings(table: dict[str, Any], key: str, default: tuple[str, ...]) -> tuple[str, ...]:
    if key not in table:
        return default
    value = table[key]
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise UsageError(f"Invalid {_TABLE} {key}: expected a list of strings")
    cleaned = tuple(item.strip() for item in value)
    if any(not item for item in cleaned):
        raise UsageError(f"Invalid {_TABLE} {key}: entries must not be empty")
    if any(any(ord(char) < 32 or char == "\x7f" for char in item) for item in cleaned):
        raise UsageError(f"Invalid {_TABLE} {key}: entries must not contain control characters")
    return cleaned


def _path_allowed(path: str, patterns: Sequence[str]) -> bool:
    return any(glob_match(path, pattern) for pattern in patterns)


def _touched_change_ids(paths: Sequence[str]) -> list[str]:
    seen: list[str] = []
    prefix = _CHANGE_IN_DIFF
    for path in paths:
        norm = normalize_repo_path(path)
        if not norm.startswith(prefix):
            continue
        rest = norm[len(prefix) :]
        change_id, sep, _tail = rest.partition("/")
        if not sep or not _change_id(change_id) or change_id in seen:
            continue
        seen.append(change_id)
    return seen


def _change_id(value: str) -> bool:
    if not value.startswith("C-") or len(value) < 3:
        return False
    return value[2:].isdigit()


def _notice(author: str, paths: Sequence[str]) -> str:
    shown = [_safe(normalize_repo_path(path)) for path in paths[:12]]
    listing = ", ".join(shown)
    extra = len(paths) - len(shown)
    if extra > 0:
        listing = f"{listing}, +{extra} more"
    return (
        f"Dependency-bot pull request from {_safe(author)} exempted from the omission gate: "
        f"every changed file matches the dependency manifest allow-list ({listing})."
    )


def _safe(text: str) -> str:
    """One annotation-safe line. Encoded newlines cannot split a workflow command."""
    return " ".join(text.replace("%", "").split())
