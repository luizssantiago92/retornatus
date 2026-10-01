"""Scan added diff lines for suppression and skip markers."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from retornatus.application.assurance.settings import load_project_config
from retornatus.application.governance.diff import added_lines, git_available
from retornatus.application.governance.globs import glob_match
from retornatus.domain.errors import UsageError

# Documentation names markers inside code. Those mentions are not suppressions.
_MARKDOWN_SUFFIXES = frozenset({".md", ".markdown", ".mdx", ".mdc"})
_FENCE_OPEN = re.compile(r"^( {0,3})(`{3,}|~{3,})")

# Markers are split in source so this file's own lines do not contain them.
_DEFAULT_PATTERNS: tuple[tuple[str, str], ...] = (
    ("noqa", r"\bno" + "qa" + r"\b"),
    ("type-ignore", r"type:\s*" + "ignore"),
    ("pragma-no-cover", r"pragma:\s*" + "no" + r"\s+cover"),
    ("pytest-skip", r"pytest\.mark\." + "skip"),
    ("pytest-xfail", r"pytest\.mark\." + "xfail"),
    ("unittest-skip", r"unittest\." + "skip"),
    ("eslint-disable", "eslint-" + "disable"),
    ("ts-ignore", r"@ts-" + "ignore" + r"\b"),
    ("ts-expect-error", r"@ts-" + "expect-error" + r"\b"),
    ("dot-only", r"\." + r"only\s*\("),
    ("it-skip", r"\bit\." + "skip" + r"\b"),
    ("describe-skip", r"\bdescribe\." + "skip" + r"\b"),
    ("pylint-disable", "pylint" + r":\s*" + "disable"),
    ("no-verify", r"--no-" + "verify" + r"\b"),
)


@dataclass(frozen=True)
class SuppressionHit:
    path: str
    line_number: int
    pattern: str
    text: str


@dataclass(frozen=True)
class SuppressionSettings:
    extra_patterns: tuple[str, ...]
    allow_patterns: tuple[str, ...]
    allow_paths: tuple[str, ...]


def load_suppression_settings(root: Path) -> SuppressionSettings:
    governance = _governance(root)
    table = governance.get("suppressions")
    if table is None:
        return SuppressionSettings((), (), ())
    if not isinstance(table, dict):
        raise UsageError("Invalid [governance.suppressions]: expected a table")
    return SuppressionSettings(
        extra_patterns=_string_list(table.get("extra_patterns"), "extra_patterns"),
        allow_patterns=_string_list(table.get("allow_patterns"), "allow_patterns"),
        allow_paths=_string_list(table.get("allow_paths"), "allow_paths"),
    )


def scan_suppressions(
    root: Path,
    *,
    base: str | None = None,
    staged: bool = False,
) -> list[SuppressionHit]:
    """Return added-line hits. Empty when the diff is clean."""
    if not git_available(root):
        raise UsageError("Not a git work tree; suppression scan needs a diff")
    settings = load_suppression_settings(root)
    compiled = _compile_patterns(settings.extra_patterns)
    allow = _compile_allow(settings.allow_patterns)
    fences_by_path: dict[str, set[int]] = {}
    hits: list[SuppressionHit] = []
    for line in added_lines(root, base=base, staged=staged):
        if _path_allowed(line.path, settings.allow_paths):
            continue
        if any(pattern.search(line.text) for pattern in allow):
            continue
        searchable = line.text
        if _is_markdown(line.path):
            if line.path not in fences_by_path:
                fences_by_path[line.path] = _fenced_line_numbers(root, line.path)
            if line.line_number in fences_by_path[line.path]:
                continue
            searchable = _mask_inline_code(line.text)
        for name, pattern in compiled:
            if pattern.search(searchable):
                hits.append(
                    SuppressionHit(
                        path=line.path,
                        line_number=line.line_number,
                        pattern=name,
                        text=line.text.strip(),
                    )
                )
    return hits


def _is_markdown(path: str) -> bool:
    return Path(path).suffix.lower() in _MARKDOWN_SUFFIXES


def _fenced_line_numbers(root: Path, path: str) -> set[int]:
    """Line numbers inside a fenced code block of a markdown file.

    Fence delimiter lines themselves are not inside the block. A missing
    file yields an empty set so the line is still scanned for inline spans.
    """
    file_path = root / path
    try:
        text = file_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return set()
    inside: set[int] = set()
    opener: str | None = None
    opener_len = 0
    for number, raw in enumerate(text.splitlines(), start=1):
        if opener is None:
            match = _FENCE_OPEN.match(raw)
            if match:
                token = match.group(2)
                opener = token[0]
                opener_len = len(token)
            continue
        stripped = raw.strip()
        if stripped and len(stripped) >= opener_len and set(stripped) == {opener}:
            opener = None
            continue
        inside.add(number)
    return inside


def _mask_inline_code(text: str) -> str:
    """Replace markdown inline code spans with spaces, preserving indexes."""
    chars = list(text)
    index = 0
    length = len(chars)
    while index < length:
        if chars[index] != "`":
            index += 1
            continue
        end = index
        while end < length and chars[end] == "`":
            end += 1
        opener_len = end - index
        cursor = end
        closed = False
        while cursor < length:
            if chars[cursor] != "`":
                cursor += 1
                continue
            run = cursor
            while run < length and chars[run] == "`":
                run += 1
            if run - cursor == opener_len:
                for pos in range(index, run):
                    chars[pos] = " "
                index = run
                closed = True
                break
            cursor = run
        if not closed:
            index = end
    return "".join(chars)


def _compile_patterns(extra: tuple[str, ...]) -> list[tuple[str, re.Pattern[str]]]:
    compiled: list[tuple[str, re.Pattern[str]]] = []
    for name, expression in _DEFAULT_PATTERNS:
        compiled.append((name, re.compile(expression)))
    for index, expression in enumerate(extra):
        try:
            compiled.append((f"extra:{expression}", re.compile(expression)))
        except re.error as exc:
            raise UsageError(f"Invalid governance.suppressions.extra_patterns[{index}]: {exc}") from exc
    return compiled


def _compile_allow(patterns: tuple[str, ...]) -> list[re.Pattern[str]]:
    compiled: list[re.Pattern[str]] = []
    for index, expression in enumerate(patterns):
        try:
            compiled.append(re.compile(expression))
        except re.error as exc:
            raise UsageError(f"Invalid governance.suppressions.allow_patterns[{index}]: {exc}") from exc
    return compiled


def _path_allowed(path: str, globs: tuple[str, ...]) -> bool:
    return any(glob_match(path, pattern) for pattern in globs)


def _governance(root: Path) -> dict[str, Any]:
    raw = load_project_config(root).get("governance")
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise UsageError("Invalid [governance]: expected a table")
    return raw


def _string_list(value: object, label: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise UsageError(f"Invalid governance.suppressions.{label}: expected a list of strings")
    return tuple(value)


def format_hit(hit: SuppressionHit) -> str:
    preview = hit.text
    if len(preview) > 160:
        preview = preview[:157] + "..."
    return f"{hit.path}:{hit.line_number}: {hit.pattern}: {preview}"
