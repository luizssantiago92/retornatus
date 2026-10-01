"""Warn when an agent edits a file outside the active Change scope.

The comparison is :func:`path_in_scope`, the same match ``gate scope`` uses.
Nothing here shells out or calls git. A missing project, no active Change,
an in-scope path, and ``.retornatus/`` print nothing. Every error exits 0
with one stderr line so a hook cannot trap the session.

Default ``[hooks] scope_mode`` is ``warn``. ``block`` denies the tool call
only on events whose host documents a deny decision. Other events fall back
to the documented warning channel. ``off`` stays silent.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from retornatus.application.agent_hooks.config import HOSTS
from retornatus.application.agent_hooks.stop import locate_project
from retornatus.application.assurance.settings import load_project_config
from retornatus.application.governance.globs import normalize_repo_path
from retornatus.application.governance.scope import change_resources, path_in_scope
from retornatus.bootstrap.hooks import active_change_ids

_MODES = frozenset({"warn", "block", "off"})
_SCOPE_SHOWN = 12
_DRIVE = re.compile(r"^[A-Za-z]:")
_PATCH_HEADER = re.compile(
    r"^\*\*\* (?:Add File|Delete File|Update File|Move to):[ \t]*(.+?)\s*$",
    re.MULTILINE,
)
_CLAUDE_EDIT_TOOLS = frozenset({"Edit", "Write", "MultiEdit"})
_CODEX_EDIT_TOOLS = frozenset({"apply_patch", "Edit", "Write"})
_CURSOR_EDIT_TOOLS = frozenset({"Write"})
_CURSOR_SILENT_EVENTS = frozenset({"after_file", "before_read", "after_tab", "before_tab"})


@dataclass(frozen=True)
class FileEditResponse:
    """What the file-edit command writes. Exit 0 is success and fail-open."""

    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0


@dataclass(frozen=True)
class EditedPath:
    """One path from a host payload, relative to the repo when it is inside."""

    display: str
    relative: str | None


def handle_file_edit(
    host: str,
    raw_stdin: str,
    *,
    start: Path,
    walk: bool,
) -> FileEditResponse:
    """Read one host payload and return a warning, a deny, or nothing."""
    try:
        return _handle_file_edit(host, raw_stdin, start=start, walk=walk)
    except Exception as exc:
        return _fail_open(f"{type(exc).__name__}: {exc}")


def scope_mode(root: Path) -> str:
    """``warn``, ``block``, or ``off``. Missing key keeps the default, warn.

    A non-string or any other value is an error so the hook fails open.
    """
    hooks = load_project_config(root).get("hooks")
    if hooks is None:
        return "warn"
    if not isinstance(hooks, dict):
        raise ValueError("Invalid [hooks]: expected a table")
    if "scope_mode" not in hooks:
        return "warn"
    raw = hooks["scope_mode"]
    if isinstance(raw, str) and raw in _MODES:
        return raw
    raise ValueError('Invalid [hooks] scope_mode: expected "warn", "block", or "off"')


def scope_mode_label(root: Path) -> str:
    """Mode for ``doctor``. A broken value is ``invalid`` and does not raise."""
    try:
        return scope_mode(root)
    except (OSError, ValueError):
        return "invalid"


def classify_edited_path(root: Path, raw: str) -> EditedPath | None:
    """Map a host path to a repo-relative path, or mark it outside the repo.

    Separators are normalized before the comparison. An empty string is ignored.
    """
    text = raw.strip().replace("\\", "/")
    while text.startswith("./"):
        text = text[2:]
    if not text or text == ".":
        return None
    if _is_absolute(text):
        return _classify_absolute(root, text)
    return _classify_relative(root, text)


def _handle_file_edit(
    host: str,
    raw_stdin: str,
    *,
    start: Path,
    walk: bool,
) -> FileEditResponse:
    name = host.strip().casefold()
    if name not in HOSTS:
        return _fail_open(f"unknown host {host!r}")
    payload, parsed = _parse_payload(raw_stdin)
    if not parsed:
        return _fail_open("invalid JSON on stdin")
    root = locate_project(start, walk=walk)
    if root is None:
        return FileEditResponse()
    mode = scope_mode(root)
    if mode == "off":
        return FileEditResponse()
    change_ids = active_change_ids(root)
    if not change_ids:
        return FileEditResponse()
    event = _event_name(payload)
    edited = _dedupe(classify_edited_path(root, item) for item in _raw_paths(name, payload))
    violations = _violations(root, change_ids, edited)
    if not violations:
        return FileEditResponse()
    warning = _warning(violations)
    stdout = _host_stdout(name, event, mode, warning)
    return FileEditResponse(stdout=stdout)


def _violations(
    root: Path,
    change_ids: list[str],
    edited: list[EditedPath],
) -> list[tuple[EditedPath, list[tuple[str, str]]]]:
    """Paths that miss at least one active Change, with that Change's scope."""
    scopes = {change_id: _scope_text(root, change_id) for change_id in change_ids}
    resources = {change_id: change_resources(root, change_id) for change_id in change_ids}
    found: list[tuple[EditedPath, list[tuple[str, str]]]] = []
    for path in edited:
        missed: list[tuple[str, str]] = []
        for change_id in change_ids:
            if path.relative is not None and path_in_scope(path.relative, resources[change_id]):
                continue
            missed.append((change_id, scopes[change_id]))
        if missed:
            found.append((path, missed))
    return found


