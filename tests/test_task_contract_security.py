"""Task lifecycle, Contract reopen, skill-need, and security review dogfood."""

from __future__ import annotations

from pathlib import Path

import pytest

from retornatus.application.adaptation.skill_need import assess_skill_need
from retornatus.application.assurance.evaluate import (
    AssuranceVerdict,
    build_claims_from_contract,
)
from retornatus.application.assurance.evidence import EvidenceService
from retornatus.application.assurance.independent import (
    evaluate_change_assurance,
    plan_independent_assurance,
    record_independent_review_evidence,
)
from retornatus.application.change.loop import next_work, project_next_work
from retornatus.application.change.tasks import TaskLifecycleError, TaskService
from retornatus.application.change.workflow import ChangeWorkflow, TaskSpec
from retornatus.application.execution.brownfield_fixture import seed_brownfield_service
from retornatus.application.execution.host_record import HostExecutionService
from retornatus.bootstrap.init import initialize_project
from retornatus.domain.enums import DemandKind, TaskLifecycle
from retornatus.infrastructure.persistence.repository import FileRepository


def test_task_lifecycle_and_loop_progression(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    created = ChangeWorkflow(tmp_path).create_change(
        title="Tasks",
        demand_statement="Ordered work",
        situation="T2 depends on T1",
        what="Complete dependent tasks",
        done_criteria=["Both tasks completed via lifecycle CLI semantics"],
        action_objective="Do the work",
        task_specs=[
            TaskSpec("First"),
            TaskSpec("Second", depends_on_indices=[0]),
        ],
    )
    assert created.action is not None
    t1, t2 = created.action.tasks[0].id, created.action.tasks[1].id
    svc = TaskService(tmp_path)

    assert next_work(tmp_path, created.change.id).id == t1
    svc.start(t1)
    action, _ = FileRepository(tmp_path).load_action(created.action.id)
    assert action.tasks[0].lifecycle is TaskLifecycle.ACTIVE

    with pytest.raises(TaskLifecycleError):
        svc.complete(t2)  # still PENDING / blocked — must start first? Actually PENDING→COMPLETE not allowed
    svc.complete(t1)

    projection = project_next_work(tmp_path, created.change.id)
    assert projection.primary is not None
    assert projection.primary.id == t2

    svc.start(t2)
    svc.complete(t2)
    action, _ = FileRepository(tmp_path).load_action(created.action.id)
    assert all(t.lifecycle is TaskLifecycle.COMPLETED for t in action.tasks)


def test_contract_reopen_archives_prior_version(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    wf = ChangeWorkflow(tmp_path)
    created = wf.create_change(
        title="API",
        demand_statement="Ship endpoint",
        situation="v1 scope",
        what="GET /v1/ping",
        done_criteria=["Automated test covers GET /v1/ping"],
        action_objective="Implement ping",
    )
    assert created.contract.active
    assert created.contract.version == 1

    reopened = wf.reopen_contract(
        created.change.id,
        what="GET /v2/ping returns 200",
        done_criteria=[
            "Automated test covers GET /v2/ping",
            "Endpoint documented",
        ],
        situation_note="Product renamed to v2",
        activate=True,
    )
    assert reopened.version == 2
    assert reopened.active is True
    assert "v2" in reopened.what

    archive = (
        tmp_path
        / ".retornatus"
        / "changes"
        / created.change.id
        / "contracts"
        / "v1.json"
    )
    assert archive.is_file()
    prior = FileRepository(tmp_path)._load_json(archive, type(created.contract))[0]
    assert prior.version == 1
    assert prior.what == "GET /v1/ping"

    change, _ = FileRepository(tmp_path).load_change(created.change.id)
    assert change.active_contract_version == 2


def test_skill_need_skips_trivial_and_flags_specialization(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    wf = ChangeWorkflow(tmp_path)
    trivial = wf.create_change(
        title="Typo",
        demand_statement="Fix typo in README",
        situation="One line fix",
        what="Correct spelling in README.md",
        done_criteria=["README spelling corrected"],
        action_objective="Fix typo",
    )
    assert trivial.action is not None
    skip = assess_skill_need(tmp_path, trivial.action.id)
    assert skip.required is False

    special = wf.create_change(
        title="Payments",
        demand_statement="Accept Stripe webhooks",
        situation="Need signature verification",
        what="Verify Stripe webhook signatures securely",
        done_criteria=["Webhook signature verified in automated tests"],
        action_objective="Implement Stripe webhook verification with current SDK",
    )
    assert special.action is not None
    need = assess_skill_need(tmp_path, special.action.id)
    assert need.required is True
    assert need.suggested_need


def test_security_review_dogfood(tmp_path: Path) -> None:
    seed_brownfield_service(tmp_path, init_git=True)
    initialize_project(tmp_path)
    created = ChangeWorkflow(tmp_path).create_change(
        title="Protect admin",
        demand_statement="Unauthorized clients must not access /admin",
        demand_kind=DemandKind.SECURITY,
        situation="Admin route needs negative security proof",
        what="Unauthorized request cannot access /admin",
        constraints=["No auth bypass", "Fail closed"],
        done_criteria=[
            "Unauthorized request cannot access /admin (security test)",
            "Independent security review of access control",
        ],
        action_objective="Enforce admin authorization",
        task_specs=[TaskSpec("Add authz check", resources=["app/main.py"])],
    )
    cid = created.change.id
    assert created.contract.active
    assert created.action is not None

    claims = build_claims_from_contract(created.contract)
    assert any("security_test" in c.required_evidence_types for c in claims)
    assert any("review_result" in c.required_evidence_types for c in claims)

    plan = plan_independent_assurance(tmp_path, cid, action_id=created.action.id)
    assert plan.required is True

    TaskService(tmp_path).start(created.action.tasks[0].id)
    HostExecutionService(tmp_path).record(
        action_id=created.action.id,
        summary="Host added authz guard on /admin",
        artifact_paths=["app/main.py"],
    )
    TaskService(tmp_path).complete(created.action.tasks[0].id)

    EvidenceService(tmp_path).add(
        change_id=cid,
        evidence_type="security_test",
        subject="/admin",
        source="pytest",
        producer="dogfood",
        subject_state="denied",
        supports_claim_id=claims[0].id,
        capture_git=True,
    )
    record_independent_review_evidence(
        tmp_path,
        change_id=cid,
        claim_id=claims[1].id,
        subject=claims[1].subject or "/admin",
        summary="Independent review: fail-closed authz looks correct",
        verdict="approved",
    )

    result = evaluate_change_assurance(tmp_path, cid)
    assert result.verdict is AssuranceVerdict.SATISFIED
