"""Suppression scan and scope gate against the real diff."""

from __future__ import annotations

import subprocess
from pathlib import Path

from typer.testing import CliRunner

from retornatus.application.change.workflow import ChangeWorkflow, TaskSpec
from retornatus.bootstrap.init import initialize_project
from retornatus.cli.main import app
from retornatus.infrastructure.persistence.repository import FileRepository

runner = CliRunner()


def _git(root: Path) -> None:
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "scope@retornatus.local"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Scope Test"],
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


def _commit(root: Path, message: str) -> None:
    subprocess.run(["git", "add", "-A"], cwd=root, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", message],
        cwd=root,
        check=True,
        capture_output=True,
    )


def test_suppressions_flag_added_markers_and_honor_allowlists(tmp_path: Path) -> None:
    _git(tmp_path)
    initialize_project(tmp_path)
    source = tmp_path / "src" / "app.py"
    source.parent.mkdir()
    source.write_text("def ok() -> None:\n    return None\n", encoding="utf-8")
    _commit(tmp_path, "app")
    noqa = "no" + "qa"
    type_ignore = "type: " + "ignore"
    no_cover = "pragma: " + "no cover"
    source.write_text(
        f"def ok() -> None:  # {noqa}\n"
        f"    return None  # {type_ignore}\n"
        f"    # {no_cover}\n",
        encoding="utf-8",
    )
    scanned = runner.invoke(
        app, ["gate", "suppressions", "--path", str(tmp_path)]
    )
    assert scanned.exit_code == 1, scanned.stdout
    assert "noqa" in scanned.stdout
    assert "type-ignore" in scanned.stdout
    assert "pragma-no-cover" in scanned.stdout

    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True, capture_output=True)
    staged = runner.invoke(
        app, ["gate", "suppressions", "--staged", "--path", str(tmp_path)]
    )
    assert staged.exit_code == 1, staged.stdout

    repo = FileRepository(tmp_path)
    data, rev = repo.load_config()
    data["governance"] = {
        "suppressions": {
            "allow_paths": ["src/**"],
            "extra_patterns": ["\\bHACK\\b"],
        }
    }
    repo.save_config(data, expected=rev)
    allowed = runner.invoke(
        app, ["gate", "suppressions", "--path", str(tmp_path)]
    )
    assert allowed.exit_code == 0, allowed.stdout

    other = tmp_path / "notes.py"
    other.write_text("HACK = True\n", encoding="utf-8")
    subprocess.run(["git", "add", "notes.py"], cwd=tmp_path, check=True, capture_output=True)
    extra = runner.invoke(
        app, ["gate", "suppressions", "--staged", "--path", str(tmp_path)]
    )
    assert extra.exit_code == 1, extra.stdout
    assert "HACK" in extra.stdout


