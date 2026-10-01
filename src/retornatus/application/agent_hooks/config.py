"""Write and remove project agent-hook config for Claude, Cursor, and Codex.

Stop entries are identified by ``retornatus hook stop --host <name>``.
Session-start entries use ``retornatus hook session-start --host <name>``.
File-edit entries use ``retornatus hook file-edit --host <name>``.
A second install updates those entries. User hooks and unrelated keys stay.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from retornatus.domain.errors import UsageError

HOSTS: tuple[str, ...] = ("claude", "cursor", "codex")
CURSOR_LOOP_LIMIT = 1
COMMAND_TIMEOUT_SECONDS = 30
CLAUDE_FILE_EDIT_MATCHER = "Edit|Write|MultiEdit"
CODEX_FILE_EDIT_MATCHER = "apply_patch|Edit|Write"
CURSOR_FILE_EDIT_MATCHER = "Write"
_CURSOR_FILE_EDIT_EVENTS = ("preToolUse", "postToolUse")

_RELATIVE: dict[str, Path] = {
    "claude": Path(".claude") / "settings.json",
    "cursor": Path(".cursor") / "hooks.json",
    "codex": Path(".codex") / "hooks.json",
}


def stop_command(host: str) -> str:
    """Shell command the host runs at turn end."""
    return f"retornatus hook stop --host {host}"


def session_start_command(host: str) -> str:
    """Shell command the host runs when a session starts."""
    return f"retornatus hook session-start --host {host}"


def file_edit_command(host: str) -> str:
    """Shell command the host runs around a file edit."""
    return f"retornatus hook file-edit --host {host}"


def parse_hosts(raw: list[str] | None) -> tuple[str, ...]:
    """Normalize ``--host`` values. An empty list means all three hosts."""
    if not raw:
        return HOSTS
    selected: list[str] = []
    for item in raw:
        name = item.strip().casefold()
        if name not in HOSTS:
            raise UsageError(f"Unknown host {item!r}. Expected one of: claude, cursor, codex.")
        if name not in selected:
            selected.append(name)
    return tuple(selected)


def hook_config_path(root: Path, host: str) -> Path:
    """Project file that stores one host's hook config."""
    try:
        relative = _RELATIVE[host]
    except KeyError as exc:
        raise UsageError(f"Unknown host {host!r}. Expected one of: claude, cursor, codex.") from exc
    return root / relative


def is_retornatus_stop_command(command: object, host: str) -> bool:
    """True when ``command`` invokes this host's Stop hook.

    A prefix such as ``uv run`` still matches. A different host does not.
    """
    return _command_has(command, ["retornatus", "hook", "stop", "--host", host])


def is_retornatus_session_command(command: object, host: str) -> bool:
    """True when ``command`` invokes this host's session-start hook."""
    return _command_has(command, ["retornatus", "hook", "session-start", "--host", host])


def is_retornatus_file_edit_command(command: object, host: str) -> bool:
    """True when ``command`` invokes this host's file-edit hook."""
    return _command_has(command, ["retornatus", "hook", "file-edit", "--host", host])


def _command_has(command: object, needle: list[str]) -> bool:
    if not isinstance(command, str):
        return False
    parts = command.split()
    width = len(needle)
    return any(parts[index : index + width] == needle for index in range(len(parts) - width + 1))


def agent_hook_status(root: Path) -> dict[str, str]:
    """Stop, session-start, and file-edit state for each host.

    ``absent`` means no Retornatus hook is present. ``unreadable`` means
    the file is not a JSON object. Otherwise the value names each hook.
    """
    return {host: _status_one(root, host) for host in HOSTS}


def install_agent_hooks(root: Path, hosts: tuple[str, ...]) -> dict[str, str]:
    """Merge Retornatus Stop, session-start, and file-edit hooks into the files."""
    states: dict[str, str] = {}
    for host in hosts:
        _install_one(root, host)
        states[host] = "installed"
    return states


def remove_agent_hooks(root: Path, hosts: tuple[str, ...]) -> dict[str, str]:
    """Drop Retornatus Stop, session-start, and file-edit hooks. Other hooks stay."""
    return {host: _remove_one(root, host) for host in hosts}


def _status_one(root: Path, host: str) -> str:
    path = hook_config_path(root, host)
    if not path.is_file():
        return "absent"
    try:
        data = _read_json_object(path)
    except UsageError:
        return "unreadable"
    stop = _contains(data, host, kind="stop")
    session = _contains(data, host, kind="session")
    file_edit = _contains(data, host, kind="file-edit")
    if not stop and not session and not file_edit:
        return "absent"
    stop_state = "installed" if stop else "absent"
    session_state = "installed" if session else "absent"
    file_edit_state = "installed" if file_edit else "absent"
    return f"stop={stop_state} session-start={session_state} file-edit={file_edit_state}"


