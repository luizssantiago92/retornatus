"""Install git hooks that call Retornatus gates.

Hooks are POSIX ``sh`` scripts so Git for Windows (which runs hooks with its
bundled shell) and worktrees both work. The hooks directory comes from
``git rev-parse --git-path hooks``, which honors ``core.hooksPath`` and
linked worktrees.

The commit-msg hook reads the message path from ``$1``. It does not open
``.git/COMMIT_EDITMSG`` on its own — that file is not the message during
pre-commit, which is a bug in the predecessor project.
"""

from __future__ import annotations

import os
import stat
import sys
from dataclasses import dataclass
from pathlib import Path

from retornatus.application.governance.diff import run_git
from retornatus.domain.errors import UsageError
from retornatus.infrastructure.persistence.repository import FileRepository

BEGIN = "# retornatus:begin"
END = "# retornatus:end"

_PRE_COMMIT = "pre-commit"
_COMMIT_MSG = "commit-msg"


@dataclass(frozen=True)
class HookStatus:
    hooks_dir: Path
    pre_commit: str
    commit_msg: str

    def render(self) -> str:
        return "\n".join(
            [
                f"hooks_path: {self.hooks_dir}",
                f"pre-commit: {self.pre_commit}",
                f"commit-msg: {self.commit_msg}",
            ]
        )


def resolve_hooks_dir(root: Path) -> Path:
    """Directory git will actually execute hooks from."""
    try:
        completed = run_git(root, ["rev-parse", "--git-path", "hooks"])
    except OSError as exc:
        raise UsageError(f"git is not available: {exc}") from exc
    if completed.returncode != 0:
        detail = completed.stderr.strip() or "not a git repository"
        raise UsageError(detail)
    raw = completed.stdout.strip()
    if not raw:
        raise UsageError("git rev-parse --git-path hooks returned an empty path")
    path = Path(raw)
    if not path.is_absolute():
        path = (root.resolve() / path).resolve()
    return path


def install_hooks(root: Path) -> HookStatus:
    """Install or refresh pre-commit and commit-msg, preserving user hooks."""
    hooks_dir = resolve_hooks_dir(root)
    hooks_dir.mkdir(parents=True, exist_ok=True)
    invocation = _python_invocation()
    _install_one(hooks_dir / _PRE_COMMIT, _pre_commit_body(invocation))
    _install_one(hooks_dir / _COMMIT_MSG, _commit_msg_body(invocation))
    return status(root)


def remove_hooks(root: Path) -> HookStatus:
    """Drop the Retornatus block. User hook text outside the markers stays."""
    hooks_dir = resolve_hooks_dir(root)
    for name in (_PRE_COMMIT, _COMMIT_MSG):
        path = hooks_dir / name
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if BEGIN not in text or END not in text:
            continue
        kept = _strip_block(text)
        if _trivial(kept):
            path.unlink()
        else:
            path.write_text(kept if kept.endswith("\n") else kept + "\n", encoding="utf-8", newline="\n")
    return status(root)


def status(root: Path) -> HookStatus:
    hooks_dir = resolve_hooks_dir(root)
    return HookStatus(
        hooks_dir=hooks_dir,
        pre_commit=_hook_state(hooks_dir / _PRE_COMMIT),
        commit_msg=_hook_state(hooks_dir / _COMMIT_MSG),
    )


def active_change_ids(root: Path) -> list[str]:
    """Changes whose Contract is active. Empty when the project has none."""
    repo = FileRepository(root)
    found: list[str] = []
    try:
        change_ids = repo.list_change_ids()
    except (OSError, FileNotFoundError):
        return []
    for change_id in change_ids:
        try:
            contract, _ = repo.load_contract(change_id)
        except (OSError, FileNotFoundError, ValueError):
            continue
        if contract.active:
            found.append(change_id)
    return found


