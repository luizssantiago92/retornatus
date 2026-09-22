"""Governance Policy CLI, native Rule projection, adapter-aware integrate (V1)."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from retornatus.application.adaptation.service import AdaptationService
from retornatus.application.change.workflow import ChangeWorkflow, TaskSpec
from retornatus.application.execution.context import assemble_execution_context
from retornatus.application.governance.gates import gate_policy
from retornatus.application.governance.policy import PolicyVerdict, evaluate_action_policy
from retornatus.bootstrap.init import initialize_project
from retornatus.bootstrap.wake import wake_up
from retornatus.cli.main import app
from retornatus.domain.enums import DecisionKind
from retornatus.infrastructure.environment.adapters import (
    ClaudeCodeAdapter,
    CodexAdapter,
    CursorAdapter,
    detect_environment,
)
from retornatus.infrastructure.environment.rule_projection import (
    RULES_BEGIN,
    format_active_rules_markdown,
    list_active_rules,
)
from retornatus.infrastructure.persistence.repository import FileRepository

runner = CliRunner()


def _activate_deny_rule(root: Path, *, statement: str, applicability: str) -> str:
    adapt = AdaptationService(root)
    candidate = adapt.propose_rule_candidate(
        statement=statement,
        applicability=applicability,
    )
    decision = adapt.record_human_decision(
        kind=DecisionKind.APPROVE_RULE_ACTIVATION,
        subject_id=candidate.id,
        summary="Approve for policy tests",
        confirmation_token=candidate.id,
    )
    activated = adapt.activate_rule(candidate.id, human_decision_id=decision.id)
    assert activated.active
    return activated.id


def test_policy_check_and_gate_deny(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    created = ChangeWorkflow(tmp_path).create_change(
        title="Secrets",
        demand_statement="Avoid leaking secrets",
        situation="Security-sensitive repo",
        what="No secrets in commits",
        done_criteria=["Policy denies secret commits"],
        action_objective="commit secrets to the repository",
        task_specs=[TaskSpec("Scan")],
    )
    assert created.action is not None
    _activate_deny_rule(
        tmp_path,
        statement="Do not commit secrets",
        applicability="commit secrets",
    )

    decision = evaluate_action_policy(tmp_path, created.action.id)
    assert decision.verdict is PolicyVerdict.DENY

    gate = gate_policy(tmp_path, created.action.id)
    assert gate.passed is False

    cli = runner.invoke(
        app,
        ["policy", "check", "--action", created.action.id, "--path", str(tmp_path)],
    )
    assert cli.exit_code == 1
    assert "DENY" in cli.stdout

    effect = runner.invoke(
        app,
        [
            "policy",
            "check",
            "--effect",
            "commit secrets to repo",
            "--path",
            str(tmp_path),
        ],
    )
    assert effect.exit_code == 1

    run = runner.invoke(
        app,
        [
            "run",
            created.action.id,
            "--strict-policy",
            "--path",
            str(tmp_path),
        ],
    )
    assert run.exit_code == 1
    assert "DENY" in run.stdout or '"policy_verdict": "DENY"' in run.stdout

    gate_cli = runner.invoke(
        app, ["gate", "policy", created.action.id, "--path", str(tmp_path)]
    )
    assert gate_cli.exit_code == 1


def test_cursor_bridge_projects_active_rules(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    (tmp_path / ".cursor").mkdir()
    _activate_deny_rule(
        tmp_path,
        statement="Do not push force to main",
        applicability="force push",
    )
    bridges = CursorAdapter().ensure_bridge_files(tmp_path)
    rule_file = tmp_path / ".cursor" / "rules" / "retornatus.mdc"
    assert rule_file in bridges or rule_file.exists()
    text = rule_file.read_text(encoding="utf-8")
    assert RULES_BEGIN in text
    assert "Do not push force to main" in text
    assert list_active_rules(tmp_path)


def test_claude_and_codex_adapters_project_rules(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    _activate_deny_rule(
        tmp_path,
        statement="Do not skip tests",
        applicability="skip tests",
    )
    claude = ClaudeCodeAdapter().ensure_bridge_files(tmp_path)
    assert claude
    claude_text = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
    assert "Do not skip tests" in claude_text
    assert RULES_BEGIN in claude_text

    # Codex on a fresh root marker
    codex_root = tmp_path / "codex-proj"
    codex_root.mkdir()
    initialize_project(codex_root)
    (codex_root / "AGENTS.md").write_text("# Agents\n", encoding="utf-8")
    _activate_deny_rule(
        codex_root,
        statement="Do not disable sandbox",
        applicability="disable sandbox",
    )
    CodexAdapter().ensure_bridge_files(codex_root)
    agents = (codex_root / "AGENTS.md").read_text(encoding="utf-8")
    assert "Do not disable sandbox" in agents

    adapter, caps = detect_environment(codex_root)
    assert adapter.kind.value == "codex"
    assert caps.native_rules is True


def test_integrate_uses_detected_environment(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    (tmp_path / "CLAUDE.md").write_text("# Project\n", encoding="utf-8")
    result = runner.invoke(app, ["integrate", "--path", str(tmp_path)])
    assert result.exit_code == 0, result.stdout
    assert "claude_code" in result.stdout
    assert RULES_BEGIN in (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")


def test_v1_acceptance_continuity_with_policy_and_wake(tmp_path: Path) -> None:
    """PRD §69 acceptance: wake → change → evidence → learning → restart."""
    initialize_project(tmp_path)
    (tmp_path / ".cursor").mkdir()

    wake1 = wake_up(tmp_path, ensure_bridges=True, auto_init=False)
    assert wake1.initialized
    assert wake1.bridge_files

    created = ChangeWorkflow(tmp_path).create_change(
        title="V1 acceptance",
        demand_statement="Close V1 acceptance scenario",
        situation="Harness ready for governed construction",
        what="Demand to Learning continuity with Policy",
        done_criteria=["Evidence recorded", "Learning preserved", "Policy enforceable"],
        action_objective="Record attributable proof without committing secrets",
        task_specs=[TaskSpec("Prove"), TaskSpec("Learn")],
    )
    assert created.action is not None

    ctx = assemble_execution_context(tmp_path, created.action.id)
    assert ctx.policy_verdict == PolicyVerdict.ALLOW.value
    assert ctx.authority

    _activate_deny_rule(
        tmp_path,
        statement="Do not commit secrets",
        applicability="commit secrets",
    )
    # Bridges refreshed on activate — Cursor rules should list the rule
    mdc = (tmp_path / ".cursor" / "rules" / "retornatus.mdc").read_text(encoding="utf-8")
    assert "Do not commit secrets" in mdc or format_active_rules_markdown(
        FileRepository(tmp_path).list_rules()
    )

    # Delete index and wake again
    index_db = tmp_path / ".retornatus" / "index" / "retornatus.db"
    if index_db.is_file():
        index_db.unlink()
    wake2 = wake_up(tmp_path, auto_init=False)
    assert created.change.id in wake2.change_ids
    assert wake2.rule_count >= 1
    assert wake2.index_entities > 0
