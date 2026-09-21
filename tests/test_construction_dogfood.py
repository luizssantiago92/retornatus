"""Real construction-path dogfood with deterministic Host execution boundary."""

from __future__ import annotations

from pathlib import Path

from retornatus.application.adaptation.service import AdaptationService
from retornatus.application.assurance.evaluate import (
    AssuranceVerdict,
    build_claims_from_contract,
    evaluate_assurance,
)
from retornatus.application.assurance.evidence import EvidenceService
from retornatus.application.change.loop import next_work
from retornatus.application.change.situation import assess_situation
from retornatus.application.change.workflow import ChangeWorkflow
from retornatus.application.execution.context import (
    assemble_assurance_context,
    assemble_execution_context,
)
from retornatus.application.execution.host_boundary import (
    simulate_health_endpoint_implementation,
)
from retornatus.application.governance.gates import (
    gate_assurance,
    gate_contract,
    gate_evidence,
)
from retornatus.bootstrap.init import initialize_project
from retornatus.bootstrap.project_init import project_init
from retornatus.bootstrap.wake import wake_up
from retornatus.domain.enums import DemandKind
from retornatus.infrastructure.index.sqlite_index import RetornatusIndex


def test_health_endpoint_construction_dogfood(tmp_path: Path) -> None:
    """
    Demand → Situation → Contract → gate → Action → loop next → Host boundary →
    real artifacts → Evidence → Assurance SATISFIED → Learning → restart/wake.
    """
    initialize_project(tmp_path)
    project_init(tmp_path)

    # Situation elicitation — simple Demand should be sufficient
    assessment = assess_situation(
        demand="Add a health endpoint",
        what='GET /health returns 200 and {"status":"ok"}',
        done_criteria=[
            "Automated test covers GET /health returns 200",
            "Endpoint documented in docs/health.md",
        ],
        project_context=(tmp_path / ".retornatus" / "project" / "project.md").read_text(
            encoding="utf-8"
        ),
    )
    assert assessment.sufficient_for_contract

    wf = ChangeWorkflow(tmp_path)
    created = wf.create_change(
        title="Add health endpoint",
        demand_statement="Add a health endpoint",
        demand_kind=DemandKind.CAPABILITY,
        situation="Ops needs a liveness check for the service.",
        what='GET /health returns 200 and {"status":"ok"}',
        done_criteria=[
            "Automated test covers GET /health returns 200",
            "Endpoint documented in docs/health.md",
        ],
        action_objective="Implement and verify health endpoint",
        tasks=["Implement /health", "Document endpoint"],
    )
    cid = created.change.id
    assert created.contract.active
    assert gate_contract(tmp_path, cid).passed
    assert created.action is not None
    # No Skill required for this trivial construction — Host boundary is enough

    nxt = next_work(tmp_path, cid)
    assert nxt is not None
    assert nxt.kind == "task"

    ctx = assemble_execution_context(tmp_path, created.action.id)
    assert ctx.contract_what
    assert "/health" in (ctx.contract_what or "")

    # Environment-native implementation boundary (deterministic; no LLM)
    host = simulate_health_endpoint_implementation(tmp_path)
    assert host.test_passed
    assert all(p.exists() for p in host.artifacts)

    claims = build_claims_from_contract(created.contract)
    assert len(claims) == 2

    EvidenceService(tmp_path).add(
        change_id=cid,
        evidence_type="test_result",
        subject="/health",
        source="host_boundary",
        producer="simulate_health_endpoint_implementation",
        subject_state=host.subject_state,
        supports_action_id=created.action.id,
        supports_claim_id=claims[0].id,
    )
    EvidenceService(tmp_path).add(
        change_id=cid,
        evidence_type="repository_observation",
        subject="docs/health.md",
        source="filesystem",
        producer="simulate_health_endpoint_implementation",
        subject_state="present",
        supports_claim_id=claims[1].id,
    )

    assert gate_evidence(tmp_path, cid).passed
    assert gate_assurance(tmp_path, cid).passed

    result = evaluate_assurance(
        claims=claims,
        evidence=EvidenceService(tmp_path).list_for_change(cid),
        current_subject_states={"/health": host.subject_state},
    )
    assert result.verdict is AssuranceVerdict.SATISFIED

    # Independent Assurance context is fresh
    assurance_ctx = assemble_assurance_context(tmp_path, created.action.id)
    assert assurance_ctx.independent_assurance is True
    assert assurance_ctx.relevant_learnings == []

    AdaptationService(tmp_path).record_learning(
        title="Health endpoint needs automated test + docs Evidence",
        body="Dogfood: Claim-bound test_result and repository_observation satisfied DONE.",
        summary="Bind Evidence to Claims",
        tags=["health", "assurance"],
        related_ids=[cid],
    )

    # Restart continuity after disposable index wipe
    RetornatusIndex(tmp_path).rebuild()
    (tmp_path / ".retornatus" / "index" / "retornatus.db").unlink()
    wake = wake_up(tmp_path, auto_init=False)
    assert cid in wake.change_ids
    assert wake.learning_count >= 1
    assert wake.index_entities > 0
    assert (tmp_path / "app" / "main.py").is_file()
    assert (tmp_path / "docs" / "health.md").is_file()
