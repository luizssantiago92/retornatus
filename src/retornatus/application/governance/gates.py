"""Mechanical gates with non-zero exit semantics (software construction brakes)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from retornatus.application.assurance.evaluate import (
    AssuranceVerdict,
    build_claims_from_contract,
    evaluate_assurance,
)
from retornatus.infrastructure.persistence.repository import FileRepository


class GateName(str, Enum):
    CONTRACT = "contract"
    EVIDENCE = "evidence"
    SKILL_RESEARCH = "skill-research"
    ASSURANCE = "assurance"
    POLICY = "policy"


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
    else:
        weak = [
            c
            for c in contract.done_criteria
            if len(c.strip()) < 8 or c.strip().lower() in {"done", "ok", "works"}
        ]
        if weak:
            messages.append("DONE criteria are too weak to establish satisfaction")
    return GateResult(GateName.CONTRACT, not messages, messages or ["Contract OK"])


def gate_evidence(root: Path, change_id: str) -> GateResult:
    """
    Evidence artifacts must exist AND be structurally attributable
    (type + subject + producer/source present — not empty placeholders).
    """
    repo = FileRepository(root)
    evidence_dir = repo.paths.change_dir(change_id) / "evidence"
    if not evidence_dir.is_dir() or not list(evidence_dir.glob("E-*.json")):
        return GateResult(
            GateName.EVIDENCE,
            False,
            [f"No evidence under {evidence_dir}"],
        )
    messages: list[str] = []
    valid = 0
    for path in evidence_dir.glob("E-*.json"):
        ev, _ = repo.load_evidence(f"{change_id}/{path.stem}")
        if not ev.type.strip() or not ev.subject.strip():
            messages.append(f"{ev.id}: missing type/subject")
            continue
        if not ev.source.strip() or not ev.producer.strip():
            messages.append(f"{ev.id}: missing source/producer")
            continue
        valid += 1
    if valid == 0:
        messages.append("No valid attributable Evidence artifacts")
        return GateResult(GateName.EVIDENCE, False, messages)
    return GateResult(
        GateName.EVIDENCE,
        True,
        messages or [f"Evidence present ({valid} valid artifact(s))"],
    )


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


def gate_assurance(
    root: Path,
    change_id: str,
    *,
    current_subject_states: dict[str, str] | None = None,
    use_git_state: bool = True,
) -> GateResult:
    """Assurance must be SATISFIED for Contract DONE Claims with bound Evidence."""
    from retornatus.application.assurance.evidence import EvidenceService
    from retornatus.application.assurance.independent import evaluate_change_assurance

    repo = FileRepository(root)
    try:
        contract, _ = repo.load_contract(change_id)
    except FileNotFoundError:
        return GateResult(GateName.ASSURANCE, False, ["No contract"])

    if not contract.active:
        return GateResult(GateName.ASSURANCE, False, ["Contract is not active"])
    if not contract.done_criteria:
        return GateResult(GateName.ASSURANCE, False, ["Contract has no DONE criteria"])

    if current_subject_states is not None:
        claims = build_claims_from_contract(contract)
        evidence = EvidenceService(root).list_for_change(change_id)
        result = evaluate_assurance(
            claims=claims,
            evidence=evidence,
            current_subject_states=current_subject_states,
        )
    else:
        result = evaluate_change_assurance(
            root, change_id, use_git_state=use_git_state
        )
    ok = result.verdict is AssuranceVerdict.SATISFIED
    detail = [
        f"Verdict={result.verdict.value}: {result.rationale}",
    ]
    for claim_id, status in result.claim_results.items():
        detail.append(f"  {claim_id}: {status}")
    return GateResult(GateName.ASSURANCE, ok, detail)


def gate_policy(root: Path, action_id: str) -> GateResult:
    """Policy must ALLOW the Action objective (DENY / REQUIRE_HUMAN = STOP)."""
    from retornatus.application.governance.policy import (
        PolicyVerdict,
        evaluate_action_policy,
    )

    try:
        decision = evaluate_action_policy(root, action_id)
    except FileNotFoundError:
        return GateResult(
            GateName.POLICY,
            False,
            [f"Action not found: {action_id}"],
        )
    ok = decision.verdict is PolicyVerdict.ALLOW
    messages = [
        f"Verdict={decision.verdict.value}: {decision.rationale}",
    ]
    if decision.matched_rule_ids:
        messages.append("matched_rules: " + ", ".join(decision.matched_rule_ids))
    return GateResult(GateName.POLICY, ok, messages)
