"""M2 persistence: atomic writes and optimistic concurrency."""

from __future__ import annotations

from pathlib import Path

import pytest

from retornatus.bootstrap.init import initialize_project
from retornatus.domain.enums import DemandKind
from retornatus.domain.models import Change, Demand
from retornatus.infrastructure.persistence.atomic import atomic_write_text
from retornatus.infrastructure.persistence.concurrency import ConcurrencyConflict
from retornatus.infrastructure.persistence.migrations import (
    IncompatibleSchemaError,
    MigrationRegistry,
)
from retornatus.infrastructure.persistence.repository import FileRepository


def test_atomic_write_leaves_no_partial_canonical(tmp_path: Path) -> None:
    target = tmp_path / "artifact.json"
    atomic_write_text(target, '{"ok": true}\n')
    assert target.read_text(encoding="utf-8") == '{"ok": true}\n'
    assert list(tmp_path.glob(".artifact.json.*.tmp")) == []


def test_change_round_trip_and_concurrency(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    repo = FileRepository(tmp_path)
    change = Change(
        id="C-0001",
        title="Persist",
        demand=Demand(statement="Save change", kind=DemandKind.CAPABILITY),
    )
    repo.save_change(change)
    loaded, rev = repo.load_change("C-0001")
    assert loaded.title == "Persist"

    updated = loaded.model_copy(update={"title": "Persist v2"})
    repo.save_change(updated, expected=rev)
    again, _ = repo.load_change("C-0001")
    assert again.title == "Persist v2"

    with pytest.raises(ConcurrencyConflict):
        repo.save_change(updated, expected=rev)


def test_incompatible_schema_fails_clearly() -> None:
    registry = MigrationRegistry()
    with pytest.raises(IncompatibleSchemaError):
        registry.migrate({"schema_version": 99})
