"""Assurance verdicts and claim↔evidence evaluation (PRD §23–§24 / M6)."""

from __future__ import annotations

import re
from enum import Enum

from pydantic import Field

from retornatus.domain.base import DomainModel
from retornatus.domain.ids import EvidenceId
from retornatus.domain.models import Contract, Evidence
from retornatus.domain.relations import Relation, RelationType


class AssuranceVerdict(str, Enum):
    SATISFIED = "SATISFIED"
    NOT_SATISFIED = "NOT_SATISFIED"
    INCONCLUSIVE = "INCONCLUSIVE"


class Claim(DomainModel):
    """A claim that Assurance must evaluate — bound to required Evidence."""

    id: str = Field(min_length=1)
    statement: str = Field(min_length=1)
    required_evidence_types: list[str] = Field(default_factory=list)
    subject: str | None = None


class AssuranceResult(DomainModel):
    """Outcome of Assurance evaluation."""

    verdict: AssuranceVerdict
    claims: list[Claim] = Field(default_factory=list)
    evidence_ids: list[EvidenceId] = Field(default_factory=list)
    rationale: str = Field(min_length=1)
    relations: list[Relation] = Field(default_factory=list)
    claim_results: dict[str, str] = Field(default_factory=dict)


_DOC_MARKERS = re.compile(r"\b(document|documented|docs|readme|openapi|spec)\b", re.I)
_TEST_MARKERS = re.compile(
    r"\b(test|pytest|automated|returns|endpoint|behavior|health|integration)\b",
    re.I,
)
_SECURITY_MARKERS = re.compile(
    r"\b(security|unauthorized|authn|authz|permission|secret)\b", re.I
)
_REVIEW_MARKERS = re.compile(r"\b(review|human approval|manual check)\b", re.I)
_BUILD_MARKERS = re.compile(r"\b(build|compile|package)\b", re.I)


def infer_required_evidence_types(criterion: str) -> list[str]:
    """
    Proportional required Evidence types for a DONE criterion.

    human_decision is never a universal substitute for test_result.
    """
    types: list[str] = []
    if _SECURITY_MARKERS.search(criterion):
        types.append("security_test")
    if _TEST_MARKERS.search(criterion):
        types.append("test_result")
    if _DOC_MARKERS.search(criterion):
        types.append("repository_observation")
    if _REVIEW_MARKERS.search(criterion):
        types.append("review_result")
    if _BUILD_MARKERS.search(criterion):
        types.append("build_result")
    if not types:
        # Software construction default: behavioral proof
        types.append("test_result")
    # Deduplicate preserving order
    seen: set[str] = set()
    ordered: list[str] = []
    for t in types:
        if t not in seen:
            seen.add(t)
            ordered.append(t)
    return ordered


def infer_claim_subject(criterion: str) -> str:
    """Prefer a stable subject token from the criterion text."""
    # Path-like or endpoint-like tokens
    path = re.search(r"(/[a-zA-Z0-9_\-./]+)", criterion)
    if path:
        return path.group(1)
    # Quoted subject
    quoted = re.search(r"[\"']([^\"']+)[\"']", criterion)
    if quoted:
        return quoted.group(1)
    return criterion.strip()[:80]


def build_claims_from_contract(contract: Contract) -> list[Claim]:
    """Derive Claims from Contract DONE criteria with proportional Evidence needs."""
    claims: list[Claim] = []
    for i, crit in enumerate(contract.done_criteria, start=1):
        claims.append(
            Claim(
                id=f"{contract.change_id}/claim-done-{i}",
                statement=crit,
                required_evidence_types=infer_required_evidence_types(crit),
                subject=infer_claim_subject(crit),
            )
        )
    return claims


def evidence_is_fresh(
    evidence: Evidence,
    *,
    current_subject_states: dict[str, str] | None = None,
) -> bool:
    """
    Derive validity/staleness when current subject state is known.

    If Evidence recorded subject_state S and current state for that subject differs,
    Evidence does not establish the current state.

    Commit-based states (``commit:<sha>``) compare on the SHA only; optional
    suffixes like ``|review:approved`` are ignored for freshness.
    """
    if not current_subject_states or not evidence.subject_state:
        return True
    current = current_subject_states.get(evidence.subject)
    if current is None:
        return True
    recorded = evidence.subject_state.split("|", 1)[0].strip()
    current_core = current.split("|", 1)[0].strip()
    return recorded == current_core


