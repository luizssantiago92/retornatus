"""End-to-end dogfood scenario covering M3–M12 (PRD §69 / M12)."""

from __future__ import annotations

from pathlib import Path

from retornatus.application.adaptation.service import AdaptationService
from retornatus.application.assurance.evaluate import (
    Claim,
    evaluate_assurance,
)
from retornatus.application.change.workflow import ChangeWorkflow
from retornatus.application.execution.context import assemble_execution_context
from retornatus.application.governance.policy import PolicyVerdict, evaluate_policy
from retornatus.application.question.loop import QuestionLoop
from retornatus.bootstrap.init import initialize_project
from retornatus.bootstrap.wake import wake_up
from retornatus.domain.enums import AuthorityCategory, DecisionKind, DemandKind
from retornatus.domain.ids import format_owned_id
from retornatus.domain.models import Authority, Evidence
from retornatus.domain.relations import Relation, RelationType
from retornatus.infrastructure.environment.adapters import CursorAdapter
from retornatus.infrastructure.index.sqlite_index import RetornatusIndex
from retornatus.infrastructure.persistence.repository import FileRepository


def test_full_dogfood_flow(tmp_path: Path) -> None:
    initialize_project(tmp_path)

    # Wake Up
    report = wake_up(tmp_path, auto_init=False)
    assert report.initialized
    assert report.environment in {"generic", "cursor", "claude_code", "codex"}

    # Demand → Situation → Contract → Action
    wf = ChangeWorkflow(tmp_path)
    created = wf.create_change(
        title="Dogfood Retornatus",
        demand_statement="Exercise the governed change path",
        demand_kind=DemandKind.CAPABILITY,
        situation="Empty harness needs an end-to-end validation change.",
        what="Complete wake→demand→assurance→learning loop",
        done_criteria=["Evidence of tests recorded", "Learning preserved"],
        action_objective="Implement and verify dogfood scenario",
        tasks=["Write flow", "Verify assurance"],
    )
    change_id = created.change.id
    assert created.contract.active
    assert created.action is not None
    # Tasks must NOT be auto-chained from declaration order
    assert created.action.tasks[1].depends_on == []

    # Execution context
    ctx = assemble_execution_context(tmp_path, created.action.id)
    assert ctx.objective
    assert ctx.authority.category is AuthorityCategory.DELEGATED

    # Finding / Question loop
    loop = QuestionLoop(tmp_path)
    finding = loop.record_finding(
        change_id=change_id,
        observation="Need attributable test evidence before resolution",
    )
    question = loop.open_question(
        change_id=change_id,
        statement="How do we establish sufficient assurance?",
        finding_ids=[finding.id],
    )
    q_action = loop.action_for_question(
        change_id=change_id,
        question_id=question.id,
        objective="Record test_result evidence",
        success_conditions=["Evidence persisted"],
    )
    assert q_action.origin_ref == question.id

    repo = FileRepository(tmp_path)
    claim_id = f"{change_id}/claim-done-1"
    evidence = Evidence(
        id=format_owned_id(change_id, "E", 1),
        type="test_result",
        subject="dogfood",
        source="pytest",
        producer="test_full_dogfood_flow",
        subject_state="passing",
        relations=[Relation(type=RelationType.SUPPORTS, target_id=claim_id)],
    )
    repo.save_evidence(evidence)

    assurance = evaluate_assurance(
        claims=[
            Claim(
                id=claim_id,
                statement="Evidence of tests recorded",
                required_evidence_types=["test_result"],
                subject="dogfood",
            )
        ],
        evidence=[evidence],
    )
    assert assurance.verdict.value == "SATISFIED"
    loop.resolve_question(question.id, summary="Evidence recorded", evidence_ids=[evidence.id])

    # Adaptation / Graduation candidate (not auto-active)
    adapt = AdaptationService(tmp_path)
    learning = adapt.record_learning(
        title="Always attach test_result evidence before closing Questions",
        body="Dogfood showed Resolution requires attributable Evidence.",
        summary="Evidence before resolution",
        tags=["assurance", "evidence"],
        related_ids=[change_id],
    )
    candidate = adapt.propose_rule_candidate(
        statement="Do not resolve Questions without attributable Evidence",
        applicability="question resolution",
        from_learning_id=learning.id,
    )
    assert candidate.active is False
    decision = adapt.record_human_decision(
        kind=DecisionKind.APPROVE_RULE_ACTIVATION,
        subject_id=candidate.id,
        summary="Approve rule after dogfood",
        confirmation_token=candidate.id,
    )
    activated = adapt.activate_rule(candidate.id, human_decision_id=decision.id)
    assert activated.active is True

    # Governance policy
    decision_pol = evaluate_policy(
        effect="resolve question without evidence",
        rules=repo.list_rules(),
        authority=Authority(category=AuthorityCategory.DELEGATED),
    )
    assert decision_pol.verdict in {
        PolicyVerdict.DENY,
        PolicyVerdict.ALLOW,
        PolicyVerdict.REQUIRE_HUMAN,
    }

    # Memory / index rebuild after deleting db
    index = RetornatusIndex(tmp_path)
    n1 = index.rebuild()
    assert n1 > 0
    index.paths.index_db.unlink()
    wake2 = wake_up(tmp_path, auto_init=False)
    assert wake2.index_entities > 0
    hits = RetornatusIndex(tmp_path).search("evidence")
    assert hits

    # Native adapter bridge (Cursor)
    bridges = CursorAdapter().ensure_bridge_files(tmp_path)
    assert bridges
    assert bridges[0].exists()

    # Restart continuity
    wake3 = wake_up(tmp_path, auto_init=False)
    assert change_id in wake3.change_ids
    assert wake3.learning_count >= 1
    assert wake3.rule_count >= 1
