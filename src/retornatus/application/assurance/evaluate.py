"""Assurance verdicts and claim↔evidence evaluation (PRD §23–§24 / M6)."""

from __future__ import annotations

import re
from collections.abc import Callable, Sequence
from enum import StrEnum
from typing import Any

from pydantic import Field

from retornatus.domain.base import DomainModel
from retornatus.domain.enums import EvidenceProvenance
from retornatus.domain.ids import EvidenceId
from retornatus.domain.models import Contract, Evidence
from retornatus.domain.relations import Relation, RelationType


class AssuranceVerdict(StrEnum):
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
    surfaces: list[dict[str, Any]] = Field(default_factory=list)


_DOC_MARKERS = re.compile(r"\b(document|documented|docs|readme|openapi|spec)\b", re.I)
_TEST_MARKERS = re.compile(
    r"\b(test|pytest|automated|returns|endpoint|behavior|health|integration)\b",
    re.I,
)
_SECURITY_MARKERS = re.compile(r"\b(security|unauthorized|authn|authz|permission|secret)\b", re.I)
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
    commit_equivalent: Callable[[str], bool] | None = None,
) -> bool:
    """
    Derive validity/staleness when current subject state is known.

    If Evidence recorded subject_state S and current state for that subject differs,
    Evidence does not establish the current state.

    Commit-based states (``commit:<sha>``) compare on the SHA only; optional
    suffixes like ``|review:approved`` are ignored for freshness.
    ``commit_equivalent`` may treat ``commit:<recorded>`` as fresh when the only
    files changed since that SHA are harness bookkeeping.
    """
    if not current_subject_states or not evidence.subject_state:
        return True
    current = current_subject_states.get(evidence.subject)
    if current is None:
        return True
    recorded = evidence.subject_state.split("|", 1)[0].strip()
    current_core = current.split("|", 1)[0].strip()
    if recorded == current_core:
        return True
    return _commit_states_equivalent(recorded, current_core, commit_equivalent)


def _commit_states_equivalent(
    recorded: str,
    current: str,
    commit_equivalent: Callable[[str], bool] | None,
) -> bool:
    prefix = "commit:"
    if commit_equivalent is None:
        return False
    if not recorded.startswith(prefix) or not current.startswith(prefix):
        return False
    recorded_sha = recorded[len(prefix) :].strip()
    return bool(recorded_sha) and commit_equivalent(recorded_sha)


def _evidence_supports_claim(evidence: Evidence, claim: Claim) -> bool:
    """Structural binding: SUPPORTS→claim.id, matching type, and subject when set."""
    bound = any(r.type is RelationType.SUPPORTS and r.target_id == claim.id for r in evidence.relations)
    if not bound:
        return False
    if evidence.type not in claim.required_evidence_types:
        return False
    if claim.subject and not evidence_subject_matches_claim(evidence.subject, claim.subject):
        return False
    challenged = any(r.type is RelationType.CHALLENGES and r.target_id == claim.id for r in evidence.relations)
    return not challenged


def _normalize_evidence(
    evidence: list[Evidence] | list[tuple[str, str]],
) -> list[Evidence]:
    if not evidence:
        return []
    normalized: list[Evidence] = []
    for item in evidence:
        if isinstance(item, Evidence):
            normalized.append(item)
            continue
        # Legacy (id, type) tuples — no claim binding possible
        eid, etype = item
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


def _check_applies(evidence_type: str, types: frozenset[str]) -> bool:
    return not types or evidence_type in types


