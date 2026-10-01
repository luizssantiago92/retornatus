"""Git diffs used by scope, suppression, and structured policy.

Paths are repo-relative and use forward slashes. When ``root`` is a
subdirectory of a larger work tree, names outside ``root`` are dropped.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from retornatus.domain.errors import UsageError


@dataclass(frozen=True)
class AddedLine:
    """One added diff line (a ``+`` line that is not a file header)."""

    path: str
    line_number: int
    text: str


def run_git(root: Path, args: list[str], *, timeout: float = 30) -> subprocess.CompletedProcess[str]:
    """Run ``git -C root`` and capture text. Does not raise on non-zero status."""
    return subprocess.run(
        ["git", "-C", str(root), *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )


def git_available(root: Path) -> bool:
    """True when ``root`` is inside a work tree with a resolvable HEAD."""
    try:
        completed = run_git(root, ["rev-parse", "--is-inside-work-tree"])
    except (OSError, subprocess.TimeoutExpired):
        return False
    return completed.returncode == 0 and completed.stdout.strip() == "true"


def git_toplevel(root: Path) -> Path | None:
    try:
        completed = run_git(root, ["rev-parse", "--show-toplevel"])
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    text = completed.stdout.strip()
    return Path(text) if text else None


def require_ref(root: Path, ref: str) -> None:
    """Raise :class:`UsageError` when ``ref`` does not resolve."""
    if not ref.strip():
        raise UsageError("Git ref must not be empty")
    try:
        completed = run_git(root, ["rev-parse", "--verify", "--quiet", ref])
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise UsageError(f"git failed while resolving {ref}: {exc}") from exc
    if completed.returncode != 0:
        raise UsageError(f"Unknown git ref: {ref}")


def changed_paths(
    root: Path,
    *,
    base: str | None = None,
    staged: bool = False,
) -> list[str]:
    """Names changed against ``base...HEAD``, the index, or the work tree.

    ``base`` uses ``git diff --name-only <base>...HEAD`` (merge-base).
    ``staged`` uses the index (``--cached``).
    With neither, the result is staged + unstaged tracked changes plus
    untracked files that are not ignored.
    """
    if base and staged:
        raise UsageError("Pass only one of --base and --staged")
    if not git_available(root):
        return []
    if base:
        require_ref(root, base)
        raw = _name_only(root, ["diff", "--name-only", f"{base}...HEAD"])
    elif staged:
        raw = _name_only(root, ["diff", "--name-only", "--cached"])
    else:
        raw = _name_only(root, ["diff", "--name-only", "HEAD"])
        raw.extend(_name_only(root, ["ls-files", "--others", "--exclude-standard"]))
    return _unique(_filter_to_root(root, raw))


def added_lines(
    root: Path,
    *,
    base: str | None = None,
    staged: bool = False,
) -> list[AddedLine]:
    """Added lines (``+``, not ``+++``) from the same diff selection as names.

    With neither ``base`` nor ``staged``, untracked files that are not ignored
    are included too. Each of their lines is an added line, the same way a
    new file appears in a diff. Names come from
    ``git ls-files --others --exclude-standard``, so gitignored paths stay out.
    ``--base`` and ``--staged`` stay limited to that range and the index.
    """
    if base and staged:
        raise UsageError("Pass only one of --base and --staged")
    if not git_available(root):
        return []
    args = ["diff", "-U0", "--no-color", "--no-ext-diff"]
    if base:
        require_ref(root, base)
        args.append(f"{base}...HEAD")
    elif staged:
        args.extend(["--cached"])
    else:
        args.append("HEAD")
    try:
        completed = run_git(root, args)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise UsageError(f"git diff failed: {exc}") from exc
    if completed.returncode != 0:
        detail = completed.stderr.strip() or "git diff failed"
        raise UsageError(detail)
    lines = _parse_added(completed.stdout)
    if not base and not staged:
        lines.extend(_untracked_added_lines(root))
    allowed = set(_filter_to_root(root, [item.path for item in lines]))
    return [item for item in lines if item.path in allowed]


# Git treats a blob as binary when a NUL appears in the first 8 KiB and then
# emits no added text lines. Match that so an untracked binary is not scanned.
_BINARY_SNIFF_BYTES = 8000


def _untracked_added_lines(root: Path) -> list[AddedLine]:
    """Every text line of each untracked, non-ignored file, as an added line."""
    added: list[AddedLine] = []
    for name in _name_only(root, ["ls-files", "--others", "--exclude-standard"]):
        added.extend(_untracked_file_lines(root, name))
    return added


def _untracked_file_lines(root: Path, name: str) -> list[AddedLine]:
    path = root / name
    try:
        if not path.is_file():
            return []
        raw = path.read_bytes()
    except OSError:
        return []
    if b"\0" in raw[:_BINARY_SNIFF_BYTES]:
        return []
    text = raw.decode("utf-8", errors="replace")
    return [
        AddedLine(path=name, line_number=number, text=line)
        for number, line in enumerate(text.splitlines(), start=1)
    ]


def _name_only(root: Path, args: list[str]) -> list[str]:
    try:
        completed = run_git(root, args)
    except (OSError, subprocess.TimeoutExpired):
        return []
    if completed.returncode != 0:
        return []
    names: list[str] = []
    for line in completed.stdout.splitlines():
        text = line.strip().replace("\\", "/")
        if text:
            names.append(text)
    return names


def _filter_to_root(root: Path, names: list[str]) -> list[str]:
    """Keep paths that live under ``root`` when ``root`` is not the toplevel."""
    toplevel = git_toplevel(root)
    if toplevel is None:
        return [_norm(name) for name in names if name.strip()]
    root_res = root.resolve()
    top = toplevel.resolve()
    try:
        prefix = root_res.relative_to(top).as_posix()
    except ValueError:
        return []
    if prefix == ".":
        prefix = ""
    kept: list[str] = []
    for name in names:
        norm = _norm(name)
        if not prefix:
            kept.append(norm)
            continue
        if norm == prefix:
            continue
        head = prefix + "/"
        if norm.startswith(head):
            kept.append(norm[len(head) :])
    return kept


def _norm(path: str) -> str:
    text = path.replace("\\", "/").strip()
    if text.startswith("./"):
        text = text[2:]
    return text


def _unique(names: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for name in names:
        if not name or name in seen:
            continue
        seen.add(name)
        ordered.append(name)
    return ordered


def _parse_added(diff_text: str) -> list[AddedLine]:
    added: list[AddedLine] = []
    path = ""
    new_line = 0
    for raw in diff_text.splitlines():
        if raw.startswith("diff --git "):
            path = _path_from_diff_header(raw)
            new_line = 0
            continue
        if raw.startswith("+++ "):
            renamed = _path_from_plus_header(raw)
            if renamed:
                path = renamed
            continue
        if raw.startswith("@@"):
            new_line = _new_start(raw)
            continue
        if raw.startswith("+"):
            if not path:
                continue
            added.append(AddedLine(path=path, line_number=max(new_line, 1), text=raw[1:]))
            new_line += 1
            continue
        if raw.startswith("-") or raw.startswith("\\"):
            continue
        # Context line in a non-zero context diff (we request -U0, but be safe).
        if path and new_line:
            new_line += 1
    return added


def _path_from_diff_header(line: str) -> str:
    # diff --git a/foo b/foo  — prefer the b/ side
    marker = " b/"
    index = line.rfind(marker)
    if index == -1:
        return ""
    return _norm(line[index + len(marker) :])


def _path_from_plus_header(line: str) -> str:
    # +++ b/foo
    text = line[4:].strip()
    if text == "/dev/null":
        return ""
    if text.startswith("b/"):
        text = text[2:]
    return _norm(text)


def _new_start(hunk: str) -> int:
    # @@ -l,s +l,s @@
    plus = hunk.find("+")
    if plus == -1:
        return 1
    rest = hunk[plus + 1 :]
    digits = []
    for char in rest:
        if char.isdigit():
            digits.append(char)
        else:
            break
    if not digits:
        return 1
    return int("".join(digits))
