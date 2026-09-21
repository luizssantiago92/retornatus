"""Independent Assurance — fresh context + review Evidence when required.

Specialization comes from Assignment + Context + Skills — not ReviewerAgent.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from retornatus.application.assurance.evaluate import (
    AssuranceResult,
    Claim,
    build_claims_from_contract,
    evaluate_assurance,
    infer_required_evidence_types,
)
from retornatus.application.assurance.evidence import EvidenceService
from retornatus.application.assurance.subject_state import (
    capture_subject_state,
    derive_current_subject_states,
)
from retornatus.application.execution.context import (
    ExecutionContext,
    assemble_assurance_context,
)
from retornatus.infrastructure.persistence.repository import FileRepository


@dataclass
class IndependentReviewPlan:
    """Projection: whether independent Assurance Execution is required."""

    required: bool
    rationale: str
    claims_needing_review: list[str] = field(default_factory=list)
    action_id: str | None = None
    execution_context: ExecutionContext | None = None


def claims_requiring_independent_review(claims: list[Claim]) -> list[Claim]:
    """Claims whose proportional Evidence includes review/security judgment."""
    needed: list[Claim] = []
    for claim in claims:
        types = set(claim.required_evidence_types) or set(
            infer_required_evidence_types(claim.statement)
        )
        if types & {"review_result", "security_test"}:
            needed.append(claim)
            continue
        stmt = claim.statement.lower()
        if any(w in stmt for w in ("independent", "review", "security", "unauthorized")):
            needed.append(claim)
    return needed


def plan_independent_assurance(
    root: Path,
    change_id: str,
    *,
    action_id: str | None = None,
) -> IndependentReviewPlan:
    """
    Determine whether Assurance needs a fresh independent Execution.

    Does not invent a ReviewerAgent — returns a plan + optional fresh context.
    """
    repo = FileRepository(root)
    contract, _ = repo.load_contract(change_id)
    claims = build_claims_from_contract(contract)
    needing = claims_requiring_independent_review(claims)

    resolved_action = action_id
    if resolved_action is None:
        actions_dir = repo.paths.change_dir(change_id) / "actions"
        if actions_dir.is_dir():
            paths = sorted(actions_dir.glob("A-*.json"))
            if paths:
                resolved_action = f"{change_id}/{paths[0].stem}"

    if not needing:
        return IndependentReviewPlan(
            required=False,
            rationale="No Claim requires independent review or security Evidence",
            action_id=resolved_action,
        )

    ctx = None
    if resolved_action:
        ctx = assemble_assurance_context(root, resolved_action)

    return IndependentReviewPlan(
        required=True,
        rationale=(
            "Independent Assurance required for claims: "
            + ", ".join(c.id for c in needing)
        ),
        claims_needing_review=[c.id for c in needing],
        action_id=resolved_action,
        execution_context=ctx,
    )


def record_independent_review_evidence(
    root: Path,
    *,
    change_id: str,
    claim_id: str,
    subject: str,
    summary: str,
    producer: str = "independent-assurance",
    verdict: str = "approved",
    use_git_state: bool = True,
) -> str:
    """
    Record review_result Evidence from an independent Assurance Execution.

    Host/Environment performs the review; Retornatus records attributable Evidence.
    """
    state = capture_subject_state(root, use_git=use_git_state)
    if state:
        subject_state = f"{state}|review:{verdict}"
    else:
        subject_state = f"review:{verdict}"

    ev = EvidenceService(root).add(
        change_id=change_id,
        evidence_type="review_result",
        subject=subject,
        source="independent_assurance",
        producer=f"{producer}:{summary[:80]}",
        subject_state=subject_state,
        supports_claim_id=claim_id,
    )
    return ev.id


def evaluate_change_assurance(
    root: Path,
    change_id: str,
    *,
    use_git_state: bool = True,
) -> AssuranceResult:
    """Evaluate Contract Claims with derived subject states when possible."""
    repo = FileRepository(root)
    contract, _ = repo.load_contract(change_id)
    claims = build_claims_from_contract(contract)
    evidence = EvidenceService(root).list_for_change(change_id)
    current_states = (
        derive_current_subject_states(root, evidence) if use_git_state else {}
    )
    return evaluate_assurance(
        claims=claims,
        evidence=evidence,
        current_subject_states=current_states or None,
    )
