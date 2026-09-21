"""Specialization Skill lifecycle tests."""

from __future__ import annotations

from pathlib import Path

from retornatus.application.adaptation.skills import SkillService
from retornatus.application.change.workflow import ChangeWorkflow
from retornatus.application.execution.context import assemble_execution_context
from retornatus.bootstrap.init import initialize_project
from retornatus.domain.enums import DemandKind, SkillStatus


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

    active = svc.activate(skill.id)
    assert active.status is SkillStatus.ACTIVE

    evolved = svc.evolve(skill.id, note="Added timestamp tolerance check")
    assert evolved.version == 2

    ctx = assemble_execution_context(tmp_path, created.action.id)
    assert any(s.id == skill.id for s in ctx.skills)

    exported = svc.export_native(skill.id, target="cursor")
    assert exported.exists()
    assert "name:" in exported.read_text(encoding="utf-8")
