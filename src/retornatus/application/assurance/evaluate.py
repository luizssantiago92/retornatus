"""Assurance verdicts and claim↔evidence evaluation (PRD §23–§24 / M6)."""

from __future__ import annotations

import re
from enum import Enum

from pydantic import Field

from retornatus.domain.base import DomainModel
from retornatus.domain.enums import EvidenceProvenance
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
    unverified_evidence_ids: list[EvidenceId] = Field(default_factory=list)
    evidence_labels: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


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

# Types whose satisfaction requires a harness-executed command with exit code 0.
# Narrative types (review notes, repository observations) stay self-reportable.
EXECUTION_EVIDENCE_TYPES = frozenset(
    {
        "test_result",
        "security_test",
        "build_result",
        "lint_result",
    }
)


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


def normalize_subject(value: str) -> str:
    """Match key: strip, case-fold, drop trailing slashes except a lone ``/``.

    Satisfaction uses this key for an exact comparison. A shorter token is not
    treated as contained in a longer one (``/`` does not match ``/health``).
    ``/Health/`` does match ``/health``.
    """
    text = value.strip().casefold()
    if len(text) > 1:
        text = text.rstrip("/")
    return text


def subjects_match(left: str, right: str) -> bool:
    """Exact subject match after :func:`normalize_subject`."""
    return normalize_subject(left) == normalize_subject(right)


def evidence_subject_matches_claim(evidence_subject: str, claim_subject: str) -> bool:
    """Whether Evidence subject establishes the Claim subject.

    Primary rule: exact match after :func:`normalize_subject`.

    One-directional exception (path token): a longer evidence path may end with
    the claim's path token, so ``docs/health.md`` matches claim ``/health.md``.
    Claim inference pulls ``/...`` tokens out of DONE text; Evidence often names
    the file. The reverse is not accepted — evidence ``/`` does not match claim
    ``/health``, and evidence ``/health`` does not match claim ``/``.
    """
    evidence_key = normalize_subject(evidence_subject)
    claim_key = normalize_subject(claim_subject)
    if evidence_key == claim_key:
        return True
    if not claim_key or not evidence_key:
        return False
    if claim_key.startswith("/"):
        return evidence_key.endswith(claim_key) and len(evidence_key) > len(claim_key)
    return evidence_key.endswith("/" + claim_key)


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
    if claim.subject and not evidence_subject_matches_claim(
        evidence.subject, claim.subject
    ):
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


def execution_proof_kind(
    evidence: Evidence,
    *,
    allow_self_reported: bool,
) -> str:
    """Classify whether execution-typed Evidence can satisfy a Claim.

    Returns ``satisfying``, ``unverified``, or ``failing``.

    Non-execution types (review notes, repository observations) return
    ``satisfying`` here; structural binding is checked separately. They remain
    labeled self-reported in Assurance output.

    Executed evidence satisfies only with exit code 0 and no timeout.
    Self-reported execution evidence is ``unverified`` unless
    ``allow_self_reported`` is set (migration opt-out).
    """
    if evidence.type not in EXECUTION_EVIDENCE_TYPES:
        return "satisfying"
    if evidence.provenance is EvidenceProvenance.EXECUTED:
        if evidence.timed_out or evidence.exit_code != 0:
            return "failing"
        return "satisfying"
    if allow_self_reported:
        return "satisfying"
    return "unverified"


def describe_evidence(evidence: Evidence, *, allow_self_reported: bool) -> str:
    """One-line label so verify output shows provenance and trust."""
    provenance = evidence.provenance.value
    if evidence.type not in EXECUTION_EVIDENCE_TYPES:
        return (
            f"{evidence.id} type={evidence.type} provenance={provenance} "
            "status=self-reported"
        )
    if evidence.provenance is EvidenceProvenance.EXECUTED:
        if evidence.timed_out:
            status = "failing(timeout)"
        elif evidence.exit_code == 0:
            status = "executed"
        else:
            status = f"failing(exit {evidence.exit_code})"
        return (
            f"{evidence.id} type={evidence.type} provenance=executed "
            f"exit_code={evidence.exit_code} status={status}"
        )
    if allow_self_reported:
        return (
            f"{evidence.id} type={evidence.type} provenance=self_reported "
            "status=self-reported(allowed)"
        )
    return (
        f"{evidence.id} type={evidence.type} provenance=self_reported "
        "status=UNVERIFIED"
    )


