"""Adversarial governance tests — attempts to violate the harness."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from retornatus.application.adaptation.service import (
    AdaptationService,
    HumanAuthorityError,
)
from retornatus.application.adaptation.skills import SkillService
from retornatus.application.assurance.evaluate import (
    AssuranceVerdict,
    build_claims_from_contract,
    evaluate_assurance,
)
from retornatus.application.assurance.evidence import EvidenceService
from retornatus.application.change.loop import next_work, project_next_work
from retornatus.application.change.readiness import (
    DependencyCycleError,
    synchronize_action,
)
from retornatus.application.change.workflow import ChangeWorkflow, TaskSpec
from retornatus.application.execution.context import assemble_execution_context
from retornatus.application.governance.bypass import BypassError, BypassService
from retornatus.application.governance.gates import gate_contract, gate_skill_research
from retornatus.application.question.loop import QuestionLoop, ResolutionIncompleteError
from retornatus.bootstrap.init import initialize_project
from retornatus.bootstrap.wake import wake_up
from retornatus.domain.enums import (
    AuthorityCategory,
    DemandKind,
)
from retornatus.domain.models import (
    Authority,
    Rule,
    Task,
)
from retornatus.infrastructure.index.sqlite_index import RetornatusIndex
from retornatus.infrastructure.persistence.repository import FileRepository


def _change(tmp_path: Path, **kwargs):
    initialize_project(tmp_path)
    defaults = dict(
        title="Health",
        demand_statement="Add health endpoint",
        demand_kind=DemandKind.CAPABILITY,
        situation="Ops needs liveness probe",
        what="GET /health returns 200 with status ok",
        done_criteria=[
            "Automated test covers GET /health",
            "Endpoint documented in docs/",
        ],
        action_objective="Implement health endpoint",
    )
    defaults.update(kwargs)
    return ChangeWorkflow(tmp_path).create_change(**defaults)


def test_contract_without_done_blocked(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    created = ChangeWorkflow(tmp_path).create_change(
        title="No done",
        demand_statement="Something vague",
        situation="unclear",
        what="maybe later",
        done_criteria=["ok"],
        activate_contract=True,
    )
    # Weak DONE / insufficient situation → contract not active
    assert created.contract.active is False
    assert not gate_contract(tmp_path, created.change.id).passed


def test_skill_without_research_blocked(tmp_path: Path) -> None:
    created = _change(tmp_path)
    skill, _ = SkillService(tmp_path).create_for_specialization(
        specialization="health patterns",
        change_id=created.change.id,
        action_id=created.action.id if created.action else None,
    )
    assert not gate_skill_research(tmp_path, skill.id).passed
    with pytest.raises(ValueError, match="research gate"):
        SkillService(tmp_path).activate(skill.id)


def test_evidence_for_wrong_claim_does_not_satisfy(tmp_path: Path) -> None:
    created = _change(tmp_path)
    claims = build_claims_from_contract(created.contract)
    assert len(claims) >= 2
    # Bind evidence to claim-2 only (docs), type test_result — wrong for claim-1 subject binding test
    EvidenceService(tmp_path).add(
        change_id=created.change.id,
        evidence_type="test_result",
        subject="/health",
        source="pytest",
        producer="adv",
        subject_state="passing",
        supports_claim_id=claims[1].id,  # wrong claim for health test
    )
    result = evaluate_assurance(
        claims=[claims[0]],
        evidence=EvidenceService(tmp_path).list_for_change(created.change.id),
    )
    assert result.verdict is not AssuranceVerdict.SATISFIED


def test_evidence_for_wrong_subject_does_not_satisfy(tmp_path: Path) -> None:
    created = _change(tmp_path)
    claims = build_claims_from_contract(created.contract)
    EvidenceService(tmp_path).add(
        change_id=created.change.id,
        evidence_type="test_result",
        subject="/metrics",
        source="pytest",
        producer="adv",
        subject_state="passing",
        supports_claim_id=claims[0].id,
    )
    result = evaluate_assurance(
        claims=[claims[0]],
        evidence=EvidenceService(tmp_path).list_for_change(created.change.id),
    )
    assert result.verdict is AssuranceVerdict.NOT_SATISFIED


def test_stale_evidence_does_not_establish_current_state(tmp_path: Path) -> None:
    created = _change(tmp_path)
    claims = build_claims_from_contract(created.contract)
    EvidenceService(tmp_path).add(
        change_id=created.change.id,
        evidence_type="test_result",
        subject="/health",
        source="pytest",
        producer="adv",
        subject_state="passing",
        supports_claim_id=claims[0].id,
    )
    result = evaluate_assurance(
        claims=[claims[0]],
        evidence=EvidenceService(tmp_path).list_for_change(created.change.id),
        current_subject_states={"/health": "failing"},
    )
    assert result.verdict is AssuranceVerdict.NOT_SATISFIED


def test_question_resolved_without_proof_blocked(tmp_path: Path) -> None:
    created = _change(tmp_path)
    loop = QuestionLoop(tmp_path)
    finding = loop.record_finding(
        change_id=created.change.id,
        observation="Health test is red",
    )
    q = loop.open_question(
        change_id=created.change.id,
        statement="Why is the health test failing?",
        finding_ids=[finding.id],
    )
    with pytest.raises(ResolutionIncompleteError):
        loop.resolve_question(q.id, summary="fixed")


def test_rule_candidate_activated_without_human_decision_blocked(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    adapt = AdaptationService(tmp_path)
    candidate = adapt.propose_rule_candidate(
        statement="Do not skip Assurance",
        applicability="assurance",
    )
    with pytest.raises(TypeError):
        adapt.activate_rule(candidate.id)  # type: ignore[call-arg]
    with pytest.raises(HumanAuthorityError):
        adapt.activate_rule(candidate.id, human_decision_id="D-9999")


def test_governance_bypass_without_reason_blocked(tmp_path: Path) -> None:
    created = _change(tmp_path)
    skill, _ = SkillService(tmp_path).create_for_specialization(
        specialization="x",
        change_id=created.change.id,
    )
    with pytest.raises(BypassError):
        SkillService(tmp_path).activate(skill.id, force=True, bypass_reason="")
    with pytest.raises(BypassError):
        BypassService(tmp_path).record_bypass(
            gate="skill-research",
            entity_id=skill.id,
            reason="  ",
        )


def test_task_depending_on_itself_blocked() -> None:
    with pytest.raises(ValidationError):
        Task(
            id="C-0001/T-001",
            description="self",
            depends_on=["C-0001/T-001"],
        )


def test_task_dependency_cycle_blocked(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    wf = ChangeWorkflow(tmp_path)
    created = wf.create_change(
        title="Cycle",
        demand_statement="Test cycles",
        situation="unit test",
        what="Detect cycles",
        done_criteria=["Cycle detection covered by unit tests"],
        action_objective="n/a",
        activate_contract=False,
    )
    with pytest.raises(DependencyCycleError):
        wf.create_action(
            change_id=created.change.id,
            objective="cyclic",
            success_conditions=["x"],
            task_specs=[
                TaskSpec("A", depends_on_indices=[1]),
                TaskSpec("B", depends_on_indices=[0]),
            ],
            action_number=2,
        )


def test_blocked_task_not_returned_by_loop_next(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    wf = ChangeWorkflow(tmp_path)
    created = wf.create_change(
        title="Deps",
        demand_statement="Ordered work with real dependency",
        situation="T2 needs T1",
        what="Tasks with depends_on",
        done_criteria=["Ready projection excludes blocked tasks"],
        action_objective="Sync tasks",
        task_specs=[
            TaskSpec("First"),
            TaskSpec("Second", depends_on_indices=[0]),
        ],
    )
    assert created.action is not None
    sync = synchronize_action(created.action)
    assert created.action.tasks[0].id in sync.ready
    assert created.action.tasks[1].id in sync.blocked

    nxt = next_work(tmp_path, created.change.id)
    assert nxt is not None
    assert nxt.id == created.action.tasks[0].id
    assert nxt.id not in sync.blocked

    projection = project_next_work(tmp_path, created.change.id)
    assert all(item.id not in sync.blocked for item in projection.ready)


def test_unrelated_rule_excluded_from_execution_context(tmp_path: Path) -> None:
    created = _change(tmp_path)
    repo = FileRepository(tmp_path)
    repo.save_rule(
        Rule(
            id="R-0001",
            statement="Always use TLS for payments API",
            applicability="payments stripe checkout",
            active=True,
            authority=Authority(category=AuthorityCategory.HUMAN),
        )
    )
    repo.save_rule(
        Rule(
            id="R-0002",
            statement="Health endpoints must not require auth",
            applicability="health endpoint liveness",
            active=True,
            authority=Authority(category=AuthorityCategory.HUMAN),
        )
    )
    assert created.action is not None
    ctx = assemble_execution_context(tmp_path, created.action.id)
    ids = {r.id for r in ctx.applicable_rules}
    assert "R-0001" not in ids
    assert "R-0002" in ids


def test_restart_after_deleting_sqlite_preserves_semantics(tmp_path: Path) -> None:
    created = _change(tmp_path)
    EvidenceService(tmp_path).add(
        change_id=created.change.id,
        evidence_type="test_result",
        subject="/health",
        source="pytest",
        producer="adv",
        subject_state="passing",
        supports_claim_id=build_claims_from_contract(created.contract)[0].id,
    )
    index = RetornatusIndex(tmp_path)
    assert index.rebuild() > 0
    index.paths.index_db.unlink()
    wake = wake_up(tmp_path, auto_init=False)
    assert created.change.id in wake.change_ids
    assert wake.index_entities > 0
    # Canonical evidence still loadable
    assert EvidenceService(tmp_path).list_for_change(created.change.id)


def test_independent_tasks_not_auto_chained(tmp_path: Path) -> None:
    created = _change(
        tmp_path,
        tasks=["Implement route", "Write docs", "Write tests"],
    )
    assert created.action is not None
    for task in created.action.tasks:
        assert task.depends_on == []
    sync = synchronize_action(created.action)
    assert len(sync.ready) == 3
    projection = project_next_work(tmp_path, created.change.id)
    assert len(projection.ready) == 3