def required_check_issue(
    evidence: Evidence,
    checks: Sequence[object],
    *,
    git_head: str | None,
    worktree_clean: bool | None,
    commit_equivalent: Callable[[str], bool] | None = None,
) -> tuple[str, str] | None:
    """Why executed evidence fails an owner-declared required check.

    Returns ``("unverified"|"stale", message)`` or None when the evidence is
    not constrained (no checks, non-execution type, or already a failing run).

    Self-reported execution evidence stays unverified even when
    ``allow_self_reported`` is set: the owner named the commands that count.

    ``commit_equivalent`` may accept a recorded commit that is not HEAD when
    the only files changed since that commit are harness bookkeeping (evidence
    just committed under ``.retornatus/changes/``). A missing callback keeps
    the strict HEAD match.
    """
    if not checks or evidence.type not in EXECUTION_EVIDENCE_TYPES:
        return None
    from retornatus.application.assurance.settings import RequiredCheck

    typed: list[RequiredCheck] = [c for c in checks if isinstance(c, RequiredCheck)]
    if not typed:
        return None
    applicable = [c for c in typed if _check_applies(evidence.type, c.types)]
    if evidence.provenance is not EvidenceProvenance.EXECUTED:
        names = ", ".join(c.name for c in applicable) or ", ".join(c.name for c in typed)
        return (
            "unverified",
            f"{evidence.id} is self-reported; required check ({names}) must be executed",
        )
    if evidence.timed_out or evidence.exit_code != 0:
        return None
    argv = list(evidence.command or [])
    matched = any(list(check.run) == argv for check in applicable)
    if not matched:
        rendered = " ".join(argv) if argv else "(none)"
        names = ", ".join(f"{c.name}={' '.join(c.run)}" for c in applicable) or "(none apply to this type)"
        return (
            "unverified",
            f"{evidence.id} argv [{rendered}] does not match a required check ({names})",
        )
    if git_head is None:
        return None
    recorded = (evidence.git_commit or "").strip()
    head = git_head.strip()
    same_commit = bool(recorded) and recorded.casefold() == head.casefold()
    equivalent = bool(recorded and not same_commit and commit_equivalent is not None and commit_equivalent(recorded))
    if not same_commit and not equivalent:
        shown = recorded or "none"
        return (
            "stale",
            f"{evidence.id} recorded commit {shown} != HEAD {git_head} (stale required check)",
        )
    if evidence.worktree_dirty is not False:
        return (
            "stale",
            f"{evidence.id} ran against a dirty worktree; required checks need a clean tree",
        )
    if worktree_clean is False:
        return (
            "stale",
            f"{evidence.id} worktree has uncommitted changes since the required check",
        )
    return None


def uncommitted_subject_fails(evidence_type: str, mode: str) -> bool:
    """Whether uncommitted edits to a subject path fail the claim.

    ``default`` fails execution types and only warns for narrative evidence.
    """
    if mode == "warn":
        return False
    if mode == "fail":
        return True
    return evidence_type in EXECUTION_EVIDENCE_TYPES


def describe_evidence(evidence: Evidence, *, allow_self_reported: bool) -> str:
    """One-line label so verify output shows provenance and trust."""
    provenance = evidence.provenance.value
    if evidence.type not in EXECUTION_EVIDENCE_TYPES:
        return f"{evidence.id} type={evidence.type} provenance={provenance} status=self-reported"
    if evidence.provenance is EvidenceProvenance.EXECUTED:
        if evidence.timed_out:
            status = "failing(timeout)"
        elif evidence.exit_code == 0:
            status = "executed"
        else:
            status = f"failing(exit {evidence.exit_code})"
        return f"{evidence.id} type={evidence.type} provenance=executed exit_code={evidence.exit_code} status={status}"
    if allow_self_reported:
        return f"{evidence.id} type={evidence.type} provenance=self_reported status=self-reported(allowed)"
    return f"{evidence.id} type={evidence.type} provenance=self_reported status=UNVERIFIED"


