"""Early Skill need from freeform prompts (Action optional)."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from retornatus.application.adaptation.skill_need import assess_skill_need
from retornatus.application.adaptation.skills import SkillService
from retornatus.bootstrap.init import initialize_project
from retornatus.cli.main import app
from retornatus.infrastructure.environment.hub_skill import install_hub_skill

runner = CliRunner()


def test_skill_need_from_prompt_flags_specialization(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    need = assess_skill_need(
        tmp_path,
        prompt="Add Stripe webhook signature verification to our API",
    )
    assert need.required is True
    assert need.source == "prompt"
    assert need.suggested_need
    assert "stripe" in (need.suggested_need or "").lower() or "Stripe" in need.rationale


def test_skill_need_from_prompt_skips_trivial(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    skip = assess_skill_need(tmp_path, prompt="Fix typo in README wording")
    assert skip.required is False
    assert skip.source == "prompt"


def test_skill_create_without_action(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    skill, _ = SkillService(tmp_path).create_for_specialization(
        specialization="Current OAuth2 PKCE patterns for our stack",
        title="OAuth PKCE",
    )
    assert skill.action_id is None
    assert skill.status.value == "DRAFT"
    assert (tmp_path / ".retornatus" / "adaptation" / "skills" / skill.id / "SKILL.md").is_file()


def test_skill_need_cli_prompt_and_rejects_both_modes(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    ok = runner.invoke(
        app,
        [
            "skill",
            "need",
            "--prompt",
            "Integrate Kubernetes rolling deploy",
            "--path",
            str(tmp_path),
        ],
    )
    assert ok.exit_code == 2, ok.stdout
    assert "required=True" in ok.stdout
    assert "source=prompt" in ok.stdout

    bad = runner.invoke(
        app,
        [
            "skill",
            "need",
            "--action",
            "C-0001/A-001",
            "--prompt",
            "also this",
            "--path",
            str(tmp_path),
        ],
    )
    assert bad.exit_code == 2
    assert "either" in bad.stdout.lower() or "Provide" in bad.stdout


def test_hub_skill_documents_early_skill_and_elicit(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    hub = install_hub_skill(tmp_path)
    text = hub.read_text(encoding="utf-8")
    assert "Chat intake" in text
    assert "intake analyze" in text
    assert "skill need --prompt" in text or "skill create" in text
    assert "CREATE=yes" in text or "create_authorized" in text or "human" in text.lower()
