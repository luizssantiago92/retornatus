"""change overview --format pr labels evidence trust and gates."""

from __future__ import annotations

import sys
from pathlib import Path

from typer.testing import CliRunner

from retornatus.application.assurance.evidence import EvidenceService
from retornatus.application.change.overview import render_pull_request
from retornatus.bootstrap.init import initialize_project
from retornatus.cli.main import app

runner = CliRunner()


def test_overview_pr_labels_executed_and_self_reported(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    created = runner.invoke(
        app,
        [
            "change",
            "create",
            "--path",
            str(tmp_path),
            "--title",
            "Health",
            "--demand",
            "Add health",
            "--what",
            "GET /health returns 200",
            "--done",
            "pytest covers GET /health returns 200",
        ],
    )
    assert created.exit_code == 0, created.stdout

    config = tmp_path / ".retornatus" / "config.toml"
    existing = config.read_text(encoding="utf-8")
    config.write_text(
        existing + "\n[assurance]\n" + 'required_checks = [{name = "unit", run = ["pytest", "-q"]}]\n',
        encoding="utf-8",
    )

    EvidenceService(tmp_path).add(
        change_id="C-0001",
        evidence_type="test_result",
        subject="/health",
        source="trust me",
        producer="agent",
        supports_claim_id="C-0001/claim-done-1",
    )
    EvidenceService(tmp_path).run(
        change_id="C-0001",
        evidence_type="test_result",
        subject="/health",
        command=[sys.executable, "-c", "print('ok')"],
        supports_claim_id="C-0001/claim-done-1",
    )

    result = runner.invoke(
        app,
        ["change", "overview", "C-0001", "--path", str(tmp_path), "--format", "pr"],
    )
    assert result.exit_code == 0, result.stdout + result.stderr
    body = result.stdout
    assert "### Claims" in body
    assert "### Evidence" in body
    assert "### Required checks" in body
    assert "### Gates" in body
    assert "self-reported" in body
    assert "executed" in body
    assert "exit `0`" in body
    assert "unverified" in body
    assert "**unit** `pytest -q` — not matched" in body
    assert "**contract** — pass" in body
    assert "commit `" in body


def test_pull_request_overview_can_omit_its_gate_list(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    created = runner.invoke(
        app,
        [
            "change",
            "create",
            "--path",
            str(tmp_path),
            "--title",
            "Health",
            "--demand",
            "Add health",
            "--what",
            "GET /health returns 200",
            "--done",
            "pytest covers GET /health returns 200",
        ],
    )
    assert created.exit_code == 0, created.stdout
    body = render_pull_request(tmp_path, "C-0001", include_gates=False)
    assert "### Claims" in body
    assert "### Gates" not in body
    assert "No changed paths" not in body


def test_overview_format_rejects_unknown_value(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    result = runner.invoke(
        app,
        ["change", "overview", "C-0001", "--path", str(tmp_path), "--format", "yaml"],
    )
    assert result.exit_code == 2
    assert "text, pr, or json" in (result.stderr + result.stdout)
