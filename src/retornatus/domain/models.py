"""Pydantic domain entities for Retornatus V1 (PRD M1)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Self

from pydantic import Field, field_validator, model_validator

from retornatus.domain.base import DomainModel
from retornatus.domain.enums import (
    ActionOriginKind,
    AuthorityCategory,
    BoundaryRealization,
    DemandKind,
    QuestionDisposition,
    QuestionLifecycle,
    RuleApplicationMode,
    SkillSource,
    SkillStatus,
    TaskLifecycle,
)
from retornatus.domain.ids import (
    ActionId,
    ChangeId,
    EvidenceId,
    FindingId,
    LearningId,
    QuestionId,
    RuleId,
    SkillId,
    TaskId,
    change_id_of,
)
from retornatus.domain.relations import Relation


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Demand(DomainModel):
    """Expressed need for the project to change (PRD §10)."""

    statement: str = Field(min_length=1)
    kind: DemandKind = DemandKind.OTHER


class Authority(DomainModel):
    """Authority classification for a decision or Action (PRD §32)."""

    category: AuthorityCategory
    rationale: str | None = None


class Boundary(DomainModel):
    """A single technical or governance boundary (PRD §33)."""

    name: str = Field(min_length=1)
    kind: str = Field(
        min_length=1,
        description="e.g. filesystem, network, tools, environment, execution scope",
    )
    realization: BoundaryRealization
    description: str | None = None


class Boundaries(DomainModel):
    """Collection of effective boundaries for a context."""

    items: list[Boundary] = Field(default_factory=list)


class Task(DomainModel):
    """Bounded verifiable unit of work, embedded in Action by default (PRD §14)."""

    id: TaskId
    description: str = Field(min_length=1)
    lifecycle: TaskLifecycle = TaskLifecycle.PENDING
    depends_on: list[TaskId] = Field(default_factory=list)

    @model_validator(mode="after")
    def _deps_same_change(self) -> Self:
        own_change = change_id_of(self.id)
        for dep in self.depends_on:
            if change_id_of(dep) != own_change:
                raise ValueError(
                    f"Task dependency {dep!r} must belong to Change {own_change}"
                )
            if dep == self.id:
                raise ValueError("Task cannot depend on itself")
        return self


class Contract(DomainModel):
    """Authoritative WHAT + Constraints + DONE (PRD §12). Immutable once active."""

    change_id: ChangeId
    version: int = Field(default=1, ge=1)
    what: str = Field(min_length=1, description="Obligations / WHAT")
    constraints: list[str] = Field(default_factory=list)
    done_criteria: list[str] = Field(
        default_factory=list,
        description="Satisfaction conditions / DONE",
    )
    active: bool = False
    activated_at: datetime | None = None

    def activate(self) -> Contract:
        """Return an active Contract snapshot. Callers must not mutate further."""
        if self.active:
            raise ValueError("Contract is already active and immutable")
        if not self.done_criteria:
            raise ValueError("Contract requires at least one done criterion before activation")
        return self.model_copy(
            update={"active": True, "activated_at": _utc_now()},
        )


class Action(DomainModel):
    """Structured response to a Contract or Question (PRD §13)."""

    id: ActionId
    origin_kind: ActionOriginKind
    origin_ref: str = Field(
        min_length=1,
        description="Contract version ref or Question id",
    )
    objective: str = Field(min_length=1)
    scope: str | None = None
    constraints: list[str] = Field(default_factory=list)
    success_conditions: list[str] = Field(default_factory=list)
    authority: Authority
    tasks: list[Task] = Field(default_factory=list)
    relations: list[Relation] = Field(default_factory=list)

    @model_validator(mode="after")
    def _tasks_belong_to_action_change(self) -> Self:
        change = change_id_of(self.id)
        seen: set[str] = set()
        for task in self.tasks:
            if change_id_of(task.id) != change:
                raise ValueError(
                    f"Task {task.id!r} must belong to Change {change}"
                )
            if task.id in seen:
                raise ValueError(f"Duplicate Task id in Action: {task.id!r}")
            seen.add(task.id)
        if self.origin_kind == ActionOriginKind.QUESTION:
            # origin_ref should look like a Question id when origin is Question
            from retornatus.domain.ids import validate_question_id

            validate_question_id(self.origin_ref)
        return self


class Finding(DomainModel):
    """Relevant observation — not automatically work or failure (PRD §20)."""

    id: FindingId
    observation: str = Field(min_length=1)
    source: str | None = None
    observed_at: datetime = Field(default_factory=_utc_now)
    relations: list[Relation] = Field(default_factory=list)


class Resolution(DomainModel):
    """Embedded closure record for a Question (PRD §22)."""

    summary: str = Field(min_length=1)
    established_at: datetime = Field(default_factory=_utc_now)
    evidence_ids: list[EvidenceId] = Field(default_factory=list)


class Question(DomainModel):
    """Structured problem grounded in Findings (PRD §21)."""

    id: QuestionId
    statement: str = Field(min_length=1)
    grounded_in: list[FindingId] = Field(min_length=1)
    lifecycle: QuestionLifecycle = QuestionLifecycle.OPEN
    disposition: QuestionDisposition = QuestionDisposition.NONE
    resolution: Resolution | None = None
    relations: list[Relation] = Field(default_factory=list)

    @model_validator(mode="after")
    def _grounding_and_resolution(self) -> Self:
        change = change_id_of(self.id)
        for finding_id in self.grounded_in:
            if change_id_of(finding_id) != change:
                raise ValueError(
                    f"Finding {finding_id!r} must belong to Change {change}"
                )
        if self.lifecycle == QuestionLifecycle.RESOLVED and self.resolution is None:
            raise ValueError("Resolved Question requires a Resolution record")
        if self.lifecycle == QuestionLifecycle.OPEN and self.resolution is not None:
            raise ValueError("Open Question must not carry a Resolution")
        return self


class Evidence(DomainModel):
    """Attributable observable information (PRD §23)."""

    id: EvidenceId
    type: str = Field(min_length=1)
    subject: str = Field(min_length=1, description="Subject / claim under observation")
    source: str = Field(min_length=1)
    producer: str = Field(min_length=1)
    observed_at: datetime = Field(default_factory=_utc_now)
    subject_state: str | None = None
    relations: list[Relation] = Field(default_factory=list)


class Rule(DomainModel):
    """Authoritative project constraint (PRD §34)."""

    id: RuleId
    statement: str = Field(min_length=1)
    applicability: str = Field(min_length=1)
    active: bool = False
    authority: Authority = Field(
        default_factory=lambda: Authority(category=AuthorityCategory.HUMAN)
    )
    modes: list[RuleApplicationMode] = Field(default_factory=list)
    relations: list[Relation] = Field(default_factory=list)

    @field_validator("authority")
    @classmethod
    def _authoritative_requires_human(cls, value: Authority) -> Authority:
        # Creating/activating authoritative Rules requires human validation (PRD §32).
        return value

    @model_validator(mode="after")
    def _active_requires_human_authority(self) -> Self:
        if self.active and self.authority.category != AuthorityCategory.HUMAN:
            raise ValueError(
                "Active authoritative Rule requires HUMAN authority validation"
            )
        return self


class LearningMetadata(DomainModel):
    """Structured metadata for a Learning Markdown artifact (PRD §37–§38)."""

    id: LearningId
    title: str = Field(min_length=1)
    summary: str | None = None
    tags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=_utc_now)
    relations: list[Relation] = Field(default_factory=list)


class Skill(DomainModel):
    """
    Reusable procedural knowledge for a class of engineering work (PRD §39).

    Skills are created for specialization needs (often one per Change feature),
    consumed as stable snapshots during Execution, and evolved via Adaptation.
    Retornatus owns structure; agents research and fill procedure content.
    """

    id: SkillId
    name: str = Field(min_length=1, description="Short machine-friendly name")
    title: str = Field(min_length=1)
    description: str = Field(
        min_length=1,
        description="When to activate this skill (progressive disclosure)",
    )
    specialization: str = Field(
        min_length=1,
        description="The concrete specialization need that justified creation",
    )
    status: SkillStatus = SkillStatus.DRAFT
    source: SkillSource = SkillSource.RESEARCHED
    version: int = Field(default=1, ge=1)
    change_id: ChangeId | None = None
    action_id: ActionId | None = None
    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime = Field(default_factory=_utc_now)
    relations: list[Relation] = Field(default_factory=list)


class Change(DomainModel):
    """Bounded engineering context for a coherent project change (PRD §9)."""

    id: ChangeId
    title: str = Field(min_length=1)
    demand: Demand
    active_contract_version: int | None = Field(
        default=None,
        ge=1,
        description="Version number of the active Contract, if any",
    )
    relations: list[Relation] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=_utc_now)
