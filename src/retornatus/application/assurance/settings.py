"""Project-level assurance settings from ``.retornatus/config.toml``."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RequiredCheck:
    """One owner-declared command that may satisfy execution-type claims.

    ``types`` empty means the argv applies to every execution evidence type.
    Otherwise the argv satisfies only those claim/evidence types.
    """

    name: str
    run: tuple[str, ...]
    types: frozenset[str]


def load_project_config(root: Path) -> dict[str, Any]:
    """Return config.toml as a dict, or ``{}`` when it cannot be read."""
    from retornatus.infrastructure.persistence.repository import FileRepository

    try:
        data, _ = FileRepository(root).load_config()
    except (OSError, FileNotFoundError, ValueError):
        return {}
    if not isinstance(data, dict):
        return {}
    return data


def allow_self_reported_enabled(root: Path) -> bool:
    """True only when ``[assurance] allow_self_reported`` is boolean true.

    Missing config, a missing key, or any other value keeps the strict default:
    self-reported execution evidence does not satisfy Claims.
    """
    assurance = _assurance_table(root)
    return assurance.get("allow_self_reported") is True


def uncommitted_changes_mode(root: Path) -> str:
    """``fail``, ``warn``, or ``default``.

    ``default`` fails execution-type claims and warns for narrative evidence.
    """
    assurance = _assurance_table(root)
    raw = assurance.get("uncommitted_changes")
    if raw is None:
        return "default"
    if raw not in {"fail", "warn"}:
        raise ValueError(
            "Invalid [assurance] uncommitted_changes: expected \"fail\" or \"warn\""
        )
    return str(raw)


def load_required_checks(root: Path) -> list[RequiredCheck]:
    """Parse ``[assurance] required_checks``. Missing key → no extra constraint."""
    assurance = _assurance_table(root)
    raw = assurance.get("required_checks")
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise ValueError(
            "Invalid required_checks: expected a list of {name, run, types?}"
        )
    checks: list[RequiredCheck] = []
    seen: set[str] = set()
    for index, item in enumerate(raw):
        checks.append(_parse_check(item, index=index))
        if checks[-1].name in seen:
            raise ValueError(
                f"Invalid required_checks: duplicate name {checks[-1].name!r}"
            )
        seen.add(checks[-1].name)
    return checks


def _assurance_table(root: Path) -> dict[str, Any]:
    assurance = load_project_config(root).get("assurance")
    if assurance is None:
        return {}
    if not isinstance(assurance, dict):
        raise ValueError("Invalid [assurance]: expected a table")
    return assurance


def _parse_check(item: object, *, index: int) -> RequiredCheck:
    if not isinstance(item, dict):
        raise ValueError(
            f"Invalid required_checks[{index}]: expected a table with name and run"
        )
    name = item.get("name")
    if not isinstance(name, str) or not name.strip():
        raise ValueError(f"Invalid required_checks[{index}]: name must be a string")
    run = item.get("run")
    if (
        not isinstance(run, list)
        or not run
        or any(not isinstance(part, str) or part == "" for part in run)
    ):
        raise ValueError(
            f"Invalid required_checks[{index}] ({name}): "
            "run must be a non-empty list of strings"
        )
    types_raw = item.get("types", item.get("claim_types", []))
    if types_raw is None:
        types_raw = []
    if not isinstance(types_raw, list) or any(not isinstance(t, str) or not t.strip() for t in types_raw):
        raise ValueError(
            f"Invalid required_checks[{index}] ({name}): "
            "types must be a list of evidence type strings"
        )
    from retornatus.application.assurance.evaluate import EXECUTION_EVIDENCE_TYPES

    types = frozenset(t.strip() for t in types_raw)
    unknown = sorted(types - EXECUTION_EVIDENCE_TYPES)
    if unknown:
        raise ValueError(
            f"Invalid required_checks[{index}] ({name}): "
            f"types {unknown} are not execution evidence types "
            f"({', '.join(sorted(EXECUTION_EVIDENCE_TYPES))})"
        )
    return RequiredCheck(name=name.strip(), run=tuple(run), types=types)
