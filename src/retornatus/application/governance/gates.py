"""Mechanical gates with non-zero exit semantics (software construction brakes)."""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path

from retornatus.application.assurance.evaluate import (
    AssuranceVerdict,
    build_claims_from_contract,
    evaluate_assurance,
)
from retornatus.infrastructure.persistence.repository import FileRepository


class GateName(StrEnum):
    CONTRACT = "contract"
    EVIDENCE = "evidence"
    SKILL_RESEARCH = "skill-research"
    ASSURANCE = "assurance"
    POLICY = "policy"
    BUDGET = "budget"
    SUPPRESSIONS = "suppressions"
    SCOPE = "scope"
    OMISSION = "omission"


@dataclass
class GateResult:
    name: GateName
    passed: bool
    messages: list[str] = field(default_factory=list)

    @property
    def exit_code(self) -> int:
        return 0 if self.passed else 1


# Placeholders that cannot be observed, plus angle-bracket tokens such as <...>.
_PLACEHOLDER_RE = re.compile(
    r"\bTODO\b|\bTBD\b|\[NEEDS CLARIFICATION\]|<[^>\n]*>",
    re.IGNORECASE,
)
# Words that do not establish a finish line. "etc" / "as needed" hide the rest.
_VAGUE_RE = re.compile(
    r"\b(?:works|properly|fast|user-friendly|as needed|etc)\b",
    re.IGNORECASE,
)
# A criterion should name something a reviewer can check. Absence is a warning.
_OBSERVABLE_RE = re.compile(
    r"\b(?:test|tests|pytest|assert|return|returns|exit|exits|"
    r"pass|passes|fail|fails|contain|contains|include|includes|"
    r"match|matches|equal|equals|file|files|command|output|"
    r"status|endpoint|response|coverage|documented|record|recorded|"
    r"verify|verified|review|reviewed|deny|denies|create|creates|"
    r"created|write|writes|exist|exists|display|show|shows|"
    r"print|prints|log|logs|section|version|commit|gate|preserved|"
    r"stored|saved|present|covers|cover|completed|detect|detected|"
    r"exclude|excludes|excluded)\b|\b\d{2,}\b",
    re.IGNORECASE,
)
_WEAK_EXACT = frozenset({"done", "ok", "works"})


def lint_done_criteria(criteria: list[str]) -> tuple[list[str], list[str]]:
    """Return ``(errors, warnings)`` for Contract DONE lines.

    Errors reject the gate: placeholders, duplicates, vague wording, and
    criteria too short to mean anything. A criterion with no observable
    outcome is a warning — the gate still passes.
    """
    errors: list[str] = []
    warnings: list[str] = []
    seen: set[str] = set()
    for raw in criteria:
        text = raw.strip()
        key = text.casefold()
        if key in seen:
            errors.append(f"DONE criterion is duplicated: {text}")
            continue
        seen.add(key)
        if len(text) < 8 or key in _WEAK_EXACT:
            errors.append(f"DONE criterion is too weak to establish satisfaction: {text}")
            continue
        if _PLACEHOLDER_RE.search(text):
            errors.append(f"DONE criterion contains a placeholder: {text}")
            continue
        if _VAGUE_RE.search(text):
            errors.append(f"DONE criterion uses vague language: {text}")
            continue
        if not _OBSERVABLE_RE.search(text):
            warnings.append(f"WARN: DONE criterion has no observable outcome: {text}")
    return errors, warnings


