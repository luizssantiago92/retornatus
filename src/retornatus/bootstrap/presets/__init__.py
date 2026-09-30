"""Packaged config presets shipped as TOML data files.

Presets are not branches in ``init``. ``python-platform`` extends ``python``
by naming that file. Suggested ship commands stay comments in the rendered
config; ``verify`` reads the same packaged defaults until the project writes
``[[surfaces.ship.checks]]``.
"""

from __future__ import annotations

import json
import tomllib
from dataclasses import dataclass, replace
from importlib.resources import files
from typing import Any

import tomli_w

from retornatus import __version__
from retornatus.application.assurance.settings import RequiredCheck, _parse_check
from retornatus.domain.errors import UsageError

_PACKAGE = "retornatus.bootstrap.presets"


@dataclass(frozen=True)
class SurfaceCheck:
    """One infra command selected by path globs."""

    name: str
    globs: tuple[str, ...]
    run: tuple[str, ...]
    suggested: bool = True


@dataclass(frozen=True)
class Preset:
    """A preset after ``extends`` has been applied."""

    name: str
    summary: str
    extends: str | None
    required_checks: tuple[RequiredCheck, ...]
    code_globs: tuple[str, ...]
    ship_globs: tuple[str, ...]
    ship_note_subject: str
    ship_checks: tuple[SurfaceCheck, ...]
    ai_globs: tuple[str, ...]
    ai_note_subject: str
    ai_run: tuple[str, ...]


_EMPTY = Preset(
    name="",
    summary="",
    extends=None,
    required_checks=(),
    code_globs=(),
    ship_globs=(),
    ship_note_subject="ship rollback",
    ship_checks=(),
    ai_globs=(),
    ai_note_subject="ai fallback",
    ai_run=(),
)


def list_presets() -> list[tuple[str, str]]:
    """``(name, summary)`` for every packaged preset, sorted by name."""
    found: list[tuple[str, str]] = []
    root = files(_PACKAGE)
    for entry in root.iterdir():
        filename = entry.name
        if not filename.endswith(".toml"):
            continue
        name = filename[: -len(".toml")]
        preset = resolve_preset(name)
        found.append((preset.name, preset.summary))
    return sorted(found, key=lambda item: item[0])


def available_preset_names() -> list[str]:
    """Sorted preset names."""
    return _packaged_names()


def resolve_preset(name: str, *, reader: Any | None = None) -> Preset:
    """Load ``name`` and merge ``extends`` from parent to child.

    ``reader`` is a ``name -> dict`` hook for tests. The default reader loads
    the packaged TOML file.
    """
    return _resolve(name, reader=reader if reader is not None else _read_packaged, stack=())


def render_config(preset: Preset, *, version: str | None = None) -> str:
    """Render ``.retornatus/config.toml`` bytes as text (trailing newline)."""
    document: dict[str, Any] = {
        "schema_version": 1,
        "retornatus": {"version": version or __version__},
        "project": {"initialized": True, "preset": preset.name},
        "assurance": {
            "required_checks": [
                {
                    "name": check.name,
                    "run": list(check.run),
                    "types": sorted(check.types),
                }
                for check in preset.required_checks
            ]
        },
    }
    if preset.code_globs:
        document["governance"] = {"scope": {"code_globs": list(preset.code_globs)}}
    surfaces: dict[str, Any] = {}
    if preset.ship_globs or preset.ship_checks:
        surfaces["ship"] = {
            "note_subject": preset.ship_note_subject,
            "globs": list(preset.ship_globs),
        }
    if preset.ai_globs or preset.ai_run:
        surfaces["ai"] = {
            "note_subject": preset.ai_note_subject,
            "globs": list(preset.ai_globs),
            "run": list(preset.ai_run),
        }
    if surfaces:
        document["surfaces"] = surfaces
    text = tomli_w.dumps(document)
    if not text.endswith("\n"):
        text += "\n"
    suggested = [check for check in preset.ship_checks if check.suggested]
    if suggested or preset.ai_run:
        text += _suggestion_comments(suggested, ai_run=preset.ai_run)
    return text


def render_preset_document(name: str) -> str:
    """Comment header plus the config ``init --preset`` would write."""
    preset = resolve_preset(name)
    header = [f"# preset: {preset.name}"]
    if preset.extends:
        header.append(f"# extends: {preset.extends}")
    header.append(f"# {preset.summary}")
    return "\n".join(header) + "\n\n" + render_config(preset)


