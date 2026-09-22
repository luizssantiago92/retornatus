"""DX parity features: overview, classify, lessons, ops, doctor scores."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from retornatus.application.change.classify import classify_change
from retornatus.bootstrap.init import initialize_project
from retornatus.cli.main import app
from retornatus.domain.enums import ComplexityLane, DemandKind

runner = CliRunner()


def _seed_change(tmp_path: Path) -> str:
    initialize_project(tmp_path)
    result = runner.invoke(
        app,
        [
            "change",
            "create",
            "--path",
            str(tmp_path),
            "-t",
            "Health endpoint",
            "-d",
            "Expose liveness",
            "-w",
            "GET /health returns 200",
            "--done",
            "Automated test covers /health",
            "-o",
            "Implement health",
        ],
    )
    assert result.exit_code == 0, result.stdout
    assert "Created C-0001" in result.stdout
    return "C-0001"


def test_classify_lanes() -> None:
    quick = classify_change(demand="Fix typo in README", what="typo only")
    assert quick.lane is ComplexityLane.QUICK

    complex_ = classify_change(
        demand="Add OAuth login",
        what="OAuth SSO for payment portal",
        demand_kind=DemandKind.SECURITY,
    )
    assert complex_.lane is ComplexityLane.COMPLEX

    standard = classify_change(
        demand="Add health endpoint",
        what="GET /health returns 200",
        done_criteria=["Automated test covers /health"],
    )
    assert standard.lane is ComplexityLane.STANDARD


def test_change_overview_cli(tmp_path: Path) -> None:
    cid = _seed_change(tmp_path)
    result = runner.invoke(app, ["change", "overview", cid, "--path", str(tmp_path)])
    assert result.exit_code == 0, result.stdout
    assert "Claims" in result.stdout
    assert "GET /health" in result.stdout or "claim-done" in result.stdout
    assert "Next" in result.stdout


def test_change_classify_cli() -> None:
    result = runner.invoke(
        app,
        ["change", "classify", "-d", "Fix typo in docs", "-w", "docs only wording"],
    )
    assert result.exit_code == 0
    assert "QUICK" in result.stdout


def test_doctor_process_brakes(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    result = runner.invoke(app, ["doctor", "--path", str(tmp_path)])
    assert "process:" in result.stdout
    assert "brakes:" in result.stdout
    assert "mode:" in result.stdout


def test_lesson_from_gate(tmp_path: Path) -> None:
    cid = _seed_change(tmp_path)
    result = runner.invoke(
        app,
        [
            "lesson",
            "from-gate",
            "--path",
            str(tmp_path),
            "--gate",
            "evidence",
            "--change",
            cid,
            "--title",
            "Missing evidence before verify",
            "--note",
            "Need Claim-bound Evidence before claiming done",
            "--propose-rule",
        ],
    )
    assert result.exit_code == 0, result.stdout
    assert "Recorded L-" in result.stdout
    assert "Rule Candidate R-" in result.stdout


def test_ops_list_show_run(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    listed = runner.invoke(app, ["ops", "list"])
    assert listed.exit_code == 0
    assert "doctor-hygiene" in listed.stdout
    assert "gate-scan" in listed.stdout

    shown = runner.invoke(app, ["ops", "show", "list-drafts"])
    assert shown.exit_code == 0
    assert "List drafts" in shown.stdout

    ran = runner.invoke(app, ["ops", "run", "list-drafts", "--path", str(tmp_path)])
    assert ran.exit_code == 0, ran.stdout
    assert "Draft" in ran.stdout or "none" in ran.stdout.lower()


def test_create_stores_lane(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    result = runner.invoke(
        app,
        [
            "change",
            "create",
            "--path",
            str(tmp_path),
            "-t",
            "Typo",
            "-d",
            "Fix typo in README",
            "-w",
            "docs typo only",
            "--done",
            "README wording fixed",
            "--lane",
            "QUICK",
        ],
    )
    assert result.exit_code == 0, result.stdout
    assert "Lane: QUICK" in result.stdout
