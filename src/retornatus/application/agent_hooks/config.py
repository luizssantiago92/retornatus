"""Write and remove project Stop-hook config for Claude, Cursor, and Codex.

Entries are identified by the command ``retornatus hook stop --host <name>``.
A second install updates that entry. User hooks and unrelated keys stay.
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
    if not isinstance(command, str):
        return False
    parts = command.split()
    needle = ["retornatus", "hook", "stop", "--host", host]
    width = len(needle)
    return any(parts[index : index + width] == needle for index in range(len(parts) - width + 1))


def agent_hook_status(root: Path) -> dict[str, str]:
    """``installed``, ``absent``, or ``unreadable`` for each host."""
    return {host: _status_one(root, host) for host in HOSTS}


def install_agent_hooks(root: Path, hosts: tuple[str, ...]) -> dict[str, str]:
    """Merge Retornatus Stop hooks into the selected host files."""
    states: dict[str, str] = {}
    for host in hosts:
        _install_one(root, host)
        states[host] = "installed"
    return states


def remove_agent_hooks(root: Path, hosts: tuple[str, ...]) -> dict[str, str]:
    """Drop Retornatus Stop hooks. Other hooks and keys stay."""
    return {host: _remove_one(root, host) for host in hosts}


def _status_one(root: Path, host: str) -> str:
    path = hook_config_path(root, host)
    if not path.is_file():
        return "absent"
    try:
        data = _read_json_object(path)
    except UsageError:
        return "unreadable"
    return "installed" if _contains(data, host) else "absent"


def _install_one(root: Path, host: str) -> None:
    path = hook_config_path(root, host)
    data = _read_json_object(path) if path.is_file() else {}
    updated = _upsert_cursor(data) if host == "cursor" else _upsert_grouped(data, host)
    _write_json(path, updated)


def _remove_one(root: Path, host: str) -> str:
    path = hook_config_path(root, host)
    if not path.is_file():
        return "absent"
    data = _read_json_object(path)
    before = json.dumps(data, sort_keys=True)
    updated = _strip_cursor(data) if host == "cursor" else _strip_grouped(data, host)
    if json.dumps(updated, sort_keys=True) == before:
        return "absent"
    if updated:
        _write_json(path, updated)
    elif path.is_file():
        path.unlink()
    return "removed"


def _contains(data: dict[str, Any], host: str) -> bool:
    hooks = data.get("hooks")
    if not isinstance(hooks, dict):
        return False
    if host == "cursor":
        stop = hooks.get("stop")
        if not isinstance(stop, list):
            return False
        return any(
            isinstance(item, dict) and is_retornatus_stop_command(item.get("command"), host)
            for item in stop
        )
    groups = hooks.get("Stop")
    if not isinstance(groups, list):
        return False
    for group in groups:
        if not isinstance(group, dict):
            continue
        inner = group.get("hooks")
        if not isinstance(inner, list):
            continue
        if any(
            isinstance(item, dict) and is_retornatus_stop_command(item.get("command"), host)
            for item in inner
        ):
            return True
    return False


def _handler(host: str) -> dict[str, Any]:
    return {
        "type": "command",
        "command": stop_command(host),
        "timeout": COMMAND_TIMEOUT_SECONDS,
    }


def _upsert_grouped(data: dict[str, Any], host: str) -> dict[str, Any]:
    hooks = _object_key(data, "hooks", label=hook_config_path(Path(), host).name)
    groups = hooks.get("Stop")
    if groups is None:
        groups = []
        hooks["Stop"] = groups
    if not isinstance(groups, list):
        raise UsageError(f"{hook_config_path(Path(), host).name} hooks.Stop must be a list")
    handler = _handler(host)
    updated = False
    rewritten: list[Any] = []
    for group in groups:
        if not isinstance(group, dict) or not isinstance(group.get("hooks"), list):
            rewritten.append(group)
            continue
        inner = group["hooks"]
        kept: list[Any] = []
        for item in inner:
            if isinstance(item, dict) and is_retornatus_stop_command(item.get("command"), host):
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
    hooks["Stop"] = rewritten
    return data


def _strip_grouped(data: dict[str, Any], host: str) -> dict[str, Any]:
    hooks = data.get("hooks")
    if not isinstance(hooks, dict):
        return data
    groups = hooks.get("Stop")
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
            if not (
                isinstance(item, dict) and is_retornatus_stop_command(item.get("command"), host)
            )
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
        hooks["Stop"] = rewritten
    else:
        hooks.pop("Stop", None)
    if not hooks:
        data.pop("hooks", None)
    return data


def _upsert_cursor(data: dict[str, Any]) -> dict[str, Any]:
    if "version" not in data:
        data = {"version": 1, **data}
    hooks = _object_key(data, "hooks", label="hooks.json")
    stop = hooks.get("stop")
    if stop is None:
        stop = []
        hooks["stop"] = stop
    if not isinstance(stop, list):
        raise UsageError("hooks.json hooks.stop must be a list")
    handler = {"command": stop_command("cursor"), "loop_limit": CURSOR_LOOP_LIMIT}
    updated = False
    rewritten: list[Any] = []
    for item in stop:
        if isinstance(item, dict) and is_retornatus_stop_command(item.get("command"), "cursor"):
            if not updated:
                rewritten.append(handler)
                updated = True
            continue
        rewritten.append(item)
    if not updated:
        rewritten.append(handler)
    hooks["stop"] = rewritten
    return data


def _strip_cursor(data: dict[str, Any]) -> dict[str, Any]:
    hooks = data.get("hooks")
    if not isinstance(hooks, dict):
        return data
    stop = hooks.get("stop")
    if not isinstance(stop, list):
        return data
    kept = [
        item
        for item in stop
        if not (isinstance(item, dict) and is_retornatus_stop_command(item.get("command"), "cursor"))
    ]
    if len(kept) == len(stop):
        return data
    if kept:
        hooks["stop"] = kept
    else:
        hooks.pop("stop", None)
    if not hooks:
        data.pop("hooks", None)
    # A file that is only the version scaffold we add on a fresh install
    # goes away with the hook. A different version, or any other key, stays.
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
