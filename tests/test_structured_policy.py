"""Structured policy rules match paths and commands, not objective wording."""

from __future__ import annotations

import subprocess
from pathlib import Path

from typer.testing import CliRunner

from retornatus.application.adaptation.service import AdaptationService
from retornatus.application.change.workflow import ChangeWorkflow, TaskSpec
from retornatus.application.governance.policy import (
    PolicyVerdict,
    evaluate_action_policy,
    evaluate_policy,
)
from retornatus.bootstrap.init import initialize_project
from retornatus.cli.main import app
from retornatus.domain.enums import AuthorityCategory, DecisionKind
from retornatus.domain.models import Authority, Rule

runner = CliRunner()


def _git(root: Path) -> None:
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "policy@retornatus.local"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Policy Test"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    (root / "README").write_text("base\n", encoding="utf-8")
    subprocess.run(["git", "add", "README"], cwd=root, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "base"],
        cwd=root,
        check=True,
        capture_output=True,
    )


def _activate(root: Path, rule: Rule) -> None:
    from retornatus.infrastructure.persistence.repository import FileRepository

    repo = FileRepository(root)
    repo.save_rule(rule)
    decision = AdaptationService(root).record_human_decision(
        kind=DecisionKind.APPROVE_RULE_ACTIVATION,
        subject_id=rule.id,
        summary="Approve structured rule",
        confirmation_token=rule.id,
    )
    AdaptationService(root).activate_rule(rule.id, human_decision_id=decision.id)


def test_structured_rule_denies_on_diff_not_wording(tmp_path: Path) -> None:
    _git(tmp_path)
    initialize_project(tmp_path)
    created = ChangeWorkflow(tmp_path).create_change(
        title="Keys",
        demand_statement="Do not land private keys",
        situation="A pem file is in the diff",
        what="Refuse key material",
        done_criteria=["Policy denies pem paths"],
        action_objective="tidy the comments",
        task_specs=[TaskSpec("Touch key", resources=["keys/id.pem"])],
    )
    assert created.action is not None
    rule = Rule(
        id="R-0009",
        statement="Do not write private keys",
        applicability="this wording is not in the objective",
        effect_type="write",
        path_globs=["**/*.pem", "**/*.key"],
        active=True,
        authority=Authority(category=AuthorityCategory.HUMAN),
    )
    _activate(tmp_path, rule)
    (tmp_path / "keys").mkdir()
    (tmp_path / "keys" / "id.pem").write_text("secret\n", encoding="utf-8")

    decision = evaluate_action_policy(tmp_path, created.action.id)
    assert decision.verdict is PolicyVerdict.DENY
    assert "structured" in decision.rationale
    assert decision.warnings == []

    cli = runner.invoke(
        app,
        [
            "policy",
            "check",
            "--effect",
            "tidy the comments",
            "--effect-type",
            "write",
            "--resource",
            "keys/id.pem",
            "--path",
            str(tmp_path),
        ],
    )
    assert cli.exit_code == 1, cli.stdout
    assert "DENY" in cli.stdout

    safe = evaluate_policy(
        effect="tidy the comments",
        rules=[rule],
        authority=Authority(category=AuthorityCategory.DELEGATED, rationale="cli"),
        paths=["docs/readme.md"],
        effect_type="write",
    )
    assert safe.verdict is PolicyVerdict.ALLOW


def test_command_pattern_and_deprecated_substring(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    rule = Rule(
        id="R-0003",
        statement="Do not run destructive deletes",
        applicability="unused for structured match",
        effect_type="exec",
        command_patterns=["rm *"],
        active=True,
        authority=Authority(category=AuthorityCategory.HUMAN),
    )
    denied = evaluate_policy(
        effect="cleanup",
        rules=[rule],
        authority=Authority(category=AuthorityCategory.DELEGATED, rationale="cli"),
        commands=["rm -rf /tmp/build"],
        effect_type="exec",
    )
    assert denied.verdict is PolicyVerdict.DENY

    legacy = Rule(
        id="R-0004",
        statement="Do not commit secrets",
        applicability="commit secrets",
        active=True,
        authority=Authority(category=AuthorityCategory.HUMAN),
    )
    decision = evaluate_policy(
        effect="commit secrets to repo",
        rules=[legacy],
        authority=Authority(category=AuthorityCategory.DELEGATED, rationale="cli"),
    )
    assert decision.verdict is PolicyVerdict.DENY
    assert decision.warnings
    assert "deprecated" in decision.warnings[0]

    reworded = evaluate_policy(
        effect="refresh the docs",
        rules=[legacy],
        authority=Authority(category=AuthorityCategory.DELEGATED, rationale="cli"),
    )
    assert reworded.verdict is PolicyVerdict.ALLOW
    assert reworded.warnings
