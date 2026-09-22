"""Shared enums for the Retornatus domain (PRD M1)."""

from __future__ import annotations

from enum import Enum


class AuthorityCategory(str, Enum):
    """Which decisions require human judgment (PRD §32)."""

    RULED = "RULED"
    DELEGATED = "DELEGATED"
    HUMAN = "HUMAN"


class BoundaryRealization(str, Enum):
    """How a boundary is realized (PRD §33)."""

    ENFORCED = "ENFORCED"
    ADVISORY = "ADVISORY"
    UNAVAILABLE = "UNAVAILABLE"


class TaskLifecycle(str, Enum):
    """Minimal Task lifecycle (PRD §14)."""

    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class QuestionLifecycle(str, Enum):
    """Minimal Question lifecycle (PRD §21)."""

    OPEN = "OPEN"
    RESOLVED = "RESOLVED"


class QuestionDisposition(str, Enum):
    """Non-lifecycle dispositions for Questions (PRD §21)."""

    NONE = "NONE"
    DUPLICATE = "DUPLICATE"
    SUPERSEDED = "SUPERSEDED"
    NOT_ACTIONABLE = "NOT_ACTIONABLE"


class ActionOriginKind(str, Enum):
    """Where an Action originates (PRD §13)."""

    CONTRACT = "CONTRACT"
    QUESTION = "QUESTION"


class RuleApplicationMode(str, Enum):
    """How a Rule may apply (PRD §34)."""

    INSTRUCTIONAL = "INSTRUCTIONAL"
    ASSURABLE = "ASSURABLE"
    ENFORCEABLE = "ENFORCEABLE"


class DemandKind(str, Enum):
    """Kinds of expressed need (PRD §10)."""

    CAPABILITY = "CAPABILITY"
    BUG = "BUG"
    REFACTOR = "REFACTOR"
    MIGRATION = "MIGRATION"
    BEHAVIOR = "BEHAVIOR"
    MAINTENANCE = "MAINTENANCE"
    SECURITY = "SECURITY"
    OTHER = "OTHER"


class ComplexityLane(str, Enum):
    """Ceremony lane — complexity must be earned (not a Spec Guardrails clone)."""

    QUICK = "QUICK"
    STANDARD = "STANDARD"
    COMPLEX = "COMPLEX"


class SkillStatus(str, Enum):
    """Skill lifecycle (PRD §39 — evolution belongs to Adaptation)."""

    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"


class SkillSource(str, Enum):
    """Where a Skill came from."""

    RESEARCHED = "RESEARCHED"
    PROJECT = "PROJECT"
    NATIVE = "NATIVE"
    IMPORTED = "IMPORTED"


class DecisionKind(str, Enum):
    """Kinds of durable human decisions (local harness boundary)."""

    APPROVE_RULE_ACTIVATION = "APPROVE_RULE_ACTIVATION"
    GOVERNANCE_BYPASS = "GOVERNANCE_BYPASS"
    CONTRACT_APPROVAL = "CONTRACT_APPROVAL"
    OTHER = "OTHER"


class DerivedTaskState(str, Enum):
    """Derived readiness projection — not durable truth (PRD §16)."""

    READY = "READY"
    BLOCKED = "BLOCKED"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
