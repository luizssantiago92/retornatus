"""Mechanical gates with non-zero exit semantics (software construction brakes)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from retornatus.application.assurance.evaluate import Claim, AssuranceVerdict, evaluate_assurance
from retornatus.infrastructure.persistence.repository import FileRepository


class GateName(str, Enum):
    CONTRACT = "contract"
    EVIDENCE = "evidence"
    SKILL_RESEARCH = "skill-research"
    ASSURANCE = "assurance"


@dataclass
class GateResult:
    name: GateName
    passed: bool
    messages: list[str] = field(default_factory=list)

    @property
    def exit_code(self) -> int:
        return 0 if self.passed else 1


def gate_contract(root: Path, change_id: str) -> GateResult:
    """Active Contract must exist with WHAT and at least one DONE criterion."""
    repo = FileRepository(root)
    messages: list[str] = []
    try:
        contract, _ = repo.load_contract(change_id)
    except FileNotFoundError:
        return GateResult(
            GateName.CONTRACT,
            False,
            [f"No contract.json for {change_id}"],
        )
    if not contract.active:
        messages.append("Contract is not active")
    if not contract.what.strip():
        messages.append("Contract WHAT is empty")
    if not contract.done_criteria:
        messages.append("Contract has no DONE criteria")
    return GateResult(GateName.CONTRACT, not messages, messages or ["Contract OK"])


def gate_evidence(root: Path, change_id: str) -> GateResult:
    """At least one Evidence artifact must exist for the Change."""
    repo = FileRepository(root)
    evidence_dir = repo.paths.change_dir(change_id) / "evidence"
    if not evidence_dir.is_dir() or not list(evidence_dir.glob("E-*.json")):
        return GateResult(
            GateName.EVIDENCE,
            False,
            [f"No evidence under {evidence_dir}"],
        )
    return GateResult(GateName.EVIDENCE, True, ["Evidence present"])


def gate_skill_research(root: Path, skill_id: str) -> GateResult:
    """
    Skill RESEARCH section must not still be an empty scaffold.

    Physical enforcement of on-demand specialization: research before ACTIVE use.
    """
    repo = FileRepository(root)
    try:
        _skill, body, _ = repo.load_skill(skill_id)
    except FileNotFoundError:
        return GateResult(GateName.SKILL_RESEARCH, False, [f"Skill not found: {skill_id}"])

    messages: list[str] = []
    has_url = "http://" in body.lower() or "https://" in body.lower()
    if not has_url:
        messages.append("RESEARCH has no source URLs — agent must research current docs first")

    # Blank procedure: numbered list with empty items only
    if re.search(r"## PROCEDURE[\s\S]*?\n1\.\s*\n2\.\s*\n3\.\s*\n", body):
        messages.append("PROCEDURE steps still blank")

    if messages:
        return GateResult(GateName.SKILL_RESEARCH, False, messages)
    return GateResult(GateName.SKILL_RESEARCH, True, ["Skill research/procedure looks filled"])


def gate_assurance(root: Path, change_id: str) -> GateResult:
    """Assurance must be SATISFIED for Contract DONE criteria."""
    repo = FileRepository(root)
    try:
        contract, _ = repo.load_contract(change_id)
    except FileNotFoundError:
        return GateResult(GateName.ASSURANCE, False, ["No contract"])

    evidence_pairs: list[tuple[str, str]] = []
    evidence_dir = repo.paths.change_dir(change_id) / "evidence"
    if evidence_dir.is_dir():
        for p in evidence_dir.glob("E-*.json"):
            ev, _ = repo.load_evidence(f"{change_id}/{p.stem}")
            evidence_pairs.append((ev.id, ev.type))

    claims = [
        Claim(
            id=f"done-{i}",
            statement=crit,
            required_evidence_types=["test_result", "human_decision", "build_result"],
        )
        for i, crit in enumerate(contract.done_criteria, start=1)
    ]
    result = evaluate_assurance(claims=claims, evidence=evidence_pairs)
    ok = result.verdict is AssuranceVerdict.SATISFIED
    return GateResult(
        GateName.ASSURANCE,
        ok,
        [f"Verdict={result.verdict.value}: {result.rationale}"],
    )