def check_commit_message(message_file: Path) -> list[str]:
    """Validate the commit message stored at ``message_file`` (hook ``$1``).

    Comment lines (``#``) and blank lines do not count. The file is the only
    input — callers must not substitute ``COMMIT_EDITMSG``.
    """
    if not message_file.is_file():
        raise UsageError(f"Commit message file not found: {message_file}")
    text = message_file.read_text(encoding="utf-8", errors="replace")
    body = [line.strip() for line in text.splitlines() if line.strip() and not line.strip().startswith("#")]
    if not body:
        return ["Commit message is empty"]
    return []


def _python_invocation() -> str:
    import retornatus

    package_parent = Path(retornatus.__file__).resolve().parent.parent
    exe = _sh_quote(sys.executable)
    src = _sh_quote(str(package_parent))
    return f"PYTHONPATH={src}${{PYTHONPATH:+:$PYTHONPATH}} {exe} -m retornatus"


def _pre_commit_body(invocation: str) -> str:
    return "\n".join(
        [
            "_retornatus_root=$(git rev-parse --show-toplevel) || exit 1",
            f'_retornatus() {{ {invocation} "$@"; }}',
            '_retornatus gate suppressions --staged --path "$_retornatus_root" || exit $?',
            '_retornatus hooks scope --path "$_retornatus_root" || exit $?',
        ]
    )


def _commit_msg_body(invocation: str) -> str:
    return "\n".join(
        [
            'if [ -z "${1:-}" ]; then',
            '  echo "retornatus: commit-msg requires the message path as its first argument" >&2',
            "  exit 1",
            "fi",
            "_retornatus_root=$(git rev-parse --show-toplevel) || exit 1",
            f'_retornatus() {{ {invocation} "$@"; }}',
            '_retornatus hooks commit-msg --message-file "$1" --path "$_retornatus_root" || exit $?',
        ]
    )


def _install_one(path: Path, body: str) -> None:
    existing = path.read_text(encoding="utf-8", errors="replace") if path.is_file() else None
    text = _merge(existing, body)
    path.write_text(text, encoding="utf-8", newline="\n")
    _make_executable(path)


def _merge(existing: str | None, body: str) -> str:
    block = f"{BEGIN}\n{body.strip()}\n{END}"
    if not existing or not existing.strip():
        return f"#!/bin/sh\n{block}\n"
    text = existing.replace("\r\n", "\n")
    if BEGIN in text and END in text:
        pre, rest = text.split(BEGIN, 1)
        _discarded, post = rest.split(END, 1)
        return _join(pre.strip("\n"), block, post.strip("\n"))
    shebang = ""
    rest = text.strip("\n")
    if rest.startswith("#!"):
        first, _, remainder = rest.partition("\n")
        shebang = first
        rest = remainder.strip("\n")
    return _join(shebang, block, rest)


def _join(*parts: str) -> str:
    kept = [part for part in parts if part.strip()]
    return "\n\n".join(kept) + "\n"


def _strip_block(text: str) -> str:
    normalized = text.replace("\r\n", "\n")
    pre, rest = normalized.split(BEGIN, 1)
    _discarded, post = rest.split(END, 1)
    combined = (pre.rstrip() + "\n\n" + post.lstrip()).strip("\n")
    if not combined:
        return ""
    return combined + "\n"


def _trivial(text: str) -> bool:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return True
    return len(lines) == 1 and lines[0].startswith("#!")


def _hook_state(path: Path) -> str:
    if not path.is_file():
        return "absent"
    text = path.read_text(encoding="utf-8", errors="replace")
    if BEGIN in text and END in text:
        return "installed"
    return "foreign"


def _sh_quote(value: str) -> str:
    return "'" + value.replace("'", "'\\''") + "'"


def _make_executable(path: Path) -> None:
    try:
        mode = path.stat().st_mode
        path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    except OSError:
        # Git for Windows executes hooks via the shebang even without a Unix mode bit.
        os.chmod(path, stat.S_IREAD | stat.S_IWRITE | stat.S_IEXEC)