def _install_one(root: Path, host: str) -> None:
    path = hook_config_path(root, host)
    data = _read_json_object(path) if path.is_file() else {}
    if host == "cursor":
        updated = _upsert_cursor_list(
            data,
            "stop",
            {"command": stop_command("cursor"), "loop_limit": CURSOR_LOOP_LIMIT},
            is_retornatus_stop_command,
        )
        updated = _upsert_cursor_list(
            updated,
            "sessionStart",
            {
                "command": session_start_command("cursor"),
                "timeout": COMMAND_TIMEOUT_SECONDS,
            },
            is_retornatus_session_command,
        )
        for event in _CURSOR_FILE_EDIT_EVENTS:
            updated = _upsert_cursor_list(
                updated,
                event,
                {
                    "command": file_edit_command("cursor"),
                    "matcher": CURSOR_FILE_EDIT_MATCHER,
                    "timeout": COMMAND_TIMEOUT_SECONDS,
                },
                is_retornatus_file_edit_command,
            )
    else:
        updated = _upsert_grouped(
            data,
            host,
            "Stop",
            _grouped_handler(host, kind="stop"),
            is_retornatus_stop_command,
        )
        updated = _upsert_grouped(
            updated,
            host,
            "SessionStart",
            _grouped_handler(host, kind="session"),
            is_retornatus_session_command,
        )
        matcher = CLAUDE_FILE_EDIT_MATCHER if host == "claude" else CODEX_FILE_EDIT_MATCHER
        updated = _upsert_grouped(
            updated,
            host,
            "PreToolUse",
            _grouped_handler(host, kind="file-edit"),
            is_retornatus_file_edit_command,
            matcher=matcher,
        )
    _write_json(path, updated)


def _remove_one(root: Path, host: str) -> str:
    path = hook_config_path(root, host)
    if not path.is_file():
        return "absent"
    data = _read_json_object(path)
    before = json.dumps(data, sort_keys=True)
    if host == "cursor":
        updated = _strip_cursor_list(data, "stop", is_retornatus_stop_command)
        updated = _strip_cursor_list(updated, "sessionStart", is_retornatus_session_command)
        for event in _CURSOR_FILE_EDIT_EVENTS:
            updated = _strip_cursor_list(updated, event, is_retornatus_file_edit_command)
        updated = _drop_cursor_scaffold(updated)
    else:
        updated = _strip_grouped(data, host, "Stop", is_retornatus_stop_command)
        updated = _strip_grouped(updated, host, "SessionStart", is_retornatus_session_command)
        updated = _strip_grouped(updated, host, "PreToolUse", is_retornatus_file_edit_command)
    if json.dumps(updated, sort_keys=True) == before:
        return "absent"
    if updated:
        _write_json(path, updated)
    elif path.is_file():
        path.unlink()
    return "removed"


def _contains(data: dict[str, Any], host: str, *, kind: str) -> bool:
    hooks = data.get("hooks")
    if not isinstance(hooks, dict):
        return False
    predicate = _predicate(kind)
    if host == "cursor":
        keys = _CURSOR_FILE_EDIT_EVENTS if kind == "file-edit" else (("stop",) if kind == "stop" else ("sessionStart",))
        return any(_cursor_list_has(hooks, key, predicate) for key in keys)
    key = {"stop": "Stop", "session": "SessionStart", "file-edit": "PreToolUse"}[kind]
    groups = hooks.get(key)
    if not isinstance(groups, list):
        return False
    for group in groups:
        if not isinstance(group, dict):
            continue
        inner = group.get("hooks")
        if not isinstance(inner, list):
            continue
        if any(isinstance(item, dict) and predicate(item.get("command"), host) for item in inner):
            return True
    return False


def _predicate(kind: str) -> Any:
    if kind == "stop":
        return is_retornatus_stop_command
    if kind == "session":
        return is_retornatus_session_command
    return is_retornatus_file_edit_command


def _cursor_list_has(hooks: dict[str, Any], event: str, predicate: Any) -> bool:
    entries = hooks.get(event)
    if not isinstance(entries, list):
        return False
    return any(isinstance(item, dict) and predicate(item.get("command"), "cursor") for item in entries)


def _grouped_handler(host: str, *, kind: str) -> dict[str, Any]:
    if kind == "stop":
        command = stop_command(host)
    elif kind == "session":
        command = session_start_command(host)
    else:
        command = file_edit_command(host)
    return {
        "type": "command",
        "command": command,
        "timeout": COMMAND_TIMEOUT_SECONDS,
    }