def _resolve(name: str, *, reader: Any, stack: tuple[str, ...]) -> Preset:
    if not isinstance(name, str) or not name.strip() or "/" in name or name.startswith("."):
        raise UsageError(_unknown_preset(name))
    cleaned = name.strip()
    if cleaned in stack:
        chain = " -> ".join((*stack, cleaned))
        raise UsageError(f"Preset extend cycle: {chain}")
    try:
        raw = reader(cleaned)
    except FileNotFoundError as exc:
        raise UsageError(_unknown_preset(cleaned)) from exc
    if not isinstance(raw, dict):
        raise UsageError(f"Preset {cleaned!r} must be a TOML table")
    parent_name = raw.get("extends")
    parent = _EMPTY
    if parent_name not in (None, ""):
        if not isinstance(parent_name, str):
            raise UsageError(f"Preset {cleaned!r} extends must be a string")
        parent = _resolve(parent_name, reader=reader, stack=(*stack, cleaned))
    return _overlay(parent, raw, filename=cleaned)


def _read_packaged(name: str) -> dict[str, Any]:
    path = files(_PACKAGE).joinpath(f"{name}.toml")
    if not path.is_file():
        raise FileNotFoundError(name)
    try:
        loaded = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise UsageError(f"Preset {name!r} could not be read: {exc}") from exc
    if not isinstance(loaded, dict):
        raise UsageError(f"Preset {name!r} must be a TOML table")
    return loaded


def _overlay(parent: Preset, raw: dict[str, Any], *, filename: str) -> Preset:
    declared = raw.get("name")
    if not isinstance(declared, str) or not declared.strip():
        raise UsageError(f"Preset {filename!r} is missing name")
    if declared.strip() != filename:
        raise UsageError(
            f"Preset file {filename}.toml declares name {declared.strip()!r}"
        )
    summary = raw.get("summary", parent.summary)
    if not isinstance(summary, str) or not summary.strip():
        raise UsageError(f"Preset {filename!r} is missing summary")
    extends = raw.get("extends")
    extends_name = extends.strip() if isinstance(extends, str) and extends.strip() else None
    assurance = _table(raw.get("assurance"), label=f"Preset {filename} assurance")
    if "required_checks" in assurance:
        checks = _required_checks(assurance.get("required_checks"), filename=filename)
    else:
        checks = parent.required_checks
    governance = _table(raw.get("governance"), label=f"Preset {filename} governance")
    scope = _table(governance.get("scope"), label=f"Preset {filename} governance.scope")
    if "code_globs" in scope:
        code_globs = _globs(scope.get("code_globs"), label=f"Preset {filename} code_globs")
    else:
        code_globs = parent.code_globs
    surfaces = _table(raw.get("surfaces"), label=f"Preset {filename} surfaces")
    ship_globs = parent.ship_globs
    ship_note = parent.ship_note_subject
    ship_checks = parent.ship_checks
    if "ship" in surfaces:
        ship = _table(surfaces.get("ship"), label=f"Preset {filename} surfaces.ship")
        ship_globs = _globs(ship.get("globs"), label=f"Preset {filename} ship globs")
        ship_note = _note_subject(ship.get("note_subject"), default=parent.ship_note_subject)
        if "checks" in ship:
            ship_checks = _surface_checks(ship.get("checks"), filename=filename)
    ai_globs = parent.ai_globs
    ai_note = parent.ai_note_subject
    ai_run = parent.ai_run
    if "ai" in surfaces:
        ai = _table(surfaces.get("ai"), label=f"Preset {filename} surfaces.ai")
        ai_globs = _globs(ai.get("globs"), label=f"Preset {filename} ai globs")
        ai_note = _note_subject(ai.get("note_subject"), default=parent.ai_note_subject)
        if "run" in ai:
            ai_run = _argv(ai.get("run"), label=f"Preset {filename} ai run")
    return replace(
        parent,
        name=declared.strip(),
        summary=summary.strip(),
        extends=extends_name,
        required_checks=checks,
        code_globs=code_globs,
        ship_globs=ship_globs,
        ship_note_subject=ship_note,
        ship_checks=ship_checks,
        ai_globs=ai_globs,
        ai_note_subject=ai_note,
        ai_run=ai_run,
    )


