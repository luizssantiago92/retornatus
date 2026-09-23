"""Prompt intake: stages → human questions → authorized Skill create."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from retornatus.application.adaptation.intake import (
    IntakeVerdict,
    analyze_prompt_intake,
    create_skill_from_intake,
)
from retornatus.application.adaptation.skills import SkillService
from retornatus.bootstrap.init import initialize_project
from retornatus.cli.main import app
from retornatus.infrastructure.environment.hub_skill import install_hub_skill

runner = CliRunner()


def test_intake_routine_for_typo(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    analysis = analyze_prompt_intake(tmp_path, "Fix typo in README wording")
    assert analysis.verdict is IntakeVerdict.ROUTINE
    assert analysis.create_authorized is False
    assert not analysis.focused_questions


def test_intake_proposes_skill_and_requires_human(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    analysis = analyze_prompt_intake(
        tmp_path, "Add Stripe webhook signature verification"
    )
    assert analysis.verdict is IntakeVerdict.PROPOSE_SKILL
    assert analysis.skill_need_required is True
    assert analysis.create_authorized is False
    topics = {q.topic for q in analysis.focused_questions}
    assert "SPECIALIZATION" in topics
    assert "CREATE" in topics

    with pytest.raises(ValueError, match="not authorized"):
        create_skill_from_intake(tmp_path, analysis)


def test_intake_answers_authorize_create(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    analysis = analyze_prompt_intake(
        tmp_path,
        "Integrate OAuth2 PKCE for our SPA",
        answers={
            "SPECIALIZATION": "yes — create a Skill",
            "NEED": "Current OAuth2 PKCE patterns for SPA + API",
            "CREATE": "yes — create DRAFT now",
        },
    )
    assert analysis.verdict is IntakeVerdict.CREATE_SKILL
    assert analysis.create_authorized is True
    assert analysis.suggested_need and "OAuth2" in analysis.suggested_need

    skill = create_skill_from_intake(tmp_path, analysis)
    assert skill.id.startswith("S-")
    assert skill.action_id is None


def test_intake_reuses_existing_active_skill(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    SkillService(tmp_path).create_for_specialization(
        specialization="Current best practices for stripe webhooks",
        title="Stripe webhooks",
    )
    # Force ACTIVE without research for overlap test
    from retornatus.domain.enums import SkillStatus
    from retornatus.infrastructure.persistence.repository import FileRepository

    repo = FileRepository(tmp_path)
    skill, body, rev = repo.load_skill("S-0001")
    repo.save_skill(
        skill.model_copy(update={"status": SkillStatus.ACTIVE}), body, expected=rev
    )

    analysis = analyze_prompt_intake(
        tmp_path, "Need stripe webhook verification again"
    )
    assert analysis.verdict is IntakeVerdict.REUSE_SKILL
    assert any("S-0001" in s for s in analysis.existing_skill_ids)


def test_intake_cli_propose_then_create(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    first = runner.invoke(
        app,
        [
            "intake",
            "analyze",
            "--prompt",
            "Add Kubernetes rolling deploy hooks",
            "--path",
            str(tmp_path),
        ],
    )
    assert first.exit_code == 2, first.stdout
    assert "PROPOSE_SKILL" in first.stdout
    assert "Focused questions" in first.stdout

    blocked = runner.invoke(
        app,
        [
            "intake",
            "analyze",
            "--prompt",
            "Add Kubernetes rolling deploy hooks",
            "--create-skill",
            "--path",
            str(tmp_path),
        ],
    )
    assert blocked.exit_code == 1
    assert "not authorized" in blocked.stdout.lower()

    created = runner.invoke(
        app,
        [
            "intake",
            "analyze",
            "--prompt",
            "Add Kubernetes rolling deploy hooks",
            "--answer",
            "SPECIALIZATION=yes — create a Skill",
            "--answer",
            "NEED=Kubernetes rolling deploy for our cluster",
            "--answer",
            "CREATE=yes — create DRAFT now",
            "--create-skill",
            "--path",
            str(tmp_path),
        ],
    )
    assert created.exit_code == 0, created.stdout
    assert "Created S-0001" in created.stdout


def test_hub_mentions_intake_analyze(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    text = install_hub_skill(tmp_path).read_text(encoding="utf-8")
    assert "intake analyze" in text
    assert "CREATE=yes" in text or "create_authorized" in text
    assert "Manual world" in text or "manual" in text.lower()