def _upsert_grouped(
    data: dict[str, Any],
    host: str,
    event: str,
    handler: dict[str, Any],
    predicate: Any,
    matcher: str | None = None,
) -> dict[str, Any]:
    label = hook_config_path(Path(), host).name
    hooks = _object_key(data, "hooks", label=label)
    groups = hooks.get(event)
    if groups is None:
        groups = []
        hooks[event] = groups
    if not isinstance(groups, list):
        raise UsageError(f"{label} hooks.{event} must be a list")
    updated = False
    rewritten: list[Any] = []
    for group in groups:
        if not isinstance(group, dict) or not isinstance(group.get("hooks"), list):
            rewritten.append(group)
            continue
        inner = group["hooks"]
        kept: list[Any] = []
        replaced_here = False
        for item in inner:
            if isinstance(item, dict) and predicate(item.get("command"), host):
                if not updated:
                    kept.append(handler)
                    updated = True
                    replaced_here = True
                continue
            kept.append(item)
        cloned = dict(group)
        cloned["hooks"] = kept
        if replaced_here and matcher and _only_our_hooks(kept, host, predicate):
            cloned["matcher"] = matcher
        rewritten.append(cloned)
    if not updated:
        fresh: dict[str, Any] = {}
        if matcher:
            fresh["matcher"] = matcher
        fresh["hooks"] = [handler]
        rewritten.append(fresh)
    hooks[event] = rewritten
    return data


def _only_our_hooks(items: list[Any], host: str, predicate: Any) -> bool:
    return bool(items) and all(isinstance(item, dict) and predicate(item.get("command"), host) for item in items)


def _strip_grouped(
    data: dict[str, Any],
    host: str,
    event: str,
    predicate: Any,
) -> dict[str, Any]:
    hooks = data.get("hooks")
    if not isinstance(hooks, dict):
        return data
    groups = hooks.get(event)
    if not isinstance(groups, list):
        return data
    rewritten: list[Any] = []
    changed = False
    for group in groups:
        if not isinstance(group, dict) or not isinstance(group.get("hooks"), list):
            rewritten.append(group)
            continue
        inner = group["hooks"]
        kept = [item for item in inner if not (isinstance(item, dict) and predicate(item.get("command"), host))]
        if len(kept) != len(inner):
            changed = True
        if not kept:
            continue
        cloned = dict(group)
        cloned["hooks"] = kept
        rewritten.append(cloned)
    if not changed:
        return data
    if rewritten:
        hooks[event] = rewritten
    else:
        hooks.pop(event, None)
    if not hooks:
        data.pop("hooks", None)
    return data


def _upsert_cursor_list(
    data: dict[str, Any],
    event: str,
    handler: dict[str, Any],
    predicate: Any,
) -> dict[str, Any]:
    if "version" not in data:
        data = {"version": 1, **data}
    hooks = _object_key(data, "hooks", label="hooks.json")
    entries = hooks.get(event)
    if entries is None:
        entries = []
        hooks[event] = entries
    if not isinstance(entries, list):
        raise UsageError(f"hooks.json hooks.{event} must be a list")
    updated = False
    rewritten: list[Any] = []
    for item in entries:
        if isinstance(item, dict) and predicate(item.get("command"), "cursor"):
            if not updated:
                rewritten.append(handler)
                updated = True
            continue
        rewritten.append(item)
    if not updated:
        rewritten.append(handler)
    hooks[event] = rewritten
    return data


def _strip_cursor_list(
    data: dict[str, Any],
    event: str,
    predicate: Any,
) -> dict[str, Any]:
    hooks = data.get("hooks")
    if not isinstance(hooks, dict):
        return data
    entries = hooks.get(event)
    if not isinstance(entries, list):
        return data
    kept = [item for item in entries if not (isinstance(item, dict) and predicate(item.get("command"), "cursor"))]
    if len(kept) == len(entries):
        return data
    if kept:
        hooks[event] = kept
    else:
        hooks.pop(event, None)
    if not hooks:
        data.pop("hooks", None)
    return data


def _drop_cursor_scaffold(data: dict[str, Any]) -> dict[str, Any]:
    """Drop the version-only file a fresh install would leave behind."""
    if list(data) == ["version"] and data.get("version") == 1:
        return {}
    return data


def _object_key(data: dict[str, Any], key: str, *, label: str) -> dict[str, Any]:
    current = data.get(key)
    if current is None:
        current = {}
        data[key] = current
    if not isinstance(current, dict):
        raise UsageError(f"{label} key {key} must be an object")
    return current


def _read_json_object(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        return {}
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise UsageError(f"{path.name} is not valid JSON: {exc.msg}") from exc
    if not isinstance(parsed, dict):
        raise UsageError(f"{path.name} must be a JSON object")
    return parsed


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    path.write_text(text, encoding="utf-8", newline="\n")
