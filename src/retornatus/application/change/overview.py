"""Change overview — Claims ↔ Evidence ↔ Tasks ↔ Questions dashboard."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

from retornatus.application.assurance.evaluate import (
    build_claims_from_contract,
    evaluate_assurance,
    evidence_is_fresh,
    execution_proof_kind,
    required_check_issue,
)
from retornatus.application.assurance.evidence import EvidenceService
from retornatus.application.assurance.settings import allow_self_reported_enabled
from retornatus.application.assurance.subject_state import derive_current_subject_states
from retornatus.application.change.loop import project_next_work
from retornatus.application.change.readiness import synchronize_action
from retornatus.domain.enums import QuestionLifecycle
from retornatus.domain.models import Evidence
from retornatus.domain.relations import RelationType
from retornatus.infrastructure.persistence.repository import FileRepository


@dataclass
class ClaimRow:
    claim_id: str
    statement: str
    required_types: list[str]
    evidence_ids: list[str]
    verdict: str


@dataclass
class ChangeOverview:
    change_id: str
    title: str
    lane: str | None
    contract_version: int | None
    contract_active: bool
    what: str
    assurance_verdict: str | None
    claims: list[ClaimRow] = field(default_factory=list)
    evidence_lines: list[str] = field(default_factory=list)
    task_lines: list[str] = field(default_factory=list)
    question_lines: list[str] = field(default_factory=list)
    next_line: str | None = None
    parallelizable: list[str] = field(default_factory=list)

    def render(self) -> str:
        lines = [
            f"# {self.change_id} - {self.title}",
            f"lane: {self.lane or 'unset'}",
            (
                f"contract: v{self.contract_version} "
                f"{'active' if self.contract_active else 'draft'}"
                if self.contract_version is not None
                else "contract: none"
            ),
            f"what: {self.what}" if self.what else "what: (none)",
            f"assurance: {self.assurance_verdict or 'n/a'}",
            "",
            "## Claims / Evidence",
        ]
        if not self.claims:
            lines.append("(no claims - activate a Contract with DONE criteria)")
        for row in self.claims:
            ev = ", ".join(row.evidence_ids) if row.evidence_ids else "(unbound)"
            types = ",".join(row.required_types) or "-"
            lines.append(
                f"- [{row.verdict}] {row.claim_id}: {row.statement} "
                f"(need={types}; evidence={ev})"
            )

        lines.append("")
        lines.append("## Evidence")
        if not self.evidence_lines:
            lines.append("(none)")
        else:
            lines.extend(f"- {x}" for x in self.evidence_lines)

        lines.append("")
        lines.append("## Tasks")
        if not self.task_lines:
            lines.append("(none / action without task graph)")
        else:
            lines.extend(f"- {x}" for x in self.task_lines)

        lines.append("")
        lines.append("## Questions")
        if not self.question_lines:
            lines.append("(none open)")
        else:
            lines.extend(f"- {x}" for x in self.question_lines)

        lines.append("")
        lines.append("## Next")
        lines.append(self.next_line or "(none)")
        if self.parallelizable:
            lines.append(
                "parallelizable: " + ", ".join(self.parallelizable)
            )
        return "\n".join(lines)


def render_pull_request(
    root: Path,
    change_id: str,
    *,
    include_gates: bool = True,
) -> str:
    """Markdown pull-request body: claims, evidence trust, checks, and gates.

    ``include_gates=False`` skips the overview gate list. The CI comment does
    that so the JSON gate table is the only gate result.
    """
    from retornatus.application.assurance.settings import (
        allow_self_reported_enabled,
        load_required_checks,
        uncommitted_changes_mode,
    )
    from retornatus.application.assurance.subject_state import (
        current_git_head,
        derive_current_subject_states,
        subjects_with_uncommitted_changes,
        substantive_worktree_clean,
    )
    from retornatus.application.governance.diff import git_available
    from retornatus.application.governance.gates import (
        gate_assurance,
        gate_contract,
        gate_evidence,
        gate_scope,
        gate_suppressions,
    )
    from retornatus.domain.enums import EvidenceProvenance

    overview = build_change_overview(root, change_id)
    evidence = EvidenceService(root).list_for_change(change_id)
    allowed = allow_self_reported_enabled(root)
    checks = load_required_checks(root)
    states = derive_current_subject_states(root, evidence)
    git_head = current_git_head(root) if git_available(root) else None
    worktree_clean = substantive_worktree_clean(root) if git_available(root) else None
    dirty = subjects_with_uncommitted_changes(root, [item.subject for item in evidence])
    mode = uncommitted_changes_mode(root)

    lines = [
        f"## {overview.change_id} — {overview.title}",
        "",
        f"**Lane:** {overview.lane or 'unset'}",
        (
            f"**Contract:** v{overview.contract_version} "
            f"({'active' if overview.contract_active else 'draft'})"
            if overview.contract_version is not None
            else "**Contract:** none"
        ),
        f"**WHAT:** {overview.what or '(none)'}",
        f"**Assurance:** {overview.assurance_verdict or 'n/a'}",
        "",
        "### Claims",
        "",
    ]
    if not overview.claims:
        lines.append("_No claims — activate a Contract with DONE criteria._")
    for row in overview.claims:
        ev = ", ".join(row.evidence_ids) if row.evidence_ids else "(unbound)"
        types = ", ".join(row.required_types) or "-"
        lines.append(
            f"- **[{row.verdict}]** `{row.claim_id}`: {row.statement} "
            f"(need: {types}; evidence: {ev})"
        )

    lines.extend(["", "### Evidence", ""])
    if not evidence:
        lines.append("_No evidence._")
    for item in evidence:
        trust = _evidence_trust(
            item,
            allow_self_reported=allowed,
            checks=checks,
            git_head=git_head,
            worktree_clean=worktree_clean,
            current_states=states,
            dirty_subjects=dirty,
            uncommitted_mode=mode,
        )
        kind = (
            "executed"
            if item.provenance is EvidenceProvenance.EXECUTED
            else "self-reported"
        )
        exit_label = "n/a" if item.exit_code is None else str(item.exit_code)
        commit = item.git_commit or "n/a"
        command = " ".join(item.command) if item.command else "(none)"
        lines.append(
            f"- **{item.id}** — {kind}, exit `{exit_label}`, "
            f"commit `{commit}`, trust: **{trust}**"
        )
        lines.append(f"  - type `{item.type}`, subject `{item.subject}`, command `{command}`")

    lines.extend(["", "### Required checks", ""])
    if not checks:
        lines.append("_None configured in `.retornatus/config.toml`._")
    else:
        for check in checks:
            matched = [
                item.id
                for item in evidence
                if item.provenance is EvidenceProvenance.EXECUTED
                and item.exit_code == 0
                and not item.timed_out
                and list(item.command or []) == list(check.run)
            ]
            rendered = " ".join(check.run)
            if matched:
                lines.append(
                    f"- **{check.name}** `{rendered}` — matched by {', '.join(matched)}"
                )
            else:
                lines.append(f"- **{check.name}** `{rendered}` — not matched")

    if include_gates:
        lines.extend(["", "### Gates", ""])
        gate_results = [
            gate_contract(root, change_id),
            gate_evidence(root, change_id),
            gate_assurance(root, change_id),
        ]
        if git_available(root):
            gate_results.append(gate_suppressions(root))
            gate_results.append(gate_scope(root, change_id))
        else:
            lines.append("_Scope and suppressions need a git work tree; not evaluated._")
        for result in gate_results:
            status = "pass" if result.passed else "fail"
            detail = "; ".join(result.messages) if result.messages else ""
            lines.append(f"- **{result.name.value}** — {status} — {detail}")

    if overview.next_line:
        lines.extend(["", "### Next", "", f"`{overview.next_line}`"])
    return "\n".join(lines)


def _evidence_trust(
    item: Evidence,
    *,
    allow_self_reported: bool,
    checks: Sequence[object],
    git_head: str | None,
    worktree_clean: bool | None,
    current_states: dict[str, str],
    dirty_subjects: set[str],
    uncommitted_mode: str,
) -> str:
    """Label one Evidence row: executed, self-reported, unverified, stale, or failing."""
    from retornatus.application.assurance.evaluate import uncommitted_subject_fails
    from retornatus.domain.enums import EvidenceProvenance

    issue = required_check_issue(
        item,
        checks,
        git_head=git_head,
        worktree_clean=worktree_clean,
    )
    if issue is not None:
        return issue[0]
    if not evidence_is_fresh(item, current_subject_states=current_states):
        return "stale"
    if item.subject in dirty_subjects and uncommitted_subject_fails(item.type, uncommitted_mode):
        return "stale"
    kind = execution_proof_kind(item, allow_self_reported=allow_self_reported)
    if kind == "unverified":
        return "unverified"
    if kind == "failing":
        return "failing"
    if item.provenance is EvidenceProvenance.SELF_REPORTED:
        return "self-reported"
    return "executed"


def build_change_overview(root: Path, change_id: str) -> ChangeOverview:
    """Assemble a human-readable Change dashboard (projection, not durable truth)."""
    repo = FileRepository(root)
    change, _ = repo.load_change(change_id)

    what = ""
    contract_version = None
    contract_active = False
    claims: list[ClaimRow] = []
    assurance_verdict = None

    try:
        contract, _ = repo.load_contract(change_id)
        contract_version = contract.version
        contract_active = contract.active
        what = contract.what
        built = build_claims_from_contract(contract)
        evidence_list = EvidenceService(root).list_for_change(change_id)
        current_states = derive_current_subject_states(root, evidence_list)
        result = evaluate_assurance(
            claims=built,
            evidence=evidence_list,
            current_subject_states=current_states,
            allow_self_reported=allow_self_reported_enabled(root),
        )
        assurance_verdict = result.verdict.value
        for claim in built:
            bound = [
                e.id
                for e in evidence_list
                if any(
                    r.type is RelationType.SUPPORTS and r.target_id == claim.id
                    for r in e.relations
                )
            ]
            claims.append(
                ClaimRow(
                    claim_id=claim.id,
                    statement=claim.statement,
                    required_types=list(claim.required_evidence_types),
                    evidence_ids=bound,
                    verdict=result.claim_results.get(claim.id, "UNKNOWN"),
                )
            )
    except FileNotFoundError:
        pass

    evidence_lines: list[str] = []
    for ev in EvidenceService(root).list_for_change(change_id):
        supports = [
            r.target_id
            for r in ev.relations
            if r.type is RelationType.SUPPORTS
        ]
        evidence_lines.append(
            f"{ev.id} type={ev.type} provenance={ev.provenance.value} "
            f"subject={ev.subject} supports={','.join(supports) or '-'}"
        )

    task_lines: list[str] = []
    actions_dir = repo.paths.change_dir(change_id) / "actions"
    if actions_dir.is_dir():
        for path in sorted(actions_dir.glob("A-*.json")):
            action, _ = repo.load_action(f"{change_id}/{path.stem}")
            if not action.tasks:
                task_lines.append(f"{action.id}: (no tasks) {action.objective}")
                continue
            sync = synchronize_action(action)
            for proj in sync.tasks:
                task_lines.append(
                    f"{proj.task_id} [{proj.state.value}] {proj.description}"
                )

    question_lines: list[str] = []
    qdir = repo.paths.change_dir(change_id) / "questions"
    if qdir.is_dir():
        for path in sorted(qdir.glob("Q-*.json")):
            q, _ = repo.load_question(f"{change_id}/{path.stem}")
            if q.lifecycle is QuestionLifecycle.OPEN:
                question_lines.append(f"{q.id} OPEN: {q.statement}")

    nxt = project_next_work(root, change_id)
    next_line = None
    if nxt.primary:
        next_line = f"{nxt.primary.kind}\t{nxt.primary.id}\t{nxt.primary.summary}"

    return ChangeOverview(
        change_id=change_id,
        title=change.title,
        lane=change.lane,
        contract_version=contract_version,
        contract_active=contract_active,
        what=what,
        assurance_verdict=assurance_verdict,
        claims=claims,
        evidence_lines=evidence_lines,
        task_lines=task_lines,
        question_lines=question_lines,
        next_line=next_line,
        parallelizable=list(nxt.parallelizable_task_ids),
    )
