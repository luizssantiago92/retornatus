"""Construction-path physical gates and CLI helpers."""

from __future__ import annotations

from pathlib import Path

from retornatus.application.assurance.evidence import EvidenceService
from retornatus.application.change.loop import next_work
from retornatus.application.change.workflow import ChangeWorkflow
from retornatus.application.governance.gates import (
    gate_assurance,
    gate_contract,
    gate_evidence,
    gate_skill_research,
)
from retornatus.application.adaptation.skills import SkillService
from retornatus.bootstrap.init import initialize_project
from retornatus.bootstrap.project_init import project_init
from retornatus.domain.enums import DemandKind
from retornatus.infrastructure.environment.hub_skill import install_hub_skill
from retornatus.infrastructure.persistence.repository import FileRepository


def test_gates_and_construction_path(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    created = ChangeWorkflow(tmp_path).create_change(
        title="Health",
        demand_statement="Add health",
        demand_kind=DemandKind.CAPABILITY,
        situation="Ops needs liveness",
        what="GET /health",
        done_criteria=["test covers /health"],
        action_objective="Implement health",
    )
    cid = created.change.id
    assert gate_contract(tmp_path, cid).passed
    assert not gate_evidence(tmp_path, cid).passed
    assert not gate_assurance(tmp_path, cid).passed

    EvidenceService(tmp_path).add(
        change_id=cid,
        evidence_type="test_result",
        subject="/health",
        source="pytest",
        producer="test",
        subject_state="passing",
        supports_action_id=created.action.id if created.action else None,
    )
    assert gate_evidence(tmp_path, cid).passed
    assert gate_assurance(tmp_path, cid).passed

    skill, _ = SkillService(tmp_path).create_for_specialization(
        specialization="FastAPI health checks",
        action_id=created.action.id if created.action else None,
        change_id=cid,
    )
    assert not gate_skill_research(tmp_path, skill.id).passed

    # Simulate researched skill
    repo = FileRepository(tmp_path)
    skill_obj, body, rev = repo.load_skill(skill.id)
    filled = body.replace(
        "| | | | |",
        "| FastAPI docs | https://fastapi.tiangolo.com/advanced/testing/ | 2026-09-21 | official |",
        1,
    ).replace(
        "## PROCEDURE (stable snapshot for Execution)\n\n"
        "Step-by-step instructions the agent (and subagents) must follow:\n\n"
        "1.\n2.\n3.\n",
        "## PROCEDURE (stable snapshot for Execution)\n\n"
        "Step-by-step instructions the agent (and subagents) must follow:\n\n"
        "1. Add route\n2. Add test\n3. Run pytest\n",
        1,
    )
    repo.save_skill(skill_obj, filled, expected=rev)
    assert gate_skill_research(tmp_path, skill.id).passed

    nxt = next_work(tmp_path, cid)
    assert nxt is not None

    project_md = project_init(tmp_path)
    assert project_md.is_file()
    hub = install_hub_skill(tmp_path)
    assert hub.is_file()
    assert "Default construction loop" in hub.read_text(encoding="utf-8")
