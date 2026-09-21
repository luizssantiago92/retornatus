"""Specialization Skill lifecycle tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from retornatus.application.adaptation.skills import SkillService
from retornatus.application.change.workflow import ChangeWorkflow
from retornatus.application.execution.context import assemble_execution_context
from retornatus.application.governance.bypass import BypassError
from retornatus.bootstrap.init import initialize_project
from retornatus.domain.enums import DemandKind, SkillStatus
from retornatus.infrastructure.persistence.repository import FileRepository


def _fill_research(root: Path, skill_id: str) -> None:
    repo = FileRepository(root)
    skill, body, rev = repo.load_skill(skill_id)
    filled = body.replace(
        "| | | | |",
        "| Stripe docs | https://docs.stripe.com/webhooks | 2026-09-21 | official |",
        1,
    ).replace(
        "## PROCEDURE (stable snapshot for Execution)\n\n"
        "Step-by-step instructions the agent (and subagents) must follow:\n\n"
        "1.\n2.\n3.\n",
        "## PROCEDURE (stable snapshot for Execution)\n\n"
        "Step-by-step instructions the agent (and subagents) must follow:\n\n"
        "1. Verify signature\n2. Reject invalid\n3. Test\n",
        1,
    )
    repo.save_skill(skill, filled, expected=rev)


def test_create_evolve_resolve_and_export_skill(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    created = ChangeWorkflow(tmp_path).create_change(
        title="Payments",
        demand_statement="Accept card payments",
        demand_kind=DemandKind.CAPABILITY,
        situation="Need Stripe webhooks",
        what="Verify Stripe webhook signatures",
        done_criteria=["Webhook verified in tests"],
        action_objective="Implement webhook verification",
    )
    assert created.action is not None

    svc = SkillService(tmp_path)
    skill, body = svc.create_for_specialization(
        specialization="Stripe webhook signature verification (current API)",
        title="Stripe webhooks",
        change_id=created.change.id,
        action_id=created.action.id,
        research_seed="Read Stripe docs: webhook signatures",
    )
    assert skill.id.startswith("S-")
    assert skill.status is SkillStatus.DRAFT
    assert "RESEARCH" in body
    assert (tmp_path / ".retornatus" / "adaptation" / "skills" / skill.id / "SKILL.md").is_file()

    with pytest.raises(ValueError, match="research gate"):
        svc.activate(skill.id)

    with pytest.raises(BypassError):
        svc.activate(skill.id, force=True)

    _fill_research(tmp_path, skill.id)
    active = svc.activate(skill.id)
    assert active.status is SkillStatus.ACTIVE

    evolved = svc.evolve(skill.id, note="Added timestamp tolerance check")
    assert evolved.version == 2

    ctx = assemble_execution_context(tmp_path, created.action.id)
    assert any(s.id == skill.id for s in ctx.skills)

    exported = svc.export_native(skill.id, target="cursor")
    assert exported.exists()
    assert "name:" in exported.read_text(encoding="utf-8")