def _warning(violations: list[tuple[EditedPath, list[tuple[str, str]]]]) -> str:
    parts: list[str] = []
    for path, missed in violations:
        scopes = " and ".join(f"{change_id} scope ({scope})" for change_id, scope in missed)
        parts.append(f"{path.display} is outside {scopes}")
    joined = "; ".join(parts)
    return (
        f"{joined}. Revert the edit, or update the Change scope "
        "(Task resources) to include this path."
    )


def _scope_text(root: Path, change_id: str) -> str:
    seen: list[str] = []
    for resource in change_resources(root, change_id):
        text = resource.strip()
        if text and text not in seen:
            seen.append(text)
    if not seen:
        return "none declared"
    shown = seen[:_SCOPE_SHOWN]
    extra = len(seen) - len(shown)
    summary = ", ".join(shown)
    if extra:
        summary += f" +{extra} more"
    return summary


def _host_stdout(host: str, event: str, mode: str, warning: str) -> str:
    if host == "cursor":
        return _cursor_stdout(event, mode, warning)
    hook_event = "PostToolUse" if event == "post" else "PreToolUse"
    if mode == "block" and hook_event == "PreToolUse":
        body: dict[str, Any] = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": warning,
            }
        }
    else:
        body = {
            "hookSpecificOutput": {
                "hookEventName": hook_event,
                "additionalContext": warning,
            }
        }
    return _dump(body)


def _cursor_stdout(event: str, mode: str, warning: str) -> str:
    """Cursor channels that the hooks reference says the agent actually reads.

    ``afterFileEdit`` documents ``file_path`` and no output fields.
    ``preToolUse`` delivers ``agent_message`` only when ``permission`` is deny.
    ``postToolUse`` delivers ``additional_context`` after the edit. A missing
    event name uses that same split: deny when blocking, context when warning.
    """
    if event in _CURSOR_SILENT_EVENTS:
        return ""
    if event == "pre":
        if mode != "block":
            return ""
        return _dump({"permission": "deny", "agent_message": warning})
    if event == "post":
        return _dump({"additional_context": warning})
    if mode == "block":
        return _dump({"permission": "deny", "agent_message": warning})
    return _dump({"additional_context": warning})


def _raw_paths(host: str, payload: dict[str, Any]) -> list[str]:
    tool_name = payload.get("tool_name")
    name = tool_name if isinstance(tool_name, str) else ""
    if host == "claude":
        if name and name not in _CLAUDE_EDIT_TOOLS:
            return []
        return _string_values(_tool_dict(payload), ("file_path",))
    if host == "codex":
        if name and name not in _CODEX_EDIT_TOOLS:
            return []
        return _codex_paths(payload)
    if name and name not in _CURSOR_EDIT_TOOLS and _event_name(payload) not in _CURSOR_SILENT_EVENTS:
        return []
    found = _string_values(payload, ("file_path",))
    found.extend(_string_values(_tool_dict(payload), ("file_path", "path", "filePath")))
    return found


