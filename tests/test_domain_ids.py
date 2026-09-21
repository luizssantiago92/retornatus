"""Domain identifier and relation vocabulary tests (M1)."""

from __future__ import annotations

import pytest
from pydantic import TypeAdapter, ValidationError

from retornatus.domain.ids import (
    ActionId,
    ChangeId,
    LearningId,
    change_id_of,
    format_change_id,
    format_owned_id,
    format_project_id,
)
from retornatus.domain.relations import Relation, RelationType


def test_project_and_change_id_formats() -> None:
    assert format_project_id("L", 1) == "L-0001"
    assert format_change_id(12) == "C-0012"
    assert format_owned_id("C-0001", "A", 1) == "C-0001/A-001"


def test_id_type_adapters_accept_valid() -> None:
    assert TypeAdapter(LearningId).validate_python("L-0001") == "L-0001"
    assert TypeAdapter(ChangeId).validate_python("C-0001") == "C-0001"
    assert TypeAdapter(ActionId).validate_python("C-0001/A-001") == "C-0001/A-001"


@pytest.mark.parametrize(
    ("adapter", "value"),
    [
        (TypeAdapter(LearningId), "R-0001"),
        (TypeAdapter(ChangeId), "A-0001"),
        (TypeAdapter(ActionId), "C-0001/T-001"),
        (TypeAdapter(ActionId), "C-0001/A-1"),
    ],
)
def test_id_type_adapters_reject_invalid(adapter: TypeAdapter[str], value: str) -> None:
    with pytest.raises(ValidationError):
        adapter.validate_python(value)


def test_change_id_of_owned() -> None:
    assert change_id_of("C-0042/E-010") == "C-0042"


def test_relation_vocabulary() -> None:
    rel = Relation(type=RelationType.GROUNDED_IN, target_id="C-0001/F-001")
    assert rel.type is RelationType.GROUNDED_IN
    assert set(RelationType) >= {
        RelationType.DERIVED_FROM,
        RelationType.GROUNDED_IN,
        RelationType.PRODUCES,
        RelationType.SATISFIES,
        RelationType.SUPPORTS,
        RelationType.CHALLENGES,
        RelationType.RESOLVES,
        RelationType.APPLIES_TO,
        RelationType.SUPERSEDES,
        RelationType.RELEVANT_TO,
    }
