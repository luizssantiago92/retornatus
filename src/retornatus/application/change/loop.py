"""Derived construction loop — next ready unit of work (not a Loop Engine)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from retornatus.domain.enums import QuestionLifecycle, TaskLifecycle
from retornatus.infrastructure.persistence.repository import FileRepository


@dataclass
class LoopNext:
    kind: str
    id: str
    summary: str


def next_work(root: Path, change_id: str) -> LoopNext | None:
    """
    Project the next actionable item for a Change.

    Order: open Questions → PENDING tasks with deps satisfied → Action objective.
    Pattern before mechanism: this is a projection, not a Loop Engine (PRD §26).
    """
    repo = FileRepository(root)
    change_dir = repo.paths.change_dir(change_id)

    questions_dir = change_dir / "questions"
    if questions_dir.is_dir():
        for path in sorted(questions_dir.glob("Q-*.json")):
            q, _ = repo.load_question(f"{change_id}/{path.stem}")
            if q.lifecycle is QuestionLifecycle.OPEN:
                return LoopNext("question", q.id, q.statement)

    actions_dir = change_dir / "actions"
    if actions_dir.is_dir():
        for path in sorted(actions_dir.glob("A-*.json")):
            action, _ = repo.load_action(f"{change_id}/{path.stem}")
            completed = {
                t.id for t in action.tasks if t.lifecycle is TaskLifecycle.COMPLETED
            }
            for task in action.tasks:
                if task.lifecycle is not TaskLifecycle.PENDING:
                    continue
                if all(dep in completed for dep in task.depends_on):
                    return LoopNext("task", task.id, task.description)
            if action.tasks and all(
                t.lifecycle is TaskLifecycle.COMPLETED for t in action.tasks
            ):
                continue
            if not action.tasks:
                return LoopNext("action", action.id, action.objective)

    try:
        change, _ = repo.load_change(change_id)
    except FileNotFoundError:
        return None
    return LoopNext("change", change.id, f"Review status for {change.title}")
