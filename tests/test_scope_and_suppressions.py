"""Suppression scan and scope gate against the real diff."""

from __future__ import annotations

import subprocess
from pathlib import Path

from typer.testing import CliRunner

from retornatus.application.change.workflow import ChangeWorkflow, TaskSpec
from retornatus.application.governance import diff_scan as diff_scan_mod
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
    marker = "no" + "qa"
    type_ignore = "type: " + "ignore"
    no_cover = "pragma: " + "no cover"
    source.write_text(
        f"def ok() -> None:  # {marker}\n    return None  # {type_ignore}\n    # {no_cover}\n",
        encoding="utf-8",
    )
    scanned = runner.invoke(app, ["gate", "suppressions", "--path", str(tmp_path)])
    assert scanned.exit_code == 1, scanned.stdout
    assert "noqa" in scanned.stdout
    assert "type-ignore" in scanned.stdout
    assert "pragma-no-cover" in scanned.stdout

    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True, capture_output=True)
    staged = runner.invoke(app, ["gate", "suppressions", "--staged", "--path", str(tmp_path)])
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
    allowed = runner.invoke(app, ["gate", "suppressions", "--path", str(tmp_path)])
    assert allowed.exit_code == 0, allowed.stdout

    other = tmp_path / "notes.py"
    other.write_text("HACK = True\n", encoding="utf-8")
    subprocess.run(["git", "add", "notes.py"], cwd=tmp_path, check=True, capture_output=True)
    extra = runner.invoke(app, ["gate", "suppressions", "--staged", "--path", str(tmp_path)])
    assert extra.exit_code == 1, extra.stdout
    assert "HACK" in extra.stdout


def test_suppressions_scan_untracked_files_and_skip_ignored(tmp_path: Path) -> None:
    """A not-yet-added file is scanned. A gitignored file is not.

    ``--base`` and ``--staged`` stay on the committed range and the index,
    so an untracked marker does not fail those modes.
    """
    _git(tmp_path)
    initialize_project(tmp_path)
    _commit(tmp_path, "init")
    marker = "no" + "qa"
    (tmp_path / "stray.py").write_text(
        f"def hidden() -> None:  # {marker}\n    return None\n",
        encoding="utf-8",
    )
    (tmp_path / "secret_skip.py").write_text(
        f"def ignored() -> None:  # {marker}\n    return None\n",
        encoding="utf-8",
    )
    (tmp_path / "blob.bin").write_bytes(b"\0not-text")
    gitignore = tmp_path / ".gitignore"
    gitignore.write_bytes(gitignore.read_bytes() + b"secret_skip.py\n")

    scanned = runner.invoke(app, ["gate", "suppressions", "--path", str(tmp_path)])
    assert scanned.exit_code == 1, scanned.stdout
    assert "stray.py:1:" in scanned.stdout
    assert "secret_skip.py" not in scanned.stdout
    assert "blob.bin" not in scanned.stdout

    staged = runner.invoke(app, ["gate", "suppressions", "--staged", "--path", str(tmp_path)])
    assert staged.exit_code == 0, staged.stdout
    assert "stray.py" not in staged.stdout

    based = runner.invoke(
        app,
        ["gate", "suppressions", "--base", "HEAD", "--path", str(tmp_path)],
    )
    assert based.exit_code == 0, based.stdout
    assert "stray.py" not in based.stdout


def test_untracked_file_lines_skip_binary_and_missing(tmp_path: Path) -> None:
    from retornatus.application.governance.diff import _untracked_file_lines

    (tmp_path / "blob.bin").write_bytes(b"\0\1\2")
    assert _untracked_file_lines(tmp_path, "blob.bin") == []
    assert _untracked_file_lines(tmp_path, "gone.py") == []
    nested = tmp_path / "nested"
    nested.mkdir()
    assert _untracked_file_lines(tmp_path, "nested") == []


def test_untracked_file_lines_skip_unreadable(tmp_path: Path, monkeypatch: object) -> None:
    from retornatus.application.governance.diff import _untracked_file_lines

    (tmp_path / "locked.py").write_text("x = 1\n", encoding="utf-8")

    def _boom(self: Path) -> bytes:
        raise OSError("unreadable")

    monkeypatch.setattr(Path, "read_bytes", _boom)
    assert _untracked_file_lines(tmp_path, "locked.py") == []


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


def test_markdown_span_helpers_ignore_unclosed_and_missing_files(tmp_path: Path) -> None:
    marker = "--no-" + "verify"
    assert diff_scan_mod._fenced_line_numbers(tmp_path, "missing.md") == set()
    assert marker in diff_scan_mod._mask_inline_code(f"see `{marker}")


def test_suppressions_skip_markdown_code_and_flag_prose(tmp_path: Path) -> None:
    """Docs may name a marker inside code. Prose and Python still fail."""
    _git(tmp_path)
    initialize_project(tmp_path)
    hook_flag = "--no-" + "verify"
    skip_marker = "pytest.mark." + "skip"
    lint_mark = "no" + "qa"
    guide = tmp_path / "docs" / "Cloud-agents.md"
    guide.parent.mkdir()
    guide.write_text(
        "Before\n"
        f"A commit can pass `{hook_flag}`.\n"
        "```bash\n"
        f"git commit {hook_flag}\n"
        "```\n"
        f"Prose must not pass {hook_flag} bare.\n"
        f"```\n{skip_marker}\n```\n",
        encoding="utf-8",
    )
    source = tmp_path / "src" / "app.py"
    source.parent.mkdir()
    source.write_text(
        f"def ok() -> None:  # {lint_mark}\n    return None\n",
        encoding="utf-8",
    )
    _commit(tmp_path, "docs and code")
    result = runner.invoke(
        app,
        ["gate", "suppressions", "--base", "HEAD~1", "--path", str(tmp_path)],
    )
    assert result.exit_code == 1, result.stdout
    assert "Cloud-agents.md" in result.stdout
    assert "prose" in result.stdout.lower() or "Prose" in result.stdout
    assert "app.py" in result.stdout
    assert lint_mark in result.stdout
    # The backtick mention and the fenced lines are not hits.
    flagged = [line for line in result.stdout.splitlines() if "Cloud-agents.md" in line]
    assert len(flagged) == 1
    assert "Prose must not pass" in flagged[0]


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
    # init ignores .env, so a normal add would skip it. Force-add still hits
    # the scope gate's denied-path rule.
    subprocess.run(
        ["git", "add", "-f", "--", ".env"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "secret"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    denied = runner.invoke(
        app,
        ["gate", "scope", created.change.id, "--base", base, "--path", str(tmp_path)],
    )
    assert denied.exit_code == 1
    assert "denied path: .env" in denied.stdout

    # Harness files stay in scope even when not listed on a Task.
    (tmp_path / ".retornatus" / "project" / "project.md").write_text("# notes\n", encoding="utf-8")
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
