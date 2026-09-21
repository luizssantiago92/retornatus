"""End-to-end gap closure: brownfield → commit staleness → independent review → tasks CLI."""

from __future__ import annotations

from pathlib import Path

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
from retornatus.application.assurance.subject_state import (
    current_git_head,
    format_commit_state,
)
from retornatus.application.change.loop import project_next_work
from retornatus.application.change.readiness import synchronize_action
from retornatus.application.change.situation import assess_situation, collect_repo_signals
from retornatus.application.change.workflow import ChangeWorkflow, TaskSpec
from retornatus.application.execution.brownfield_fixture import (
    git_commit_all,
    seed_brownfield_service,
)
from retornatus.application.execution.host_boundary import (
    simulate_health_endpoint_implementation,
)
from retornatus.application.governance.gates import gate_assurance, gate_contract
from retornatus.bootstrap.init import initialize_project
from retornatus.bootstrap.project_init import project_init
from retornatus.bootstrap.wake import wake_up
from retornatus.domain.enums import DemandKind


def test_brownfield_full_gap_closure(tmp_path: Path) -> None:
    """
    1. Brownfield fixture with git
    2. Situation from repo signals (no re-ask stack)
    3. Tasks with real depends_on + resources
    4. Host implements health
    5. Evidence with commit:<sha>
    6. Stale after new commit
    7. Independent review Claim + review_result
    8. wake continuity
    """
    seed_brownfield_service(tmp_path, init_git=True)
    assert (tmp_path / "pyproject.toml").is_file()
    assert (tmp_path / ".github" / "workflows" / "ci.yml").is_file()
    head0 = current_git_head(tmp_path)
    assert head0

    initialize_project(tmp_path)
    project_init(tmp_path)

    signals = collect_repo_signals(tmp_path)
    assert any("pyproject" in s for s in signals)
    assert any("health" in s.lower() for s in signals)

    assessment = assess_situation(
        demand="Add a health endpoint for ops liveness",
        what='GET /health returns 200 and {"status":"ok"}',
        done_criteria=[
            "Automated test covers GET /health returns 200",
            "Endpoint documented in docs/health.md",
            "Independent review of health surface",
        ],
        project_context=(tmp_path / ".retornatus" / "project" / "project.md").read_text(
            encoding="utf-8"
        ),
        repo_signals=signals,
    )
    assert assessment.sufficient_for_contract
    assert any("pytest" in c.lower() for c in assessment.constraints)
    # Must not invent "what language?" questions
    assert not any(q.topic.lower() == "language" for q in assessment.focused_questions)

    wf = ChangeWorkflow(tmp_path)
    created = wf.create_change(
        title="Add health endpoint",
        demand_statement="Add a health endpoint for ops liveness",
        demand_kind=DemandKind.CAPABILITY,
        situation="Brownfield Acme Service lacks liveness probe.",
        what='GET /health returns 200 and {"status":"ok"}',
        done_criteria=[
            "Automated test covers GET /health returns 200",
            "Endpoint documented in docs/health.md",
            "Independent review of health surface",
        ],
        action_objective="Implement and verify health endpoint",
        task_specs=[
            TaskSpec("Implement /health in app/main.py", resources=["app/main.py"]),
            TaskSpec("Document endpoint", resources=["docs/health.md"]),
            TaskSpec(
                "Add pytest coverage",
                depends_on_indices=[0],
                resources=["tests/test_health.py"],
            ),
        ],
    )
    cid = created.change.id
    assert created.contract.active
    assert gate_contract(tmp_path, cid).passed
    assert created.action is not None
    assert created.action.tasks[2].depends_on == [created.action.tasks[0].id]
    assert created.action.tasks[0].resources == ["app/main.py"]

    sync = synchronize_action(created.action)
    assert created.action.tasks[0].id in sync.ready
    assert created.action.tasks[1].id in sync.ready
    assert created.action.tasks[2].id in sync.blocked

    projection = project_next_work(tmp_path, cid)
    assert len(projection.ready) == 2

    host = simulate_health_endpoint_implementation(tmp_path)
    assert host.test_passed
    sha_impl = git_commit_all(tmp_path, "Add health endpoint")
    assert sha_impl

    claims = build_claims_from_contract(created.contract)
    assert len(claims) == 3
    # claim-3 should need review_result
    assert "review_result" in claims[2].required_evidence_types

    EvidenceService(tmp_path).add(
        change_id=cid,
        evidence_type="test_result",
        subject="/health",
        source="host_boundary",
        producer="dogfood",
        supports_claim_id=claims[0].id,
        capture_git=True,
    )
    EvidenceService(tmp_path).add(
        change_id=cid,
        evidence_type="repository_observation",
        subject="docs/health.md",
        source="filesystem",
        producer="dogfood",
        supports_claim_id=claims[1].id,
        capture_git=True,
    )

    plan = plan_independent_assurance(tmp_path, cid, action_id=created.action.id)
    assert plan.required is True
    assert plan.execution_context is not None
    assert plan.execution_context.independent_assurance is True

    # Without review Evidence → not SATISFIED
    mid = evaluate_change_assurance(tmp_path, cid)
    assert mid.verdict is not AssuranceVerdict.SATISFIED

    record_independent_review_evidence(
        tmp_path,
        change_id=cid,
        claim_id=claims[2].id,
        subject="health surface",
        summary="Fresh review: endpoint is minimal and safe",
        verdict="approved",
    )

    ok = evaluate_change_assurance(tmp_path, cid)
    assert ok.verdict is AssuranceVerdict.SATISFIED
    assert gate_assurance(tmp_path, cid).passed

    # Staleness: mutate subject and commit → prior commit Evidence becomes stale
    (tmp_path / "app" / "main.py").write_text(
        '"""Acme service entrypoints."""\n\n'
        "def version() -> dict:\n"
        '    return {"service": "acme", "version": "0.1.1"}\n\n'
        "def health() -> tuple[dict, int]:\n"
        '    return {"status": "ok"}, 200\n',
        encoding="utf-8",
    )
    sha_new = git_commit_all(tmp_path, "Bump version alongside health")
    assert sha_new and sha_new != sha_impl

    stale = evaluate_change_assurance(tmp_path, cid)
    assert stale.verdict is AssuranceVerdict.NOT_SATISFIED

    # Re-capture Evidence at new HEAD for behavioral claims
    EvidenceService(tmp_path).add(
        change_id=cid,
        evidence_type="test_result",
        subject="/health",
        source="host_boundary",
        producer="dogfood-refresh",
        supports_claim_id=claims[0].id,
        capture_git=True,
    )
    EvidenceService(tmp_path).add(
        change_id=cid,
        evidence_type="repository_observation",
        subject="docs/health.md",
        source="filesystem",
        producer="dogfood-refresh",
        supports_claim_id=claims[1].id,
        capture_git=True,
    )
    record_independent_review_evidence(
        tmp_path,
        change_id=cid,
        claim_id=claims[2].id,
        subject="health surface",
        summary="Re-review after version bump",
        verdict="approved",
    )
    fresh = evaluate_change_assurance(tmp_path, cid)
    assert fresh.verdict is AssuranceVerdict.SATISFIED

    wake = wake_up(tmp_path, auto_init=False)
    assert cid in wake.change_ids
    assert any("pyproject" in (wake.project_context_summary or "") for _ in [0]) or (
        wake.project_context_summary is not None
    )


def test_commit_subject_state_format(tmp_path: Path) -> None:
    seed_brownfield_service(tmp_path, init_git=True)
    head = current_git_head(tmp_path)
    assert head
    assert format_commit_state(head).startswith("commit:")