def _evidence_supports_claim(evidence: Evidence, claim: Claim) -> bool:
    """Structural binding: SUPPORTS→claim.id, matching type, and subject when set."""
    bound = any(
        r.type is RelationType.SUPPORTS and r.target_id == claim.id
        for r in evidence.relations
    )
    if not bound:
        return False
    if evidence.type not in claim.required_evidence_types:
        return False
    if claim.subject:
        # Subject must match claim subject (exact or contained)
        subj = evidence.subject.strip().lower()
        want = claim.subject.strip().lower()
        if subj != want and want not in subj and subj not in want:
            return False
    challenged = any(
        r.type is RelationType.CHALLENGES and r.target_id == claim.id
        for r in evidence.relations
    )
    if challenged:
        return False
    return True


def _normalize_evidence(
    evidence: list[Evidence] | list[tuple[str, str]],
) -> list[Evidence]:
    if not evidence:
        return []
    first = evidence[0]
    if isinstance(first, Evidence):
        return list(evidence)  # type: ignore[arg-type]
    # Legacy (id, type) tuples — no claim binding possible
    normalized: list[Evidence] = []
    for item in evidence:
        eid, etype = item  # type: ignore[misc]
        normalized.append(
            Evidence(
                id=eid,
                type=etype,
                subject="unspecified",
                source="legacy",
                producer="legacy",
            )
        )
    return normalized


def evaluate_assurance(
    *,
    claims: list[Claim],
    evidence: list[Evidence] | list[tuple[str, str]],
    current_subject_states: dict[str, str] | None = None,
) -> AssuranceResult:
    """
    Evaluate whether Evidence structurally supports each Claim.

    - Evidence must SUPPORT the Claim id (relation)
    - Evidence type must be appropriate for the Claim
    - Subject must align when Claim.subject is set
    - Stale Evidence (detectable via subject_state) does not establish current state
    - Missing Evidence → INCONCLUSIVE; wrong Evidence → NOT_SATISFIED when present but unfit
    """
    items = _normalize_evidence(evidence)
    evidence_ids = [e.id for e in items]

    if not claims:
        return AssuranceResult(
            verdict=AssuranceVerdict.INCONCLUSIVE,
            rationale="No claims provided",
            evidence_ids=evidence_ids,
        )

    claim_results: dict[str, str] = {}
    unmet: list[str] = []
    inconclusive: list[str] = []
    supporting_ids: list[str] = []

    for claim in claims:
        if not claim.required_evidence_types:
            claim_results[claim.id] = "INCONCLUSIVE"
            inconclusive.append(claim.id)
            continue

        fresh_supporting = [
            e
            for e in items
            if _evidence_supports_claim(e, claim)
            and evidence_is_fresh(e, current_subject_states=current_subject_states)
        ]
        if fresh_supporting:
            claim_results[claim.id] = "SATISFIED"
            supporting_ids.extend(e.id for e in fresh_supporting)
            continue

        # Bound but stale, or wrong-type/wrong-subject evidence present for this claim?
        related = [
            e
            for e in items
            if any(
                r.type in {RelationType.SUPPORTS, RelationType.CHALLENGES}
                and r.target_id == claim.id
                for r in e.relations
            )
            or (
                claim.subject
                and e.subject.strip().lower() == claim.subject.strip().lower()
            )
        ]
        stale_only = [
            e
            for e in items
            if any(r.type is RelationType.SUPPORTS and r.target_id == claim.id for r in e.relations)
            and not evidence_is_fresh(e, current_subject_states=current_subject_states)
        ]
        if stale_only and not fresh_supporting:
            claim_results[claim.id] = "NOT_SATISFIED"
            unmet.append(claim.id)
        elif related and not fresh_supporting:
            # Evidence exists for this subject/claim but does not satisfy requirements
            claim_results[claim.id] = "NOT_SATISFIED"
            unmet.append(claim.id)
        elif not items:
            claim_results[claim.id] = "INCONCLUSIVE"
            inconclusive.append(claim.id)
        else:
            # Evidence present in Change but none bound to this claim
            claim_results[claim.id] = "INCONCLUSIVE"
            inconclusive.append(claim.id)

    if unmet:
        verdict = AssuranceVerdict.NOT_SATISFIED
        rationale = f"Unmet claims: {', '.join(unmet)}"
    elif inconclusive:
        verdict = AssuranceVerdict.INCONCLUSIVE
        rationale = f"Insufficient evidence for claims: {', '.join(inconclusive)}"
    else:
        verdict = AssuranceVerdict.SATISFIED
        rationale = "All claims have matching attributable evidence"

    unique_support = list(dict.fromkeys(supporting_ids))
    return AssuranceResult(
        verdict=verdict,
        claims=claims,
        evidence_ids=evidence_ids,
        rationale=rationale,
        relations=[
            Relation(type=RelationType.SUPPORTS, target_id=eid) for eid in unique_support
        ],
        claim_results=claim_results,
    )
