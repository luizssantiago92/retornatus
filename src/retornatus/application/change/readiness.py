"""Derived Task readiness and dependency synchronization (PRD §15–§16).

Readiness is projected — never stored as durable READY.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from retornatus.domain.enums import DerivedTaskState, TaskLifecycle
from retornatus.domain.models import Action, Task


class DependencyCycleError(ValueError):
    """Task depends_on graph contains a cycle."""


def detect_dependency_cycles(tasks: list[Task]) -> list[list[str]]:
    """Return list of cycles (each cycle as task id list). Empty if acyclic."""
    by_id = {t.id: t for t in tasks}
    cycles: list[list[str]] = []
    visiting: set[str] = set()
    visited: set[str] = set()
    stack: list[str] = []

    def dfs(node: str) -> None:
        if node in visited:
            return
        if node in visiting:
            if node in stack:
                idx = stack.index(node)
                cycles.append(stack[idx:] + [node])
            return
        visiting.add(node)
        stack.append(node)
        task = by_id.get(node)
        if task:
            for dep in task.depends_on:
                if dep not in by_id:
                    # Missing dep is a block, not a cycle
                    continue
                dfs(dep)
        stack.pop()
        visiting.discard(node)
        visited.add(node)

    for task in tasks:
        dfs(task.id)
    return cycles


def assert_acyclic(tasks: list[Task]) -> None:
    cycles = detect_dependency_cycles(tasks)
    if cycles:
        rendered = "; ".join(" → ".join(c) for c in cycles)
        raise DependencyCycleError(f"Task dependency cycle detected: {rendered}")


@dataclass
class TaskProjection:
    task_id: str
    state: DerivedTaskState
    description: str
    blocked_by: list[str] = field(default_factory=list)
    resource_conflicts: list[str] = field(default_factory=list)


@dataclass
class SyncProjection:
    """Synchronization projection for an Action's tasks."""

    action_id: str
    tasks: list[TaskProjection]
    ready: list[str]
    blocked: list[str]
    active: list[str]
    completed: list[str]
    failed: list[str]
    parallelizable: list[str]
    resource_conflict_pairs: list[tuple[str, str]] = field(default_factory=list)


def _terminal_completed(lifecycle: TaskLifecycle) -> bool:
    return lifecycle is TaskLifecycle.COMPLETED


def project_task_state(
    task: Task,
    *,
    tasks_by_id: dict[str, Task],
    active_resource_owners: dict[str, str],
) -> TaskProjection:
    if task.lifecycle is TaskLifecycle.COMPLETED:
        return TaskProjection(task.id, DerivedTaskState.COMPLETED, task.description)
    if task.lifecycle is TaskLifecycle.FAILED:
        return TaskProjection(task.id, DerivedTaskState.FAILED, task.description)
    if task.lifecycle is TaskLifecycle.ACTIVE:
        return TaskProjection(task.id, DerivedTaskState.ACTIVE, task.description)

    blocked_by: list[str] = []
    for dep in task.depends_on:
        dep_task = tasks_by_id.get(dep)
        if dep_task is None:
            blocked_by.append(dep)
        elif not _terminal_completed(dep_task.lifecycle):
            blocked_by.append(dep)

    conflicts: list[str] = []
    for resource in task.resources:
        owner = active_resource_owners.get(resource)
        if owner and owner != task.id:
            conflicts.append(resource)

    if blocked_by or conflicts:
        return TaskProjection(
            task.id,
            DerivedTaskState.BLOCKED,
            task.description,
            blocked_by=blocked_by,
            resource_conflicts=conflicts,
        )
    return TaskProjection(task.id, DerivedTaskState.READY, task.description)


def synchronize_action(action: Action) -> SyncProjection:
    """
    Derive READY / BLOCKED / ACTIVE / COMPLETED / FAILED for Action tasks.

    Dependencies determine readiness; they do not prescribe executor.
    Parallelizable does not mean should be parallelized.
    Resource conflicts constrain concurrency without inventing fake depends_on.
    """
    assert_acyclic(action.tasks)
    by_id = {t.id: t for t in action.tasks}
    active_owners: dict[str, str] = {}
    for task in action.tasks:
        if task.lifecycle is TaskLifecycle.ACTIVE:
            for resource in task.resources:
                # first active owner wins for conflict reporting
                active_owners.setdefault(resource, task.id)

    projections = [
        project_task_state(t, tasks_by_id=by_id, active_resource_owners=active_owners)
        for t in action.tasks
    ]

    ready = [p.task_id for p in projections if p.state is DerivedTaskState.READY]
    blocked = [p.task_id for p in projections if p.state is DerivedTaskState.BLOCKED]
    active = [p.task_id for p in projections if p.state is DerivedTaskState.ACTIVE]
    completed = [p.task_id for p in projections if p.state is DerivedTaskState.COMPLETED]
    failed = [p.task_id for p in projections if p.state is DerivedTaskState.FAILED]

    conflict_pairs: list[tuple[str, str]] = []
    ready_tasks = [by_id[tid] for tid in ready]
    for i, a in enumerate(ready_tasks):
        for b in ready_tasks[i + 1 :]:
            shared = set(a.resources) & set(b.resources)
            if shared:
                conflict_pairs.append((a.id, b.id))

    # Parallelizable = ready tasks that do not share resources with each other
    conflicted: set[str] = set()
    for left_id, right_id in conflict_pairs:
        conflicted.add(left_id)
        conflicted.add(right_id)
    parallelizable = [tid for tid in ready if tid not in conflicted]

    return SyncProjection(
        action_id=action.id,
        tasks=projections,
        ready=ready,
        blocked=blocked,
        active=active,
        completed=completed,
        failed=failed,
        parallelizable=parallelizable,
        resource_conflict_pairs=conflict_pairs,
    )
