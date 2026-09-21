"""Execution context assembly (PRD M5) — assembled, not inherited."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from pydantic import Field

from retornatus.domain.base import DomainModel
from retornatus.domain.models import (
    Action,
    Authority,
    Boundaries,
    Boundary,
    LearningMetadata,
    Rule,
)
from retornatus.domain.enums import BoundaryRealization
from retornatus.infrastructure.persistence.repository import FileRepository


class ExecutionContext(DomainModel):
    """Stable assembled context for a bounded execution."""

    action_id: str
    assembled_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    objective: str
    success_conditions: list[str] = Field(default_factory=list)
    authority: Authority
    boundaries: Boundaries = Field(default_factory=Boundaries)
    applicable_rules: list[Rule] = Field(default_factory=list)
    relevant_learnings: list[LearningMetadata] = Field(default_factory=list)
    skill_ids: list[str] = Field(default_factory=list)
    capability_requirements: list[str] = Field(default_factory=list)


def assemble_execution_context(
    root: Path,
    action_id: str,
    *,
    skill_ids: list[str] | None = None,
    capability_requirements: list[str] | None = None,
    query: str | None = None,
) -> ExecutionContext:
    repo = FileRepository(root)
    action, _ = repo.load_action(action_id)
    rules = [r for r in repo.list_rules() if r.active]
    learnings = repo.list_learnings()
    if query:
        q = query.lower()
        learnings = [
            L
            for L in learnings
            if q in L.title.lower()
            or (L.summary and q in L.summary.lower())
            or any(q in t.lower() for t in L.tags)
        ]
    else:
        learnings = learnings[:5]

    boundaries = Boundaries(
        items=[
            Boundary(
                name="repository-root",
                kind="filesystem",
                realization=BoundaryRealization.ADVISORY,
                description=str(root.resolve()),
            )
        ]
    )

    return ExecutionContext(
        action_id=action.id,
        objective=action.objective,
        success_conditions=action.success_conditions,
        authority=action.authority,
        boundaries=boundaries,
        applicable_rules=rules,
        relevant_learnings=learnings,
        skill_ids=skill_ids or [],
        capability_requirements=capability_requirements or [],
    )
