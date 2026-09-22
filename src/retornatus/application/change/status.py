"""Derived Change status projection — not durable truth (PRD §44)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from retornatus.application.adaptation.skill_need import assess_skill_need
from retornatus.application.assurance.independent import evaluate_change_assurance
from retornatus.application.change.loop import project_next_work
from retornatus.application.change.readiness import synchronize_action
from retornatus.domain.enums import QuestionLifecycle
from retornatus.infrastructure.persistence.repository import FileRepository


@dataclass
class ChangeStatusProjection:
    change_id: str
    title: str
    contract_version: int | None
    contract_active: bool
    open_questions: int = 0
    tasks_ready: int = 0
    tasks_blocked: int = 0
    tasks_active: int = 0
    tasks_completed: int = 0
    tasks_failed: int = 0
    next_kind: str | None = None
    next_id: str | None = None
    next_summary: str | None = None
    skill_required: bool | None = None
    assurance_verdict: str | None = None
    lines: list[str] = field(default_factory=list)

    def render(self) -> str:
        return "\n".join(self.lines)


def project_change_status(root: Path, change_id: str) -> ChangeStatusProjection:
    """Assemble a rich derived status for one Change."""
    repo = FileRepository(root)
    change, _ = repo.load_change(change_id)
    contract_version = None
    contract_active = False
    try:
        contract, _ = repo.load_contract(change_id)
        contract_version = contract.version
        contract_active = contract.active
    except FileNotFoundError:
        proj = ChangeStatusProjection(
            change_id=change_id,
            title=change.title,
            contract_version=None,
            contract_active=False,
            lines=[f"{change_id}: demand understood, no contract — {change.title}"],
        )
        return proj

    open_q = 0
    qdir = repo.paths.change_dir(change_id) / "questions"
    if qdir.is_dir():
        for path in qdir.glob("Q-*.json"):
            q, _ = repo.load_question(f"{change_id}/{path.stem}")
            if q.lifecycle is QuestionLifecycle.OPEN:
                open_q += 1

    ready = blocked = active = completed = failed = 0
    first_action_id: str | None = None
    actions_dir = repo.paths.change_dir(change_id) / "actions"
    if actions_dir.is_dir():
        for path in sorted(actions_dir.glob("A-*.json")):
            action, _ = repo.load_action(f"{change_id}/{path.stem}")
            if first_action_id is None:
                first_action_id = action.id
            if not action.tasks:
                continue
            sync = synchronize_action(action)
            ready += len(sync.ready)
            blocked += len(sync.blocked)
            active += len(sync.active)
            completed += len(sync.completed)
            failed += len(sync.failed)

    nxt = project_next_work(root, change_id)
    skill_required = None
    if first_action_id:
        skill_required = assess_skill_need(root, first_action_id).required

    assurance_verdict = None
    if contract_active:
        try:
            assurance_verdict = evaluate_change_assurance(root, change_id).verdict.value
        except Exception:  # noqa: BLE001
            assurance_verdict = "UNAVAILABLE"

    if not contract_active:
        header = f"{change_id}: contract draft v{contract_version} — {change.title}"
    else:
        header = f"{change_id}: contract v{contract_version} active — {change.title}"

    lines = [header]
    lines.append(
        f"  tasks: ready={ready} blocked={blocked} active={active} "
        f"completed={completed} failed={failed}"
    )
    lines.append(f"  open_questions: {open_q}")
    if nxt.primary:
        lines.append(f"  next: {nxt.primary.kind}\t{nxt.primary.id}\t{nxt.primary.summary}")
    if skill_required is not None:
        lines.append(f"  skill_need: {'required' if skill_required else 'optional/skip'}")
    if assurance_verdict:
        lines.append(f"  assurance: {assurance_verdict}")

    return ChangeStatusProjection(
        change_id=change_id,
        title=change.title,
        contract_version=contract_version,
        contract_active=contract_active,
        open_questions=open_q,
        tasks_ready=ready,
        tasks_blocked=blocked,
        tasks_active=active,
        tasks_completed=completed,
        tasks_failed=failed,
        next_kind=nxt.primary.kind if nxt.primary else None,
        next_id=nxt.primary.id if nxt.primary else None,
        next_summary=nxt.primary.summary if nxt.primary else None,
        skill_required=skill_required,
        assurance_verdict=assurance_verdict,
        lines=lines,
    )