def _required_checks(raw: object, *, filename: str) -> tuple[RequiredCheck, ...]:
    if not isinstance(raw, list):
        raise UsageError(f"Preset {filename!r} required_checks must be a list")
    checks: list[RequiredCheck] = []
    seen: set[str] = set()
    for index, item in enumerate(raw):
        try:
            parsed = _parse_check(item, index=index)
        except ValueError as exc:
            raise UsageError(f"Preset {filename!r}: {exc}") from exc
        if parsed.name in seen:
            raise UsageError(f"Preset {filename!r} duplicate check {parsed.name!r}")
        seen.add(parsed.name)
        checks.append(parsed)
    return tuple(checks)


def _surface_checks(raw: object, *, filename: str) -> tuple[SurfaceCheck, ...]:
    if not isinstance(raw, list):
        raise UsageError(f"Preset {filename!r} ship checks must be a list")
    checks: list[SurfaceCheck] = []
    seen: set[str] = set()
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            raise UsageError(f"Preset {filename!r} ship check {index} must be a table")
        name = item.get("name")
        if not isinstance(name, str) or not name.strip():
            raise UsageError(f"Preset {filename!r} ship check {index} needs a name")
        if name.strip() in seen:
            raise UsageError(f"Preset {filename!r} duplicate ship check {name.strip()!r}")
        seen.add(name.strip())
        suggested = item.get("suggested", True)
        if not isinstance(suggested, bool):
            raise UsageError(
                f"Preset {filename!r} ship check {name.strip()!r} suggested must be a boolean"
            )
        checks.append(
            SurfaceCheck(
                name=name.strip(),
                globs=_globs(item.get("globs"), label=f"ship check {name.strip()} globs"),
                run=_argv(item.get("run"), label=f"ship check {name.strip()} run"),
                suggested=suggested,
            )
        )
    return tuple(checks)


def _table(value: object, *, label: str) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise UsageError(f"{label} must be a table")
    return value


def _globs(value: object, *, label: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        raise UsageError(f"{label} must be a list of glob strings")
    return tuple(item.strip() for item in value)


def _argv(value: object, *, label: str) -> tuple[str, ...]:
    if (
        not isinstance(value, list)
        or not value
        or any(not isinstance(part, str) or part == "" for part in value)
    ):
        raise UsageError(f"{label} must be a non-empty list of strings")
    return tuple(value)


def _note_subject(value: object, *, default: str) -> str:
    if value is None:
        return default
    if not isinstance(value, str) or not value.strip():
        raise UsageError("note_subject must be a non-empty string")
    return value.strip()


def _packaged_names() -> list[str]:
    names: list[str] = []
    for entry in files(_PACKAGE).iterdir():
        filename = entry.name
        if filename.endswith(".toml"):
            names.append(filename[: -len(".toml")])
    return sorted(names)


def _unknown_preset(name: object) -> str:
    available = ", ".join(_packaged_names()) or "(none)"
    shown = name if isinstance(name, str) else repr(name)
    return f"Unknown preset {shown!r}. Available presets: {available}"


def _suggestion_comments(checks: list[SurfaceCheck], *, ai_run: tuple[str, ...]) -> str:
    lines = [
        "# Suggested commands. verify uses these argv values when the matching",
        "# paths are part of the Change and [[surfaces.ship.checks]] is omitted.",
        "# Uncomment the ship tables to replace the packaged defaults entirely.",
        "# Structural checks only: not a plan review, and not an AppSec audit.",
        "# Eval quality is the team's job; verify only requires the command ran.",
    ]
    if ai_run:
        rendered = " ".join(ai_run)
        lines.append(f"# AI eval default (also set as surfaces.ai.run): {rendered}")
    for check in checks:
        lines.append("#")
        lines.append("# [[surfaces.ship.checks]]")
        lines.append(f"# name = {json.dumps(check.name)}")
        globs = ", ".join(json.dumps(glob) for glob in check.globs)
        lines.append(f"# globs = [{globs}]")
        run = ", ".join(json.dumps(part) for part in check.run)
        lines.append(f"# run = [{run}]")
    lines.append("")
    return "\n".join(lines) + "\n"
