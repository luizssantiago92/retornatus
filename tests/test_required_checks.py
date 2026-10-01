"""Owner-declared required checks and uncommitted subject freshness."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from typer.testing import CliRunner

from retornatus.application.assurance.evaluate import AssuranceVerdict
from retornatus.application.assurance.independent import evaluate_change_assurance
from retornatus.cli.main import app
from retornatus.infrastructure.persistence.repository import FileRepository

runner = CliRunner()


def _git(root: Path) -> None:
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "checks@retornatus.local"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Checks Test"],
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


def _init_change(root: Path, done: str) -> None:
    init = runner.invoke(app, ["init", str(root)])
    assert init.exit_code == 0, init.stdout
    created = runner.invoke(
        app,
        [
            "change",
            "create",
            "--path",
            str(root),
            "--title",
            "checks",
            "--demand",
            "Prove the command",
            "--what",
            "Owner names the check",
            "--done",
            done,
        ],
    )
    assert created.exit_code == 0, created.stdout


def _set_checks(root: Path, checks: list[dict[str, object]]) -> None:
    repo = FileRepository(root)
    data, rev = repo.load_config()
    assurance = dict(data.get("assurance") or {})
    assurance["required_checks"] = checks
    data["assurance"] = assurance
    repo.save_config(data, expected=rev)


def _passing_argv() -> list[str]:
    return [sys.executable, "-c", "import sys; sys.exit(0)"]


def test_evidence_run_true_does_not_satisfy_required_check(tmp_path: Path) -> None:
    _git(tmp_path)
    _init_change(tmp_path, "GET /health returns 200 with pytest test")
    _commit(tmp_path, "init")
    _set_checks(
        tmp_path,
        [{"name": "tests", "run": ["pytest", "-q"], "types": ["test_result"]}],
    )
    rogue = ["true"] if shutil.which("true") else _passing_argv()
    ran = runner.invoke(
        app,
        [
            "evidence",
            "run",
            "--path",
            str(tmp_path),
            "-c",
            "C-0001",
            "-t",
            "test_result",
            "-s",
            "/health",
            "--claim",
            "C-0001/claim-done-1",
            "--",
            *rogue,
        ],
    )
    assert ran.exit_code == 0, ran.stdout
    verified = runner.invoke(app, ["verify", "C-0001", "--path", str(tmp_path)])
    assert verified.exit_code != 0
    assert "UNVERIFIED" in verified.stdout
    assert "required check" in verified.stdout
    assert '"verdict": "SATISFIED"' not in verified.stdout


def test_matching_required_check_satisfies_only_when_clean_and_current(
    tmp_path: Path,
) -> None:
    _git(tmp_path)
    _init_change(tmp_path, "GET /health returns 200 with pytest test")
    argv = _passing_argv()
    _set_checks(tmp_path, [{"name": "tests", "run": argv}])
    _commit(tmp_path, "checks configured")

    ran = runner.invoke(
        app,
        [
            "evidence",
            "run",
            "--path",
            str(tmp_path),
            "-c",
            "C-0001",
            "-t",
            "test_result",
            "-s",
            "/health",
            "--claim",
            "C-0001/claim-done-1",
            "--",
            *argv,
        ],
    )
    assert ran.exit_code == 0, ran.stdout
    verified = runner.invoke(app, ["verify", "C-0001", "--path", str(tmp_path)])
    assert verified.exit_code == 0, verified.stdout
    assert '"verdict": "SATISFIED"' in verified.stdout

    (tmp_path / "README").write_text("edited after the check\n", encoding="utf-8")
    dirty = runner.invoke(app, ["verify", "C-0001", "--path", str(tmp_path)])
    assert dirty.exit_code != 0
    assert "uncommitted changes" in dirty.stdout
    assert "stale" in dirty.stdout.casefold()

    _commit(tmp_path, "later edit")
    moved = runner.invoke(app, ["verify", "C-0001", "--path", str(tmp_path)])
    assert moved.exit_code != 0
    assert "recorded commit" in moved.stdout


def test_evidence_commit_does_not_stale_required_check(tmp_path: Path) -> None:
    _git(tmp_path)
    _init_change(tmp_path, "GET /health returns 200 with pytest test")
    argv = _passing_argv()
    _set_checks(tmp_path, [{"name": "tests", "run": argv, "types": ["test_result"]}])
    _commit(tmp_path, "checks configured")
    ran = runner.invoke(
        app,
        [
            "evidence",
            "run",
            "--path",
            str(tmp_path),
            "-c",
            "C-0001",
            "-t",
            "test_result",
            "-s",
            "/health",
            "--claim",
            "C-0001/claim-done-1",
            "--",
            *argv,
        ],
    )
    assert ran.exit_code == 0, ran.stdout
    _commit(tmp_path, "record evidence")
    verified = runner.invoke(app, ["verify", "C-0001", "--path", str(tmp_path)])
    assert verified.exit_code == 0, verified.stdout
    assert '"verdict": "SATISFIED"' in verified.stdout

    (tmp_path / "README").write_text("source edit after the check\n", encoding="utf-8")
    _commit(tmp_path, "source edit")
    moved = runner.invoke(app, ["verify", "C-0001", "--path", str(tmp_path)])
    assert moved.exit_code != 0
    assert "recorded commit" in moved.stdout


def test_repo_required_checks_match_project_commands() -> None:
    from retornatus.application.assurance.settings import load_required_checks

    root = Path(__file__).resolve().parents[1]
    checks = load_required_checks(root)
    assert [(check.name, list(check.run), set(check.types)) for check in checks] == [
        ("pytest", ["uv", "run", "pytest", "-q"], {"test_result"}),
        (
            "ruff",
            ["uv", "run", "ruff", "check", "src", "tests", "scripts"],
            {"lint_result"},
        ),
        ("mypy", ["uv", "run", "mypy"], {"lint_result"}),
        (
            "docs",
            ["uv", "run", "python", "scripts/build_docs_html.py", "--check"],
            {"build_result"},
        ),
        ("uv-lock", ["uv", "lock", "--check"], {"build_result"}),
    ]


def test_verify_run_checks_records_the_configured_command(tmp_path: Path) -> None:
    _git(tmp_path)
    _init_change(tmp_path, "GET /health returns 200 with pytest test")
    argv = _passing_argv()
    _set_checks(tmp_path, [{"name": "tests", "run": argv, "types": ["test_result"]}])
    _commit(tmp_path, "ready")
    verified = runner.invoke(
        app,
        ["verify", "C-0001", "--path", str(tmp_path), "--run-checks"],
    )
    assert verified.exit_code == 0, verified.stdout
    assert "Recorded C-0001/E-" in verified.stdout
    assert '"verdict": "SATISFIED"' in verified.stdout

    direct = runner.invoke(
        app,
        ["checks", "run", "--path", str(tmp_path), "-c", "C-0001"],
    )
    assert direct.exit_code == 0, direct.stdout


def test_uncommitted_subject_path_stales_execution_evidence(tmp_path: Path) -> None:
    _git(tmp_path)
    (tmp_path / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
    _init_change(tmp_path, 'pytest covers "app.py"')
    _commit(tmp_path, "app")
    ran = runner.invoke(
        app,
        [
            "evidence",
            "run",
            "--path",
            str(tmp_path),
            "-c",
            "C-0001",
            "-t",
            "test_result",
            "-s",
            "app.py",
            "--claim",
            "C-0001/claim-done-1",
            "--",
            * _passing_argv(),
        ],
    )
    assert ran.exit_code == 0, ran.stdout
    fresh = evaluate_change_assurance(tmp_path, "C-0001")
    assert fresh.verdict is AssuranceVerdict.SATISFIED

    (tmp_path / "README").write_text("unrelated\n", encoding="utf-8")
    unrelated = evaluate_change_assurance(tmp_path, "C-0001")
    assert unrelated.verdict is AssuranceVerdict.SATISFIED
    (tmp_path / "README").unlink()

    (tmp_path / "app.py").write_text("VALUE = 2\n", encoding="utf-8")
    stale = runner.invoke(app, ["verify", "C-0001", "--path", str(tmp_path)])
    assert stale.exit_code != 0
    assert "uncommitted changes" in stale.stdout
    assert "stale" in stale.stdout.casefold()


def test_uncommitted_narrative_warns_unless_configured_to_fail(tmp_path: Path) -> None:
    _git(tmp_path)
    (tmp_path / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
    _init_change(tmp_path, 'documented "app.py" in the repository')
    _commit(tmp_path, "docs")
    added = runner.invoke(
        app,
        [
            "evidence",
            "add",
            "--path",
            str(tmp_path),
            "-c",
            "C-0001",
            "-t",
            "repository_observation",
            "-s",
            "app.py",
            "--source",
            "filesystem",
            "--claim",
            "C-0001/claim-done-1",
        ],
    )
    assert added.exit_code == 0, added.stdout
    (tmp_path / "app.py").write_text("VALUE = 2\n", encoding="utf-8")
    warned = runner.invoke(app, ["verify", "C-0001", "--path", str(tmp_path)])
    assert warned.exit_code == 0, warned.stdout
    assert "uncommitted changes" in warned.stdout
    assert "(warning)" in warned.stdout

    repo = FileRepository(tmp_path)
    data, rev = repo.load_config()
    assurance = dict(data.get("assurance") or {})
    assurance["uncommitted_changes"] = "fail"
    data["assurance"] = assurance
    repo.save_config(data, expected=rev)
    failed = runner.invoke(app, ["verify", "C-0001", "--path", str(tmp_path)])
    assert failed.exit_code != 0
    assert "(stale)" in failed.stdout


def test_allow_self_reported_does_not_bypass_required_checks(tmp_path: Path) -> None:
    _git(tmp_path)
    _init_change(tmp_path, "GET /health returns 200 with pytest test")
    _set_checks(tmp_path, [{"name": "tests", "run": ["pytest", "-q"]}])
    repo = FileRepository(tmp_path)
    data, rev = repo.load_config()
    assurance = dict(data.get("assurance") or {})
    assurance["allow_self_reported"] = True
    assurance["required_checks"] = [{"name": "tests", "run": ["pytest", "-q"]}]
    data["assurance"] = assurance
    repo.save_config(data, expected=rev)
    added = runner.invoke(
        app,
        [
            "evidence",
            "add",
            "--path",
            str(tmp_path),
            "-c",
            "C-0001",
            "-t",
            "test_result",
            "-s",
            "/health",
            "--source",
            "trust me",
            "--claim",
            "C-0001/claim-done-1",
        ],
    )
    assert added.exit_code == 0, added.stdout
    verified = runner.invoke(
        app,
        ["verify", "C-0001", "--path", str(tmp_path), "--allow-self-reported"],
    )
    assert verified.exit_code != 0
    assert "self-reported" in verified.stdout
    assert "required check" in verified.stdout
