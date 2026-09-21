"""Task lifecycle transitions within an Action (PRD §14).

Durable lifecycle is PENDING/ACTIVE/COMPLETED/FAILED.
READY remains derived — never stored.
"""

from __future__ import annotations

from pathlib import Path

from retornatus.domain.enums import TaskLifecycle
from retornatus.domain.ids import change_id_of
from retornatus.domain.models import Action, Task
from retornatus.infrastructure.persistence.repository import FileRepository


class TaskLifecycleError(ValueError):
    """Invalid Task lifecycle transition."""


_ALLOWED: dict[TaskLifecycle, set[TaskLifecycle]] = {
    TaskLifecycle.PENDING: {TaskLifecycle.ACTIVE, TaskLifecycle.FAILED},
    TaskLifecycle.ACTIVE: {
        TaskLifecycle.COMPLETED,
        TaskLifecycle.FAILED,
        TaskLifecycle.PENDING,  # release back to pool
    },
    TaskLifecycle.FAILED: {TaskLifecycle.PENDING, TaskLifecycle.ACTIVE},
    TaskLifecycle.COMPLETED: set(),  # terminal unless explicit reopen
}


def _find_task(action: Action, task_id: str) -> Task:
    for task in action.tasks:
        if task.id == task_id:
            return task
    raise TaskLifecycleError(f"Task {task_id} not found in Action {action.id}")


class TaskService:
    def __init__(self, root: Path) -> None:
        self.repo = FileRepository(root)

    def set_lifecycle(
        self,
        task_id: str,
        lifecycle: TaskLifecycle,
        *,
        force: bool = False,
    ) -> Action:
        """
        Update embedded Task lifecycle on its owning Action.

        ``force`` allows COMPLETED → PENDING reopen for correction.
        """
        change_id = change_id_of(task_id)
        # Find owning action by scanning
        action = self._find_action_for_task(change_id, task_id)
        action, rev = self.repo.load_action(action.id)
        task = _find_task(action, task_id)
        current = task.lifecycle
        if current is lifecycle:
            return action
        allowed = set(_ALLOWED.get(current, set()))
        if force and current is TaskLifecycle.COMPLETED:
            allowed.add(TaskLifecycle.PENDING)
            allowed.add(TaskLifecycle.ACTIVE)
        if lifecycle not in allowed:
            raise TaskLifecycleError(
                f"Cannot transition {task_id} {current.value} → {lifecycle.value}"
            )
        updated_tasks = [
            t.model_copy(update={"lifecycle": lifecycle}) if t.id == task_id else t
            for t in action.tasks
        ]
        updated = action.model_copy(update={"tasks": updated_tasks})
        self.repo.save_action(updated, expected=rev)
        return updated

    def start(self, task_id: str) -> Action:
        return self.set_lifecycle(task_id, TaskLifecycle.ACTIVE)

    def complete(self, task_id: str) -> Action:
        return self.set_lifecycle(task_id, TaskLifecycle.COMPLETED)

    def fail(self, task_id: str) -> Action:
        return self.set_lifecycle(task_id, TaskLifecycle.FAILED)

    def reopen(self, task_id: str) -> Action:
        return self.set_lifecycle(task_id, TaskLifecycle.PENDING, force=True)

    def _find_action_for_task(self, change_id: str, task_id: str) -> Action:
        actions_dir = self.repo.paths.change_dir(change_id) / "actions"
        if not actions_dir.is_dir():
            raise TaskLifecycleError(f"No actions for {change_id}")
        for path in sorted(actions_dir.glob("A-*.json")):
            action, _ = self.repo.load_action(f"{change_id}/{path.stem}")
            if any(t.id == task_id for t in action.tasks):
                return action
        raise TaskLifecycleError(f"No Action owns Task {task_id}")