def evaluate_assurance(
    *,
    claims: list[Claim],
    evidence: list[Evidence] | list[tuple[str, str]],
    current_subject_states: dict[str, str] | None = None,
    allow_self_reported: bool = False,
    required_checks: Sequence[object] | None = None,
    git_head: str | None = None,
    worktree_clean: bool | None = None,
    uncommitted_subjects: set[str] | None = None,
    uncommitted_mode: str = "default",
    commit_equivalent: Callable[[str], bool] | None = None,
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
    - When ``required_checks`` is set, execution evidence must be an exact argv
      match, exit 0, recorded commit == ``git_head`` (or equivalent via
      ``commit_equivalent``), and a clean worktree.
      ``allow_self_reported`` does not bypass that.
    - Uncommitted edits to a claim subject path are stale when the mode fails
      (default: execution types fail, narrative types warn)
    - Missing Evidence → INCONCLUSIVE; wrong Evidence → NOT_SATISFIED when present but unfit
    - Self-reported execution evidence → claim result UNVERIFIED and overall
      not SATISFIED
    """
    items = _normalize_evidence(evidence)
    evidence_ids = [e.id for e in items]
    checks = list(required_checks or [])
    check_issues: dict[str, tuple[str, str]] = {}
    if checks:
        for item in items:
            issue = required_check_issue(
                item,
                checks,
                git_head=git_head,
                worktree_clean=worktree_clean,
                commit_equivalent=commit_equivalent,
            )
            if issue is not None:
                check_issues[item.id] = issue
    labels = [describe_evidence(e, allow_self_reported=allow_self_reported) for e in items]
    for item in items:
        issue = check_issues.get(item.id)
        if issue is not None:
            labels.append(f"{item.id} required_check={issue[0]}")
    unverified_ids = [
        e.id
        for e in items
        if execution_proof_kind(e, allow_self_reported=allow_self_reported) == "unverified"
        or check_issues.get(e.id, ("", ""))[0] == "unverified"
    ]
    warnings: list[str] = []
    seen_warnings: set[str] = set()

    def _warn(message: str) -> None:
        if message not in seen_warnings:
            seen_warnings.add(message)
            warnings.append(message)

    for issue in check_issues.values():
        _warn(issue[1])
    dirty_subjects = uncommitted_subjects or set()
    for item in items:
        if item.subject not in dirty_subjects:
            continue
        fails = uncommitted_subject_fails(item.type, uncommitted_mode)
        tail = " (stale)" if fails else " (warning)"
        _warn(f"{item.id} subject {item.subject!r} has uncommitted changes{tail}")
    if allow_self_reported and not checks:
        for item in items:
            if item.type in EXECUTION_EVIDENCE_TYPES and item.provenance is not EvidenceProvenance.EXECUTED:
                _warn(f"{item.id} self-reported {item.type} accepted via allow_self_reported")

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
    stale_claim_ids: list[str] = []
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
            if evidence_is_fresh(
                e,
                current_subject_states=current_subject_states,
                commit_equivalent=commit_equivalent,
            )
        ]
        fresh_ids = {id(e) for e in fresh}
        stale = [e for e in structural if id(e) not in fresh_ids]
        for item in list(fresh):
            if item.subject in dirty_subjects and uncommitted_subject_fails(item.type, uncommitted_mode):
                fresh.remove(item)
                stale.append(item)

        satisfying: list[Evidence] = []
        unverified: list[Evidence] = []
        failing: list[Evidence] = []
        for item in fresh:
            issue = check_issues.get(item.id)
            if issue is not None:
                if issue[0] == "stale":
                    stale.append(item)
                else:
                    unverified.append(item)
                continue
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
            if stale:
                stale_claim_ids.append(claim.id)
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
                r.type in {RelationType.SUPPORTS, RelationType.CHALLENGES} and r.target_id == claim.id
                for r in e.relations
            )
            or (claim.subject is not None and evidence_subject_matches_claim(e.subject, claim.subject))
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

    stale_notes = [message for kind, message in check_issues.values() if kind == "stale"]
    uncommitted_fail_notes = [message for message in warnings if message.endswith("(stale)")]
    if unmet:
        verdict = AssuranceVerdict.NOT_SATISFIED
        if stale_claim_ids and (stale_notes or uncommitted_fail_notes):
            rationale = "Stale evidence: " + "; ".join([*uncommitted_fail_notes, *stale_notes])
        else:
            rationale = f"Unmet claims: {', '.join(unmet)}"
    elif unverified_claims:
        verdict = AssuranceVerdict.NOT_SATISFIED
        if checks and any(check_issues.get(cid) for cid in unverified_ids):
            rationale = (
                "Unverified claims (required check not met): "
                + ", ".join(unverified_claims)
                + ". Run `verify --run-checks` or `checks run`."
            )
        else:
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
        relations=[Relation(type=RelationType.SUPPORTS, target_id=eid) for eid in unique_support],
        claim_results=claim_results,
        unverified_evidence_ids=unverified_ids,
        evidence_labels=labels,
        warnings=warnings,
    )