def test_suppressions_base_ref_sees_only_that_range(tmp_path: Path) -> None:
    _git(tmp_path)
    initialize_project(tmp_path)
    _commit(tmp_path, "retornatus")
    subprocess.run(
        ["git", "checkout", "-b", "feature"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    skip_marker = "@pytest.mark." + "skip"
    (tmp_path / "skip_test.py").write_text(
        f"import pytest\n\n{skip_marker}\ndef test_hidden() -> None:\n    pass\n",
        encoding="utf-8",
    )
    _commit(tmp_path, "skip")
    result = runner.invoke(
        app,
        ["gate", "suppressions", "--base", "HEAD~1", "--path", str(tmp_path)],
    )
    assert result.exit_code == 1, result.stdout + result.stderr
    assert "pytest-skip" in result.stdout


def test_scope_resources_denied_and_sensitive(tmp_path: Path) -> None:
    _git(tmp_path)
    initialize_project(tmp_path)
    created = ChangeWorkflow(tmp_path).create_change(
        title="Scope",
        demand_statement="Limit the diff to declared files",
        situation="Tasks name the files they may touch",
        what="Edit src/app.py only",
        done_criteria=["pytest covers src/app.py behavior"],
        action_objective="Implement the declared file",
        task_specs=[TaskSpec("Implement app", resources=["src/app.py"])],
    )
    assert created.action is not None
    _commit(tmp_path, "change")
    base = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    app_py = tmp_path / "src" / "app.py"
    app_py.parent.mkdir()
    app_py.write_text("VALUE = 1\n", encoding="utf-8")
    _commit(tmp_path, "in scope")
    ok = runner.invoke(
        app,
        ["gate", "scope", created.change.id, "--base", base, "--path", str(tmp_path)],
    )
    assert ok.exit_code == 0, ok.stdout

    (tmp_path / "extra.txt").write_text("nope\n", encoding="utf-8")
    _commit(tmp_path, "extra")
    outside = runner.invoke(
        app,
        ["gate", "scope", created.change.id, "--base", base, "--path", str(tmp_path)],
    )
    assert outside.exit_code == 1
    assert "out of scope: extra.txt" in outside.stdout

    (tmp_path / ".env").write_text("TOKEN=1\n", encoding="utf-8")
    _commit(tmp_path, "secret")
    denied = runner.invoke(
        app,
        ["gate", "scope", created.change.id, "--base", base, "--path", str(tmp_path)],
    )
    assert denied.exit_code == 1
    assert "denied path: .env" in denied.stdout

    # Harness files stay in scope even when not listed on a Task.
    (tmp_path / ".retornatus" / "project" / "project.md").write_text(
        "# notes\n", encoding="utf-8"
    )
    worktree = runner.invoke(
        app,
        ["gate", "scope", created.change.id, "--path", str(tmp_path)],
    )
    assert worktree.exit_code == 0, worktree.stdout
    assert ".retornatus/" not in worktree.stdout


def test_sensitive_path_requires_review_or_security_claim(tmp_path: Path) -> None:
    _git(tmp_path)
    initialize_project(tmp_path)
    created = ChangeWorkflow(tmp_path).create_change(
        title="Auth",
        demand_statement="Touch authentication carefully",
        situation="Auth changes need a review claim",
        what="Update auth login",
        done_criteria=["pytest covers auth login behavior"],
        action_objective="Edit auth",
        task_specs=[TaskSpec("Login", resources=["auth/login.py"])],
    )
    _commit(tmp_path, "change")
    base = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    login = tmp_path / "auth" / "login.py"
    login.parent.mkdir()
    login.write_text("def login() -> bool:\n    return True\n", encoding="utf-8")
    _commit(tmp_path, "auth")
    blocked = runner.invoke(
        app,
        ["gate", "scope", created.change.id, "--base", base, "--path", str(tmp_path)],
    )
    assert blocked.exit_code == 1, blocked.stdout
    assert "sensitive paths" in blocked.stdout

    reviewed = ChangeWorkflow(tmp_path).create_change(
        title="Auth review",
        demand_statement="Review the authentication change",
        situation="A human review is the sensitive-path claim",
        what="Review auth login",
        done_criteria=["Independent review of authorization for auth/login.py"],
        action_objective="Record the review",
        task_specs=[TaskSpec("Review", resources=["auth/login.py"])],
    )
    # Second change shares the same diff. Its claim must be satisfied.
    from retornatus.application.assurance.evidence import EvidenceService

    claim_id = f"{reviewed.change.id}/claim-done-1"
    EvidenceService(tmp_path).add(
        change_id=reviewed.change.id,
        evidence_type="review_result",
        subject="auth/login.py",
        source="reviewer",
        producer="human",
        supports_claim_id=claim_id,
    )
    opened = runner.invoke(
        app,
        [
            "gate",
            "scope",
            reviewed.change.id,
            "--base",
            base,
            "--path",
            str(tmp_path),
        ],
    )
    assert opened.exit_code == 0, opened.stdout
