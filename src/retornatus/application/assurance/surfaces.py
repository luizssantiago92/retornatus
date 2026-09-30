"""Path-triggered ship and AI evidence rules for ``verify``.

Rules live in ``[surfaces]`` (written by the ``python-platform`` preset and
presets that extend it). When no changed or Task-scoped path matches, the
rule is ``not required``. Matching paths require executed evidence of the
configured command plus a narrative note. A packaged check with
``optional = true`` covers its paths and still requires the note, but it
does not require the command. This is a structural check, not a plan review
or an eval grade.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from retornatus.application.assurance.evaluate import (
    EXECUTION_EVIDENCE_TYPES,
    AssuranceResult,
    AssuranceVerdict,
)
from retornatus.application.assurance.settings import load_project_config
from retornatus.application.governance.diff import changed_paths, git_available
from retornatus.application.governance.globs import glob_match
from retornatus.application.governance.scope import change_resources
from retornatus.bootstrap.presets import SurfaceCheck, resolve_preset
from retornatus.domain.enums import EvidenceProvenance
from retornatus.domain.errors import UsageError
from retornatus.domain.models import Evidence

_PLACEHOLDERS = frozenset(
    {
        "",
        "—",
        "-",
        "n/a",
        "na",
        "none",
        "tbd",
        "todo",
        "(fill in)",
        "(fill me)",
    }
)


@dataclass(frozen=True)
class SurfaceSettings:
    """Effective ship and AI rules for one project."""

    ship_globs: tuple[str, ...]
    ship_note_subject: str
    ship_checks: tuple[SurfaceCheck, ...]
    ai_globs: tuple[str, ...]
    ai_note_subject: str
    ai_run: tuple[str, ...]


def load_surface_settings(root: Path) -> SurfaceSettings | None:
    """Return surface rules, or ``None`` when ``[surfaces]`` is absent.

    Omitted ``[[surfaces.ship.checks]]`` uses the packaged checks of
    ``[project].preset``. A present ``checks`` list replaces those defaults.
    """
    config = load_project_config(root)
    surfaces = config.get("surfaces")
    if surfaces is None:
        return None
    if not isinstance(surfaces, dict):
        raise ValueError("Invalid [surfaces]: expected a table")
    project = config.get("project")
    preset_name = ""
    if isinstance(project, dict) and isinstance(project.get("preset"), str):
        preset_name = project["preset"].strip()
    packaged_ship: tuple[SurfaceCheck, ...] = ()
    packaged_ai: tuple[str, ...] = ()
    if preset_name:
        try:
            packaged = resolve_preset(preset_name)
        except UsageError as exc:
            raise ValueError(f"Invalid [project].preset: {exc}") from exc
        packaged_ship = packaged.ship_checks
        packaged_ai = packaged.ai_run
    ship = _section(surfaces, "ship")
    ai = _section(surfaces, "ai")
    ship_checks = packaged_ship
    if "checks" in ship:
        ship_checks = _parse_checks(ship.get("checks"))
    ai_run = packaged_ai
    if "run" in ai:
        ai_run = _parse_argv(ai.get("run"), label="surfaces.ai.run")
    return SurfaceSettings(
        ship_globs=_parse_globs(ship.get("globs"), label="surfaces.ship.globs"),
        ship_note_subject=_parse_subject(ship.get("note_subject"), default="ship rollback"),
        ship_checks=ship_checks,
        ai_globs=_parse_globs(ai.get("globs"), label="surfaces.ai.globs"),
        ai_note_subject=_parse_subject(ai.get("note_subject"), default="ai fallback"),
        ai_run=ai_run,
    )


def collect_surface_paths(root: Path, change_id: str) -> list[str]:
    """Task resources plus git worktree changes, de-duplicated."""
    ordered: list[str] = []
    seen: set[str] = set()
    for path in change_resources(root, change_id):
        _add_path(ordered, seen, path)
    if git_available(root):
        for path in changed_paths(root):
            _add_path(ordered, seen, path)
    return ordered


def evaluate_surface_rules(
    *,
    paths: list[str],
    evidence: list[Evidence],
    settings: SurfaceSettings,
) -> list[dict[str, Any]]:
    """Ship and AI rule documents for the verdict envelope."""
    return [
        _ship_rule(paths, evidence, settings),
        _ai_rule(paths, evidence, settings),
    ]


def apply_surface_rules(
    root: Path,
    change_id: str,
    result: AssuranceResult,
    evidence: list[Evidence],
) -> AssuranceResult:
    """Attach surface status and fail the verdict when a required rule is unmet."""
    settings = load_surface_settings(root)
    if settings is None:
        return result
    rules = evaluate_surface_rules(
        paths=collect_surface_paths(root, change_id),
        evidence=evidence,
        settings=settings,
    )
    unmet = [rule for rule in rules if rule["status"] == "unsatisfied"]
    warnings = list(result.warnings)
    for rule in unmet:
        warnings.append(f"surface {rule['name']}: " + "; ".join(rule["missing"]))
    if not unmet:
        return result.model_copy(update={"surfaces": rules, "warnings": warnings})
    detail = "Surface requirements unmet: " + " | ".join(
        f"{rule['name']}: {'; '.join(rule['missing'])}" for rule in unmet
    )
    rationale = (
        detail
        if result.verdict is AssuranceVerdict.SATISFIED
        else f"{detail}. {result.rationale}"
    )
    verdict = result.verdict
    if verdict is AssuranceVerdict.SATISFIED or verdict is AssuranceVerdict.INCONCLUSIVE:
        verdict = AssuranceVerdict.NOT_SATISFIED
    return result.model_copy(
        update={
            "surfaces": rules,
            "warnings": warnings,
            "verdict": verdict,
            "rationale": rationale,
        }
    )


def _ship_rule(
    paths: list[str],
    evidence: list[Evidence],
    settings: SurfaceSettings,
) -> dict[str, Any]:
    matched = _matching(paths, settings.ship_globs)
    if not matched:
        return _document("ship", "not required", [], [], [])
    missing: list[str] = []
    required: list[str] = []
    covered: set[str] = set()
    for check in settings.ship_checks:
        hits = _matching(matched, check.globs)
        if not hits:
            continue
        covered.update(hits)
        if check.optional:
            continue
        label = f"{check.name}: {' '.join(check.run)}"
        required.append(label)
        if not _executed(evidence, check.run):
            missing.append(f"executed check {label}")
    for path in matched:
        if path not in covered:
            missing.append(f"no ship check covers {path}")
    if not _note(evidence, settings.ship_note_subject):
        missing.append(f"rollback note (subject {settings.ship_note_subject!r})")
    status = "satisfied" if not missing else "unsatisfied"
    return _document("ship", status, matched, required, missing)


def _ai_rule(
    paths: list[str],
    evidence: list[Evidence],
    settings: SurfaceSettings,
) -> dict[str, Any]:
    matched = _matching(paths, settings.ai_globs)
    if not matched:
        return _document("ai", "not required", [], [], [])
    missing: list[str] = []
    required: list[str] = []
    if not settings.ai_run:
        missing.append("eval command is not configured")
    else:
        label = " ".join(settings.ai_run)
        required.append(label)
        if not _executed(evidence, settings.ai_run):
            missing.append(f"executed eval: {label}")
    if not _note(evidence, settings.ai_note_subject):
        missing.append(f"fallback note (subject {settings.ai_note_subject!r})")
    status = "satisfied" if not missing else "unsatisfied"
    return _document("ai", status, matched, required, missing)


def _document(
    name: str,
    status: str,
    matched: list[str],
    required: list[str],
    missing: list[str],
) -> dict[str, Any]:
    return {
        "name": name,
        "status": status,
        "matched_paths": list(matched),
        "required_checks": list(required),
        "missing": list(missing),
    }


def _matching(paths: list[str], globs: tuple[str, ...]) -> list[str]:
    if not globs:
        return []
    return [path for path in paths if any(glob_match(path, pattern) for pattern in globs)]


def _executed(evidence: list[Evidence], run: tuple[str, ...]) -> bool:
    target = list(run)
    for item in evidence:
        if item.provenance is not EvidenceProvenance.EXECUTED:
            continue
        if item.timed_out or item.exit_code != 0:
            continue
        if list(item.command or []) == target:
            return True
    return False


def _note(evidence: list[Evidence], subject: str) -> bool:
    want = subject.strip().casefold()
    if not want:
        return False
    for item in evidence:
        if item.type in EXECUTION_EVIDENCE_TYPES:
            continue
        if item.subject.strip().casefold() != want:
            continue
        if _placeholder(item.source):
            continue
        return True
    return False


def _placeholder(value: str) -> bool:
    cleaned = value.strip().strip("`").casefold()
    if cleaned in _PLACEHOLDERS:
        return True
    return cleaned.startswith("(fill")


def _section(surfaces: dict[str, Any], name: str) -> dict[str, Any]:
    raw = surfaces.get(name)
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise ValueError(f"Invalid [surfaces.{name}]: expected a table")
    return raw


def _parse_globs(value: object, *, label: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        raise ValueError(f"Invalid {label}: expected a list of glob strings")
    return tuple(item.strip() for item in value)


def _parse_argv(value: object, *, label: str) -> tuple[str, ...]:
    if (
        not isinstance(value, list)
        or not value
        or any(not isinstance(part, str) or part == "" for part in value)
    ):
        raise ValueError(f"Invalid {label}: expected a non-empty list of strings")
    return tuple(value)


def _parse_subject(value: object, *, default: str) -> str:
    if value is None:
        return default
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Invalid note_subject: expected a non-empty string")
    return value.strip()


def _parse_checks(value: object) -> tuple[SurfaceCheck, ...]:
    if not isinstance(value, list):
        raise ValueError("Invalid surfaces.ship.checks: expected a list of tables")
    checks: list[SurfaceCheck] = []
    seen: set[str] = set()
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise ValueError(f"Invalid surfaces.ship.checks[{index}]: expected a table")
        name = item.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"Invalid surfaces.ship.checks[{index}]: name must be a string")
        cleaned = name.strip()
        if cleaned in seen:
            raise ValueError(f"Invalid surfaces.ship.checks: duplicate name {cleaned!r}")
        seen.add(cleaned)
        optional = item.get("optional", False)
        if not isinstance(optional, bool):
            raise ValueError(
                f"Invalid surfaces.ship.checks[{index}]: optional must be a boolean"
            )
        checks.append(
            SurfaceCheck(
                name=cleaned,
                globs=_parse_globs(item.get("globs"), label=f"surfaces.ship.checks[{index}].globs"),
                run=_parse_argv(item.get("run"), label=f"surfaces.ship.checks[{index}].run"),
                suggested=False,
                optional=optional,
            )
        )
    return tuple(checks)


def _add_path(ordered: list[str], seen: set[str], path: str) -> None:
    text = path.replace("\\", "/").strip()
    while text.startswith("./"):
        text = text[2:]
    if not text or text in seen:
        return
    seen.add(text)
    ordered.append(text)
