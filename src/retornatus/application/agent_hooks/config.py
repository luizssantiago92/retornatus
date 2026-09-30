"""Write and remove project agent-hook config for Claude, Cursor, and Codex.

Stop entries are identified by ``retornatus hook stop --host <name>``.
Session-start entries use ``retornatus hook session-start --host <name>``.
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


def parse_hosts(raw: list[str] | None) -> tuple[str, ...]:
    """Normalize ``--host`` values. An empty list means all three hosts."""
    if not raw:
        return HOSTS
    selected: list[str] = []
    for item in raw:
        name = item.strip().casefold()
        if name not in HOSTS:
            raise UsageError(
                f"Unknown host {item!r}. Expected one of: claude, cursor, codex."
            )
        if name not in selected:
            selected.append(name)
    return tuple(selected)


def hook_config_path(root: Path, host: str) -> Path:
    """Project file that stores one host's hook config."""
    try:
        relative = _RELATIVE[host]
    except KeyError as exc:
        raise UsageError(
            f"Unknown host {host!r}. Expected one of: claude, cursor, codex."
        ) from exc
    return root / relative


def is_retornatus_stop_command(command: object, host: str) -> bool:
    """True when ``command`` invokes this host's Stop hook.

    A prefix such as ``uv run`` still matches. A different host does not.
    """
    return _command_has(command, ["retornatus", "hook", "stop", "--host", host])


def is_retornatus_session_command(command: object, host: str) -> bool:
    """True when ``command`` invokes this host's session-start hook."""
    return _command_has(command, ["retornatus", "hook", "session-start", "--host", host])


def _command_has(command: object, needle: list[str]) -> bool:
    if not isinstance(command, str):
        return False
    parts = command.split()
    width = len(needle)
    return any(parts[index : index + width] == needle for index in range(len(parts) - width + 1))


def agent_hook_status(root: Path) -> dict[str, str]:
    """Stop and session-start state for each host.

    ``absent`` means neither Retornatus hook is present. ``unreadable`` means
    the file is not a JSON object. Otherwise the value names each hook.
    """
    return {host: _status_one(root, host) for host in HOSTS}


def install_agent_hooks(root: Path, hosts: tuple[str, ...]) -> dict[str, str]:
    """Merge Retornatus Stop and session-start hooks into the selected files."""
    states: dict[str, str] = {}
    for host in hosts:
        _install_one(root, host)
        states[host] = "installed"
    return states


def remove_agent_hooks(root: Path, hosts: tuple[str, ...]) -> dict[str, str]:
    """Drop Retornatus Stop and session-start hooks. Other hooks and keys stay."""
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
    if not stop and not session:
        return "absent"
    stop_state = "installed" if stop else "absent"
    session_state = "installed" if session else "absent"
    return f"stop={stop_state} session-start={session_state}"


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
        updated = _drop_cursor_scaffold(updated)
    else:
        updated = _strip_grouped(data, host, "Stop", is_retornatus_stop_command)
        updated = _strip_grouped(updated, host, "SessionStart", is_retornatus_session_command)
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
    predicate = is_retornatus_stop_command if kind == "stop" else is_retornatus_session_command
    if host == "cursor":
        key = "stop" if kind == "stop" else "sessionStart"
        entries = hooks.get(key)
        if not isinstance(entries, list):
            return False
        return any(
            isinstance(item, dict) and predicate(item.get("command"), host) for item in entries
        )
    key = "Stop" if kind == "stop" else "SessionStart"
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


def _grouped_handler(host: str, *, kind: str) -> dict[str, Any]:
    command = stop_command(host) if kind == "stop" else session_start_command(host)
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
        for item in inner:
            if isinstance(item, dict) and predicate(item.get("command"), host):
                if not updated:
                    kept.append(handler)
                    updated = True
                continue
            kept.append(item)
        cloned = dict(group)
        cloned["hooks"] = kept
        rewritten.append(cloned)
    if not updated:
        rewritten.append({"hooks": [handler]})
    hooks[event] = rewritten
    return data


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
        kept = [
            item
            for item in inner
            if not (isinstance(item, dict) and predicate(item.get("command"), host))
        ]
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
    kept = [
        item
        for item in entries
        if not (isinstance(item, dict) and predicate(item.get("command"), "cursor"))
    ]
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
