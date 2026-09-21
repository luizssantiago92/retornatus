"""Assurance verdicts and evaluation (PRD §24 / M6)."""

from __future__ import annotations

from enum import Enum

from pydantic import Field

from retornatus.domain.base import DomainModel
from retornatus.domain.ids import EvidenceId
from retornatus.domain.relations import Relation, RelationType


class AssuranceVerdict(str, Enum):
    SATISFIED = "SATISFIED"
    NOT_SATISFIED = "NOT_SATISFIED"
    INCONCLUSIVE = "INCONCLUSIVE"


class Claim(DomainModel):
    """A claim that Assurance must evaluate."""

    id: str = Field(min_length=1)
    statement: str = Field(min_length=1)
    required_evidence_types: list[str] = Field(default_factory=list)


class AssuranceResult(DomainModel):
    """Outcome of Assurance evaluation."""

    verdict: AssuranceVerdict
    claims: list[Claim] = Field(default_factory=list)
    evidence_ids: list[EvidenceId] = Field(default_factory=list)
    rationale: str = Field(min_length=1)
    relations: list[Relation] = Field(default_factory=list)


def evaluate_assurance(
    *,
    claims: list[Claim],
    evidence: list[tuple[str, str]],  # (evidence_id, evidence_type)
) -> AssuranceResult:
    """
    Deterministic Assurance: each claim needs at least one matching evidence type.

    Missing capability/evidence → INCONCLUSIVE (PRD §24).
    """
    if not claims:
        return AssuranceResult(
            verdict=AssuranceVerdict.INCONCLUSIVE,
            rationale="No claims provided",
            evidence_ids=[e[0] for e in evidence],
        )

    types_present = {t for _, t in evidence}
    evidence_ids = [eid for eid, _ in evidence]
    unmet: list[str] = []
    inconclusive: list[str] = []

    for claim in claims:
        if not claim.required_evidence_types:
            inconclusive.append(claim.id)
            continue
        if any(req in types_present for req in claim.required_evidence_types):
            continue
        if not evidence:
            inconclusive.append(claim.id)
        else:
            unmet.append(claim.id)

    if unmet:
        verdict = AssuranceVerdict.NOT_SATISFIED
        rationale = f"Unmet claims: {', '.join(unmet)}"
    elif inconclusive:
        verdict = AssuranceVerdict.INCONCLUSIVE
        rationale = f"Insufficient evidence for claims: {', '.join(inconclusive)}"
    else:
        verdict = AssuranceVerdict.SATISFIED
        rationale = "All claims have matching attributable evidence"

    return AssuranceResult(
        verdict=verdict,
        claims=claims,
        evidence_ids=evidence_ids,
        rationale=rationale,
        relations=[
            Relation(type=RelationType.SUPPORTS, target_id=eid) for eid in evidence_ids
        ],
    )