def gate_contract(root: Path, change_id: str) -> GateResult:
    """Active Contract must exist with WHAT and lint-clean DONE criteria."""
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
        errors, warnings = lint_done_criteria(list(contract.done_criteria))
        messages.extend(errors)
        if messages:
            return GateResult(GateName.CONTRACT, False, messages + warnings)
        if warnings:
            return GateResult(GateName.CONTRACT, True, warnings)
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

    from retornatus.application.assurance.settings import (
        allow_self_reported_enabled,
        load_required_checks,
        uncommitted_changes_mode,
    )
    from retornatus.application.assurance.subject_state import (
        commit_delta_is_harness_only,
        current_git_head,
        subjects_with_uncommitted_changes,
        substantive_worktree_clean,
    )

    allowed = allow_self_reported_enabled(root)
    if current_subject_states is not None:
        claims = build_claims_from_contract(contract)
        evidence = EvidenceService(root).list_for_change(change_id)
        checks = load_required_checks(root)
        dirty = subjects_with_uncommitted_changes(root, [item.subject for item in evidence])
        head = current_git_head(root) if checks else None
        equivalent: Callable[[str], bool] | None = None
        if head:
            recorded_head = head

            def equivalent(recorded: str) -> bool:
                return commit_delta_is_harness_only(root, recorded, recorded_head)

        result = evaluate_assurance(
            claims=claims,
            evidence=evidence,
            current_subject_states=current_subject_states,
            allow_self_reported=allowed,
            required_checks=checks or None,
            git_head=head,
            worktree_clean=substantive_worktree_clean(root) if checks else None,
            uncommitted_subjects=dirty or None,
            uncommitted_mode=uncommitted_changes_mode(root),
            commit_equivalent=equivalent,
        )
    else:
        result = evaluate_change_assurance(
            root,
            change_id,
            use_git_state=use_git_state,
            allow_self_reported=allowed,
        )
    ok = result.verdict is AssuranceVerdict.SATISFIED
    detail = [
        f"Verdict={result.verdict.value}: {result.rationale}",
    ]
    for claim_id, status in result.claim_results.items():
        detail.append(f"  {claim_id}: {status}")
    detail.extend(result.evidence_labels)
    for warning in result.warnings:
        detail.append(f"WARN {warning}")
    return GateResult(GateName.ASSURANCE, ok, detail)


def gate_budget(root: Path, action_id: str) -> GateResult:
    """Optional Action attempt budget — STOP when attempts are exhausted."""
    repo = FileRepository(root)
    try:
        action, _ = repo.load_action(action_id)
    except FileNotFoundError:
        return GateResult(GateName.BUDGET, False, [f"Action not found: {action_id}"])
    if action.max_attempts is None:
        return GateResult(
            GateName.BUDGET,
            True,
            ["No max_attempts set (unlimited)"],
        )
    remaining = action.max_attempts - action.attempt_count
    if action.attempt_count >= action.max_attempts:
        return GateResult(
            GateName.BUDGET,
            False,
            [
                f"Attempt budget exhausted: {action.attempt_count}/{action.max_attempts}",
                "Record a Decision / raise max_attempts before continuing",
            ],
        )
    return GateResult(
        GateName.BUDGET,
        True,
        [f"Attempts {action.attempt_count}/{action.max_attempts} ({remaining} remaining)"],
    )


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
    for warning in decision.warnings:
        messages.append(f"WARN {warning}")
    return GateResult(GateName.POLICY, ok, messages)


def gate_suppressions(
    root: Path,
    *,
    base: str | None = None,
    staged: bool = False,
) -> GateResult:
    """STOP when added diff lines introduce suppression or skip markers."""
    from retornatus.application.governance.diff_scan import format_hit, scan_suppressions

    hits = scan_suppressions(root, base=base, staged=staged)
    if not hits:
        return GateResult(
            GateName.SUPPRESSIONS,
            True,
            ["No suppression markers in added lines"],
        )
    messages = [f"{len(hits)} suppression marker(s) in added lines:"]
    messages.extend(format_hit(hit) for hit in hits)
    return GateResult(GateName.SUPPRESSIONS, False, messages)


def gate_omission(
    root: Path,
    *,
    base: str | None = None,
    staged: bool = False,
    author: str = "",
    declared_change: str | None = None,
) -> GateResult:
    """STOP when code changes and no Change covers it, unless a listed bot is exempt."""
    from retornatus.application.governance.omission import assess_omission

    report = assess_omission(
        root,
        base=base,
        staged=staged,
        author=author,
        declared_change=declared_change,
    )
    return GateResult(GateName.OMISSION, report.passed, list(report.messages))


def gate_scope(
    root: Path,
    change_id: str,
    *,
    base: str | None = None,
    staged: bool = False,
) -> GateResult:
    """STOP when the diff leaves Task.resources or touches denied/sensitive paths."""
    from retornatus.application.governance.scope import evaluate_scope

    report = evaluate_scope(root, change_id, base=base, staged=staged)
    return GateResult(GateName.SCOPE, report.passed, report.messages)
