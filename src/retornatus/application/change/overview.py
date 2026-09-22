"""Change overview — Claims ↔ Evidence ↔ Tasks ↔ Questions dashboard."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from retornatus.application.assurance.evaluate import (
    build_claims_from_contract,
    evaluate_assurance,
)
from retornatus.application.assurance.evidence import EvidenceService
from retornatus.application.assurance.subject_state import derive_current_subject_states
from retornatus.application.change.loop import project_next_work
from retornatus.application.change.readiness import synchronize_action
from retornatus.domain.enums import QuestionLifecycle
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
            f"# {self.change_id} — {self.title}",
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
            "## Claims ↔ Evidence",
        ]
        if not self.claims:
            lines.append("(no claims — activate a Contract with DONE criteria)")
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
            f"{ev.id} type={ev.type} subject={ev.subject} "
            f"supports={','.join(supports) or '-'}"
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
