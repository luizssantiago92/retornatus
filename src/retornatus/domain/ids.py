"""Identifier types and allocation helpers (PRD §51)."""

from __future__ import annotations

import re
from typing import Annotated

from pydantic import AfterValidator, StringConstraints

# Project-level: L-0001, R-0001, D-0001, S-0001 (Skill)
_PROJECT_ID = re.compile(r"^(?P<prefix>[LRDS])-(?P<num>\d{4,})$")
# Change: C-0001
_CHANGE_ID = re.compile(r"^C-(?P<num>\d{4,})$")
# Change-owned: C-0001/A-001, C-0001/T-001, ...
_OWNED_ID = re.compile(
    r"^(?P<change>C-\d{4,})/(?P<kind>[ATFQE])-(?P<num>\d{3,})$"
)

_StrictStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


def _validate_project_id(value: str, *, allowed: frozenset[str], label: str) -> str:
    match = _PROJECT_ID.fullmatch(value)
    if match is None or match.group("prefix") not in allowed:
        raise ValueError(f"Invalid {label} id: {value!r}")
    return value


def _validate_change_id(value: str) -> str:
    if _CHANGE_ID.fullmatch(value) is None:
        raise ValueError(f"Invalid Change id: {value!r}")
    return value


def _validate_owned_id(value: str, *, kind: str, label: str) -> str:
    match = _OWNED_ID.fullmatch(value)
    if match is None or match.group("kind") != kind:
        raise ValueError(f"Invalid {label} id: {value!r}")
    return value


def validate_learning_id(value: str) -> str:
    return _validate_project_id(value, allowed=frozenset({"L"}), label="Learning")


def validate_rule_id(value: str) -> str:
    return _validate_project_id(value, allowed=frozenset({"R"}), label="Rule")


def validate_decision_id(value: str) -> str:
    return _validate_project_id(value, allowed=frozenset({"D"}), label="Decision")


def validate_skill_id(value: str) -> str:
    return _validate_project_id(value, allowed=frozenset({"S"}), label="Skill")


def validate_change_id(value: str) -> str:
    return _validate_change_id(value)


def validate_action_id(value: str) -> str:
    return _validate_owned_id(value, kind="A", label="Action")


def validate_task_id(value: str) -> str:
    return _validate_owned_id(value, kind="T", label="Task")


def validate_finding_id(value: str) -> str:
    return _validate_owned_id(value, kind="F", label="Finding")


def validate_question_id(value: str) -> str:
    return _validate_owned_id(value, kind="Q", label="Question")


def validate_evidence_id(value: str) -> str:
    return _validate_owned_id(value, kind="E", label="Evidence")


LearningId = Annotated[_StrictStr, AfterValidator(validate_learning_id)]
RuleId = Annotated[_StrictStr, AfterValidator(validate_rule_id)]
DecisionId = Annotated[_StrictStr, AfterValidator(validate_decision_id)]
SkillId = Annotated[_StrictStr, AfterValidator(validate_skill_id)]
ChangeId = Annotated[_StrictStr, AfterValidator(validate_change_id)]
ActionId = Annotated[_StrictStr, AfterValidator(validate_action_id)]
TaskId = Annotated[_StrictStr, AfterValidator(validate_task_id)]
FindingId = Annotated[_StrictStr, AfterValidator(validate_finding_id)]
QuestionId = Annotated[_StrictStr, AfterValidator(validate_question_id)]
EvidenceId = Annotated[_StrictStr, AfterValidator(validate_evidence_id)]


def change_id_of(owned_id: str) -> str:
    """Extract ``C-NNNN`` from a Change-owned identifier."""
    match = _OWNED_ID.fullmatch(owned_id)
    if match is None:
        raise ValueError(f"Not a Change-owned id: {owned_id!r}")
    return match.group("change")


def format_project_id(prefix: str, number: int) -> str:
    if prefix not in {"L", "R", "D", "S"}:
        raise ValueError(f"Unsupported project id prefix: {prefix!r}")
    if number < 1:
        raise ValueError("Identifier number must be >= 1")
    return f"{prefix}-{number:04d}"


def format_change_id(number: int) -> str:
    if number < 1:
        raise ValueError("Identifier number must be >= 1")
    return f"C-{number:04d}"


def format_owned_id(change_id: str, kind: str, number: int) -> str:
    validate_change_id(change_id)
    if kind not in {"A", "T", "F", "Q", "E"}:
        raise ValueError(f"Unsupported owned id kind: {kind!r}")
    if number < 1:
        raise ValueError("Identifier number must be >= 1")
    return f"{change_id}/{kind}-{number:03d}"