def evaluate_assurance(
    *,
    claims: list[Claim],
    evidence: list[Evidence] | list[tuple[str, str]],
    current_subject_states: dict[str, str] | None = None,
    allow_self_reported: bool = False,
) -> AssuranceResult:
    """
    Evaluate whether Evidence structurally supports each Claim.

    - Evidence must SUPPORT the Claim id (relation)
    - Evidence type must be appropriate for the Claim
    - Subject must match exactly after normalization when Claim.subject is set
    - Stale Evidence (detectable via subject_state) does not establish current state
    - Execution types (test/build/lint/security test) satisfy only when
      provenance is ``executed`` and the exit code is 0, unless
      ``allow_self_reported`` is set
    - Missing Evidence → INCONCLUSIVE; wrong Evidence → NOT_SATISFIED when present but unfit
    - Self-reported execution evidence → claim result UNVERIFIED and overall
      not SATISFIED
    """
    items = _normalize_evidence(evidence)
    evidence_ids = [e.id for e in items]
    labels = [
        describe_evidence(e, allow_self_reported=allow_self_reported) for e in items
    ]
    unverified_ids = [
        e.id
        for e in items
        if execution_proof_kind(e, allow_self_reported=allow_self_reported) == "unverified"
    ]
    warnings: list[str] = []
    if allow_self_reported:
        for item in items:
            if (
                item.type in EXECUTION_EVIDENCE_TYPES
                and item.provenance is not EvidenceProvenance.EXECUTED
            ):
                warnings.append(
                    f"{item.id} self-reported {item.type} accepted via allow_self_reported"
                )

    if not claims:
        return AssuranceResult(
            verdict=AssuranceVerdict.INCONCLUSIVE,
            rationale="No claims provided",
            evidence_ids=evidence_ids,
            evidence_labels=labels,
            unverified_evidence_ids=unverified_ids,
            warnings=warnings,
        )

    claim_results: dict[str, str] = {}
    unmet: list[str] = []
    inconclusive: list[str] = []
    unverified_claims: list[str] = []
    supporting_ids: list[str] = []

    for claim in claims:
        if not claim.required_evidence_types:
            claim_results[claim.id] = "INCONCLUSIVE"
            inconclusive.append(claim.id)
            continue

        structural = [e for e in items if _evidence_supports_claim(e, claim)]
        fresh = [
            e
            for e in structural
            if evidence_is_fresh(e, current_subject_states=current_subject_states)
        ]
        fresh_ids = {id(e) for e in fresh}
        stale = [e for e in structural if id(e) not in fresh_ids]

        satisfying: list[Evidence] = []
        unverified: list[Evidence] = []
        failing: list[Evidence] = []
        for item in fresh:
            kind = execution_proof_kind(item, allow_self_reported=allow_self_reported)
            if kind == "satisfying":
                satisfying.append(item)
            elif kind == "unverified":
                unverified.append(item)
            else:
                failing.append(item)

        if satisfying:
            claim_results[claim.id] = "SATISFIED"
            supporting_ids.extend(e.id for e in satisfying)
            continue

        if stale or failing:
            claim_results[claim.id] = "NOT_SATISFIED"
            unmet.append(claim.id)
            continue

        if unverified:
            claim_results[claim.id] = "UNVERIFIED"
            unverified_claims.append(claim.id)
            continue

        # Bound but wrong-type/wrong-subject evidence present for this claim?
        related = [
            e
            for e in items
            if any(
                r.type in {RelationType.SUPPORTS, RelationType.CHALLENGES}
                and r.target_id == claim.id
                for r in e.relations
            )
            or (
                claim.subject is not None
                and evidence_subject_matches_claim(e.subject, claim.subject)
            )
        ]
        if related:
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
    elif unverified_claims:
        verdict = AssuranceVerdict.NOT_SATISFIED
        rationale = (
            "Unverified claims (self-reported execution evidence does not satisfy): "
            + ", ".join(unverified_claims)
            + ". Re-record with `evidence run` or pass --allow-self-reported."
        )
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
        unverified_evidence_ids=unverified_ids,
        evidence_labels=labels,
        warnings=warnings,
    )
