"""Canonical relationship vocabulary (PRD §50)."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class RelationType(str, Enum):
    """Small canonical relation set — no graph database required."""

    DERIVED_FROM = "DERIVED_FROM"
    GROUNDED_IN = "GROUNDED_IN"
    PRODUCES = "PRODUCES"
    SATISFIES = "SATISFIES"
    SUPPORTS = "SUPPORTS"
    CHALLENGES = "CHALLENGES"
    RESOLVES = "RESOLVES"
    APPLIES_TO = "APPLIES_TO"
    SUPERSEDES = "SUPERSEDES"
    RELEVANT_TO = "RELEVANT_TO"


class Relation(BaseModel):
    """A directed relationship belonging to canonical entity metadata."""

    model_config = ConfigDict(extra="forbid")

    type: RelationType
    target_id: str = Field(min_length=1, description="Identifier of the related entity.")
    note: str | None = None
