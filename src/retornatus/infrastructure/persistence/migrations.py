"""Explicit schema migration registry (PRD §54)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from retornatus.domain.base import CURRENT_SCHEMA_VERSION

MigrationFn = Callable[[dict[str, Any]], dict[str, Any]]


class IncompatibleSchemaError(Exception):
    """Raised when an artifact schema cannot be migrated safely."""


class MigrationRegistry:
    """Deterministic, explicit migrations between schema versions."""

    def __init__(self) -> None:
        self._migrations: dict[tuple[int, int], MigrationFn] = {}

    def register(self, from_version: int, to_version: int, fn: MigrationFn) -> None:
        if to_version != from_version + 1:
            raise ValueError("Migrations must advance exactly one version")
        self._migrations[(from_version, to_version)] = fn

    def migrate(
        self,
        payload: dict[str, Any],
        *,
        target_version: int = CURRENT_SCHEMA_VERSION,
    ) -> dict[str, Any]:
        version = int(payload.get("schema_version", 0))
        if version == 0:
            raise IncompatibleSchemaError("Missing schema_version")
        if version > target_version:
            raise IncompatibleSchemaError(
                f"Artifact schema_version {version} is newer than supported {target_version}"
            )
        data = dict(payload)
        while version < target_version:
            key = (version, version + 1)
            if key not in self._migrations:
                raise IncompatibleSchemaError(
                    f"No migration registered from v{version} to v{version + 1}"
                )
            data = self._migrations[key](data)
            data["schema_version"] = version + 1
            version += 1
        return data


# V1 ships with identity support only — future versions register real migrations.
DEFAULT_REGISTRY = MigrationRegistry()
