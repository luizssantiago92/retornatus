"""Derived construction loop — next ready unit of work (not a Loop Engine)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from retornatus.application.change.readiness import synchronize_action
from retornatus.domain.enums import DerivedTaskState, QuestionLifecycle
from retornatus.infrastructure.persistence.repository import FileRepository


@dataclass
class LoopNext:
    kind: str
    id: str
    summary: str


@dataclass
class LoopProjection:
    """Reliable projection of legitimate next work (may include multiple ready tasks)."""

    primary: LoopNext | None
    ready: list[LoopNext] = field(default_factory=list)
    blocked_task_ids: list[str] = field(default_factory=list)
    parallelizable_task_ids: list[str] = field(default_factory=list)


def project_next_work(root: Path, change_id: str) -> LoopProjection:
    """
    Project next actionable item(s) for a Change.

    Order: open Questions → READY tasks (never BLOCKED) → Action objective.
    Multiple independent READY tasks are reported without inventing a Wave entity.
    """
    repo = FileRepository(root)
    change_dir = repo.paths.change_dir(change_id)
    ready_items: list[LoopNext] = []
    blocked: list[str] = []
    parallelizable: list[str] = []

    questions_dir = change_dir / "questions"
    if questions_dir.is_dir():
        for path in sorted(questions_dir.glob("Q-*.json")):
            q, _ = repo.load_question(f"{change_id}/{path.stem}")
            if q.lifecycle is QuestionLifecycle.OPEN:
                item = LoopNext("question", q.id, q.statement)
                return LoopProjection(primary=item, ready=[item])

    actions_dir = change_dir / "actions"
    if actions_dir.is_dir():
        for path in sorted(actions_dir.glob("A-*.json")):
            action, _ = repo.load_action(f"{change_id}/{path.stem}")
            if not action.tasks:
                item = LoopNext("action", action.id, action.objective)
                return LoopProjection(primary=item, ready=[item])

            sync = synchronize_action(action)
            blocked.extend(sync.blocked)
            parallelizable.extend(sync.parallelizable)
            for proj in sync.tasks:
                if proj.state is DerivedTaskState.READY:
                    ready_items.append(
                        LoopNext("task", proj.task_id, proj.description)
                    )
                elif proj.state is DerivedTaskState.ACTIVE:
                    # Active work is legitimate to continue — surface as primary preference
                    ready_items.insert(
                        0,
                        LoopNext("task", proj.task_id, f"[ACTIVE] {proj.description}"),
                    )

            if ready_items:
                return LoopProjection(
                    primary=ready_items[0],
                    ready=ready_items,
                    blocked_task_ids=blocked,
                    parallelizable_task_ids=parallelizable,
                )

            # All tasks completed for this action — continue scanning
            if sync.completed and len(sync.completed) == len(action.tasks):
                continue

    try:
        change, _ = repo.load_change(change_id)
    except FileNotFoundError:
        return LoopProjection(primary=None)
    review = LoopNext("change", change.id, f"Review status for {change.title}")
    return LoopProjection(primary=review, ready=[review])


def next_work(root: Path, change_id: str) -> LoopNext | None:
    """Backward-compatible single-item projection."""
    return project_next_work(root, change_id).primary
