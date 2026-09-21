"""Domain model validation tests (M1)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from retornatus.domain import (
    CURRENT_SCHEMA_VERSION,
    Action,
    ActionOriginKind,
    Authority,
    AuthorityCategory,
    Boundary,
    BoundaryRealization,
    Change,
    Contract,
    Demand,
    DemandKind,
    Evidence,
    Finding,
    LearningMetadata,
    Question,
    QuestionLifecycle,
    Relation,
    RelationType,
    Resolution,
    Rule,
    Task,
    TaskLifecycle,
)


def _authority() -> Authority:
    return Authority(category=AuthorityCategory.DELEGATED, rationale="routine work")


def test_change_and_demand_carry_schema_version() -> None:
    change = Change(
        id="C-0001",
        title="Add init command",
        demand=Demand(statement="Bootstrap .retornatus", kind=DemandKind.CAPABILITY),
    )
    assert change.schema_version == CURRENT_SCHEMA_VERSION
    assert change.demand.kind is DemandKind.CAPABILITY


def test_contract_activation_requires_done_criteria() -> None:
    contract = Contract(
        change_id="C-0001",
        what="Ship retornatus init",
        constraints=["Python 3.11+"],
    )
    with pytest.raises(ValueError, match="done criterion"):
        contract.activate()

    active = Contract(
        change_id="C-0001",
        what="Ship retornatus init",
        done_criteria=["uv run retornatus init creates .retornatus"],
    ).activate()
    assert active.active is True
    assert active.activated_at is not None
    with pytest.raises(ValueError, match="already active"):
        active.activate()


def test_action_with_embedded_tasks() -> None:
    action = Action(
        id="C-0001/A-001",
        origin_kind=ActionOriginKind.CONTRACT,
        origin_ref="contract@v1",
        objective="Implement domain models",
        success_conditions=["Models validate sample artifacts"],
        authority=_authority(),
        tasks=[
            Task(
                id="C-0001/T-001",
                description="Define identifiers",
                lifecycle=TaskLifecycle.COMPLETED,
            ),
            Task(
                id="C-0001/T-002",
                description="Define entities",
                depends_on=["C-0001/T-001"],
            ),
        ],
        relations=[Relation(type=RelationType.SATISFIES, target_id="C-0001")],
    )
    assert len(action.tasks) == 2


def test_action_rejects_cross_change_task() -> None:
    with pytest.raises(ValidationError):
        Action(
            id="C-0001/A-001",
            origin_kind=ActionOriginKind.CONTRACT,
            origin_ref="contract@v1",
            objective="x",
            authority=_authority(),
            tasks=[Task(id="C-0002/T-001", description="wrong change")],
        )


def test_question_requires_finding_grounding() -> None:
    with pytest.raises(ValidationError):
        Question(id="C-0001/Q-001", statement="Why failing?", grounded_in=[])

    finding = Finding(id="C-0001/F-001", observation="Test suite red on Windows")
    question = Question(
        id="C-0001/Q-001",
        statement="Path separator handling?",
        grounded_in=[finding.id],
        relations=[Relation(type=RelationType.GROUNDED_IN, target_id=finding.id)],
    )
    assert question.lifecycle is QuestionLifecycle.OPEN

    resolved = question.model_copy(
        update={
            "lifecycle": QuestionLifecycle.RESOLVED,
            "resolution": Resolution(
                summary="Normalized paths via pathlib",
                evidence_ids=["C-0001/E-001"],
            ),
        }
    )
    assert resolved.resolution is not None


def test_evidence_minimal_structure() -> None:
    evidence = Evidence(
        id="C-0001/E-001",
        type="test_result",
        subject="M1 domain models",
        source="pytest",
        producer="ci",
        subject_state="passing",
        relations=[Relation(type=RelationType.SUPPORTS, target_id="C-0001/A-001")],
    )
    assert evidence.schema_version == CURRENT_SCHEMA_VERSION


def test_rule_active_requires_human_authority() -> None:
    with pytest.raises(ValidationError, match="HUMAN"):
        Rule(
            id="R-0001",
            statement="Do not commit secrets",
            applicability="all changes",
            active=True,
            authority=Authority(category=AuthorityCategory.DELEGATED),
        )

    rule = Rule(
        id="R-0001",
        statement="Do not commit secrets",
        applicability="all changes",
        active=True,
        authority=Authority(category=AuthorityCategory.HUMAN, rationale="policy"),
    )
    assert rule.active is True


def test_learning_metadata_and_boundaries() -> None:
    learning = LearningMetadata(
        id="L-0001",
        title="Prefer pathlib on Windows",
        summary="Avoid hardcoded separators",
        tags=["windows", "paths"],
        relations=[Relation(type=RelationType.RELEVANT_TO, target_id="C-0001")],
    )
    boundary = Boundary(
        name="no-network",
        kind="network",
        realization=BoundaryRealization.ADVISORY,
    )
    assert learning.id == "L-0001"
    assert boundary.realization is BoundaryRealization.ADVISORY


def test_round_trip_json() -> None:
    change = Change(
        id="C-0001",
        title="Domain core",
        demand=Demand(statement="Model the domain", kind=DemandKind.CAPABILITY),
    )
    restored = Change.model_validate_json(change.model_dump_json())
    assert restored == change