def _codex_paths(payload: dict[str, Any]) -> list[str]:
    tool_input = payload.get("tool_input")
    found: list[str] = []
    if isinstance(tool_input, dict):
        found.extend(_string_values(tool_input, ("file_path",)))
        found.extend(_paths_in_command(tool_input.get("command")))
    elif isinstance(tool_input, str):
        found.extend(_paths_in_command(tool_input))
    return found


def _paths_in_command(command: object) -> list[str]:
    text = _command_text(command)
    if not text:
        return []
    return [match.group(1).strip() for match in _PATCH_HEADER.finditer(text) if match.group(1).strip()]


def _command_text(command: object) -> str:
    if isinstance(command, str):
        return command
    if isinstance(command, list):
        parts = [item for item in command if isinstance(item, str)]
        for part in parts:
            if "Begin Patch" in part or "*** " in part:
                return part
        return "\n".join(parts)
    return ""


def _tool_dict(payload: dict[str, Any]) -> dict[str, Any]:
    raw = payload.get("tool_input")
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str) and raw.strip().startswith("{"):
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return {}
        if isinstance(parsed, dict):
            return parsed
    return {}


def _string_values(data: dict[str, Any], keys: tuple[str, ...]) -> list[str]:
    found: list[str] = []
    for key in keys:
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            found.append(value)
            return found
    return found


def _dedupe(paths: Any) -> list[EditedPath]:
    seen: set[str] = set()
    chosen: list[EditedPath] = []
    for item in paths:
        if item is None:
            continue
        key = item.relative if item.relative is not None else f"out:{item.display}"
        if key in seen:
            continue
        seen.add(key)
        chosen.append(item)
    return chosen


def _event_name(payload: dict[str, Any]) -> str:
    """Canonical event token. Host casing differences collapse here."""
    raw = payload.get("hook_event_name")
    if not isinstance(raw, str):
        return ""
    key = raw.strip().casefold().replace("_", "")
    return {
        "pretooluse": "pre",
        "posttooluse": "post",
        "afterfileedit": "after_file",
        "beforereadfile": "before_read",
        "aftertabfileedit": "after_tab",
        "beforetabfileread": "before_tab",
    }.get(key, "other")


def _classify_absolute(root: Path, text: str) -> EditedPath:
    if _DRIVE.match(text) and os.name != "nt":
        return EditedPath(display=text, relative=None)
    try:
        relative = Path(text).resolve().relative_to(root.resolve())
    except (OSError, ValueError):
        return EditedPath(display=text, relative=None)
    repo_path = normalize_repo_path(relative.as_posix())
    if not repo_path:
        return EditedPath(display=text, relative=None)
    return EditedPath(display=repo_path, relative=repo_path)


def _classify_relative(root: Path, text: str) -> EditedPath:
    try:
        relative = (root.resolve() / text).resolve().relative_to(root.resolve())
    except (OSError, ValueError):
        return EditedPath(display=text, relative=None)
    repo_path = normalize_repo_path(relative.as_posix())
    if not repo_path:
        return EditedPath(display=text, relative=None)
    return EditedPath(display=repo_path, relative=repo_path)


def _is_absolute(text: str) -> bool:
    return text.startswith("/") or _DRIVE.match(text) is not None


def _parse_payload(raw: str) -> tuple[dict[str, Any], bool]:
    if not raw.strip():
        return {}, True
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {}, False
    if isinstance(parsed, dict):
        return parsed, True
    return {}, True


def _dump(body: dict[str, Any]) -> str:
    return json.dumps(body, ensure_ascii=False) + "\n"


def _fail_open(detail: str) -> FileEditResponse:
    line = detail.replace("\n", " ").strip()
    return FileEditResponse(stderr=f"retornatus hook file-edit: fail-open ({line})\n")
