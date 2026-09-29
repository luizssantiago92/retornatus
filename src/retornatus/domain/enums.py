"""Shared enums for the Retornatus domain (PRD M1)."""

from __future__ import annotations

from enum import StrEnum


class AuthorityCategory(StrEnum):
    """Which decisions require human judgment (PRD §32)."""

    RULED = "RULED"
    DELEGATED = "DELEGATED"
    HUMAN = "HUMAN"


class BoundaryRealization(StrEnum):
    """How a boundary is realized (PRD §33)."""

    ENFORCED = "ENFORCED"
    ADVISORY = "ADVISORY"
    UNAVAILABLE = "UNAVAILABLE"


class TaskLifecycle(StrEnum):
    """Minimal Task lifecycle (PRD §14)."""

    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class QuestionLifecycle(StrEnum):
    """Minimal Question lifecycle (PRD §21)."""

    OPEN = "OPEN"
    RESOLVED = "RESOLVED"


class QuestionDisposition(StrEnum):
    """Non-lifecycle dispositions for Questions (PRD §21)."""

    NONE = "NONE"
    DUPLICATE = "DUPLICATE"
    SUPERSEDED = "SUPERSEDED"
    NOT_ACTIONABLE = "NOT_ACTIONABLE"


class ActionOriginKind(StrEnum):
    """Where an Action originates (PRD §13)."""

    CONTRACT = "CONTRACT"
    QUESTION = "QUESTION"


class RuleApplicationMode(StrEnum):
    """How a Rule may apply (PRD §34)."""

    INSTRUCTIONAL = "INSTRUCTIONAL"
    ASSURABLE = "ASSURABLE"
    ENFORCEABLE = "ENFORCEABLE"


class DemandKind(StrEnum):
    """Kinds of expressed need (PRD §10)."""

    CAPABILITY = "CAPABILITY"
    BUG = "BUG"
    REFACTOR = "REFACTOR"
    MIGRATION = "MIGRATION"
    BEHAVIOR = "BEHAVIOR"
    MAINTENANCE = "MAINTENANCE"
    SECURITY = "SECURITY"
    OTHER = "OTHER"


class ComplexityLane(StrEnum):
    """Ceremony lane — complexity must be earned (not a Spec Guardrails clone)."""

    QUICK = "QUICK"
    STANDARD = "STANDARD"
    COMPLEX = "COMPLEX"


class SkillStatus(StrEnum):
    """Skill lifecycle (PRD §39 — evolution belongs to Adaptation)."""

    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"


class SkillSource(StrEnum):
    """Where a Skill came from."""

    RESEARCHED = "RESEARCHED"
    PROJECT = "PROJECT"
    NATIVE = "NATIVE"
    IMPORTED = "IMPORTED"


class EvidenceProvenance(StrEnum):
    """How an Evidence record was produced.

    ``self_reported`` is whatever an agent or human typed into ``evidence add``.
    ``executed`` means Retornatus itself ran the command (``evidence run``).
    """

    SELF_REPORTED = "self_reported"
    EXECUTED = "executed"


class DecisionKind(StrEnum):
    """Kinds of durable human decisions (local harness boundary)."""

    APPROVE_RULE_ACTIVATION = "APPROVE_RULE_ACTIVATION"
    GOVERNANCE_BYPASS = "GOVERNANCE_BYPASS"
    CONTRACT_APPROVAL = "CONTRACT_APPROVAL"
    OTHER = "OTHER"


class DerivedTaskState(StrEnum):
    """Derived readiness projection — not durable truth (PRD §16)."""

    READY = "READY"
    BLOCKED = "BLOCKED"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
