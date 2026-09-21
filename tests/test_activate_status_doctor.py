"""Activate Contract, rich status, doctor hygiene, Question reopen, auto-number."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from retornatus.application.change.status import project_change_status
from retornatus.application.change.workflow import ChangeWorkflow, TaskSpec
from retornatus.application.question.loop import QuestionLoop
from retornatus.bootstrap.doctor import run_doctor
from retornatus.bootstrap.init import initialize_project
from retornatus.cli.main import app
from retornatus.domain.enums import QuestionLifecycle
from retornatus.infrastructure.persistence.repository import FileRepository

runner = CliRunner()


def test_activate_draft_contract_via_workflow_and_cli(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    wf = ChangeWorkflow(tmp_path)
    created = wf.create_change(
        title="Draft first",
        demand_statement="Ship endpoint",
        situation="Still gathering constraints",
        what="GET /health returns 200",
        done_criteria=["Automated test covers GET /health"],
        activate_contract=False,
        action_objective="Implement health",
        task_specs=[TaskSpec("Write handler"), TaskSpec("Add test")],
    )
    assert created.contract.active is False

    # Insufficient elicit path: empty done would fail — we have done criteria
    activated = wf.activate_contract(created.change.id)
    assert activated.active is True
    assert activated.version == 1
    change, _ = FileRepository(tmp_path).load_change(created.change.id)
    assert change.active_contract_version == 1

    # Second activate is idempotent
    again = wf.activate_contract(created.change.id)
    assert again.active is True

    # CLI path with a fresh draft
    draft = wf.create_change(
        title="CLI draft",
        demand_statement="Second endpoint",
        situation="Ready enough",
        what="GET /ready returns 200",
        done_criteria=["Automated test covers GET /ready"],
        activate_contract=False,
    )
    result = runner.invoke(
        app, ["change", "activate", draft.change.id, "--path", str(tmp_path)]
    )
    assert result.exit_code == 0, result.stdout
    assert "active=True" in result.stdout


def test_activate_refuses_when_situation_insufficient(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    wf = ChangeWorkflow(tmp_path)
    created = wf.create_change(
        title="Vague",
        demand_statement="Do something",
        situation="Unknown",
        what="Something",
        done_criteria=["It works somehow"],
        activate_contract=False,
    )
    # Force a contract with empty done to trip activation guard
    contract, rev = FileRepository(tmp_path).load_contract(created.change.id)
    stripped = contract.model_copy(update={"done_criteria": []})
    FileRepository(tmp_path).save_contract(stripped, expected=rev)

    with pytest.raises(ValueError, match="insufficient|done criterion"):
        wf.activate_contract(created.change.id)


def test_rich_status_projection(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    created = ChangeWorkflow(tmp_path).create_change(
        title="Status demo",
        demand_statement="Build feature",
        situation="Clear scope",
        what="Feature ships with tests",
        done_criteria=["Feature tested"],
        action_objective="Implement feature",
        task_specs=[TaskSpec("Implement"), TaskSpec("Test", depends_on_indices=[0])],
    )
    proj = project_change_status(tmp_path, created.change.id)
    text = proj.render()
    assert created.change.id in text
    assert "tasks:" in text
    assert "ready=" in text
    assert proj.contract_active is True
    assert proj.tasks_ready >= 1
    assert proj.tasks_blocked >= 1

    cli = runner.invoke(app, ["status", "--path", str(tmp_path)])
    assert cli.exit_code == 0, cli.stdout
    assert created.change.id in cli.stdout
    assert "tasks:" in cli.stdout


def test_doctor_warns_on_draft_contract(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    ChangeWorkflow(tmp_path).create_change(
        title="Draft",
        demand_statement="Later",
        situation="Incomplete",
        what="TBD endpoint",
        done_criteria=["Tests pass"],
        activate_contract=False,
    )
    report = run_doctor(tmp_path)
    assert report.wake.initialized
    assert any("draft" in w.lower() for w in report.warnings)

    cli = runner.invoke(app, ["doctor", "--path", str(tmp_path)])
    assert cli.exit_code == 0, cli.stdout
    assert "draft" in cli.stdout.lower() or "warnings:" in cli.stdout


def test_finding_question_auto_number_and_reopen(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    created = ChangeWorkflow(tmp_path).create_change(
        title="Q loop",
        demand_statement="Investigate bug",
        situation="Failure observed",
        what="Bug fixed with proof",
        done_criteria=["Regression test passes"],
    )
    loop = QuestionLoop(tmp_path)
    f1 = loop.record_finding(change_id=created.change.id, observation="First fail")
    f2 = loop.record_finding(change_id=created.change.id, observation="Second fail")
    assert f1.id.endswith("/F-001")
    assert f2.id.endswith("/F-002")

    q1 = loop.open_question(
        change_id=created.change.id,
        statement="How do we establish the fix works?",
        finding_ids=[f1.id],
    )
    q2 = loop.open_question(
        change_id=created.change.id,
        statement="Is the root cause documented?",
        finding_ids=[f2.id],
    )
    assert q1.id.endswith("/Q-001")
    assert q2.id.endswith("/Q-002")

    # Non-verifiable resolve without evidence
    resolved = loop.resolve_question(q2.id, summary="Yes, in Situation notes")
    assert resolved.lifecycle is QuestionLifecycle.RESOLVED
    assert resolved.resolution is not None

    reopened = loop.reopen_question(q2.id)
    assert reopened.lifecycle is QuestionLifecycle.OPEN
    assert reopened.resolution is None

    # CLI reopen
    loop.resolve_question(q2.id, summary="Documented again")
    cli = runner.invoke(
        app, ["question", "reopen", q2.id, "--path", str(tmp_path)]
    )
    assert cli.exit_code == 0, cli.stdout
    assert "Reopened" in cli.stdout
    q, _ = FileRepository(tmp_path).load_question(q2.id)
    assert q.lifecycle is QuestionLifecycle.OPEN

    # CLI auto-number (omit --number)
    add = runner.invoke(
        app,
        [
            "finding",
            "add",
            "--change",
            created.change.id,
            "--observation",
            "Third observation",
            "--path",
            str(tmp_path),
        ],
    )
    assert add.exit_code == 0, add.stdout
    assert "F-003" in add.stdout
