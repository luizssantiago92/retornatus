"""Base domain model with schema versioning (PRD §54)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

CURRENT_SCHEMA_VERSION = 1


class DomainModel(BaseModel):
    """Canonical structured artifact base — every artifact carries schema_version."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    schema_version: int = Field(
        default=CURRENT_SCHEMA_VERSION,
        ge=1,
        description="Explicit schema version for migration registry (PRD §54).",
    )
