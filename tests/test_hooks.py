"""Git hook install: worktrees, core.hooksPath, and commit-msg $1."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from typer.testing import CliRunner

from retornatus.application.change.workflow import ChangeWorkflow, TaskSpec
from retornatus.bootstrap.hooks import BEGIN, END
from retornatus.bootstrap.init import initialize_project
from retornatus.cli.main import app

runner = CliRunner()


def _git(root: Path) -> None:
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "hooks@retornatus.local"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Hooks Test"],
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


def _hooks_dir(root: Path) -> Path:
    raw = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--git-path", "hooks"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    path = Path(raw)
    if not path.is_absolute():
        path = (root / path).resolve()
    return path


def test_install_respects_hooks_path_worktree_and_commit_msg_argument(
    tmp_path: Path,
) -> None:
    main = tmp_path / "main"
    main.mkdir()
    _git(main)
    subprocess.run(
        ["git", "config", "core.hooksPath", ".githooks"],
        cwd=main,
        check=True,
        capture_output=True,
    )
    installed = runner.invoke(app, ["hooks", "install", "--path", str(main)])
    assert installed.exit_code == 0, installed.stdout
    hooks = _hooks_dir(main)
    assert hooks == (main / ".githooks").resolve()
    pre_commit = (hooks / "pre-commit").read_text(encoding="utf-8")
    commit_msg = (hooks / "commit-msg").read_text(encoding="utf-8")
    assert BEGIN in pre_commit and END in pre_commit
    assert "gate suppressions --staged" in pre_commit
    assert "hooks scope" in pre_commit
    assert "$1" in commit_msg
    assert "COMMIT_EDITMSG" not in commit_msg
    assert "--message-file" in commit_msg

    status = runner.invoke(app, ["hooks", "status", "--path", str(main)])
    assert "pre-commit: installed" in status.stdout
    assert "commit-msg: installed" in status.stdout

    # commit-msg reads $1, not a side file named COMMIT_EDITMSG.
    decoy = main / ".git" / "COMMIT_EDITMSG"
    decoy.parent.mkdir(parents=True, exist_ok=True)
    decoy.write_text("\n", encoding="utf-8")
    message = tmp_path / "actual-message.txt"
    message.write_text("Explain the scope gate\n", encoding="utf-8")
    good = subprocess.run(
        ["sh", str(hooks / "commit-msg"), str(message)],
        cwd=main,
        capture_output=True,
        text=True,
    )
    assert good.returncode == 0, good.stdout + good.stderr
    assert "commit message ok" in good.stdout

    empty = tmp_path / "empty-message.txt"
    empty.write_text("# only a comment\n\n", encoding="utf-8")
    bad = subprocess.run(
        ["sh", str(hooks / "commit-msg"), str(empty)],
        cwd=main,
        capture_output=True,
        text=True,
    )
    assert bad.returncode != 0
    assert "empty" in (bad.stdout + bad.stderr).lower()

    work = tmp_path / "wt"
    subprocess.run(
        ["git", "worktree", "add", "-b", "wt-branch", str(work)],
        cwd=main,
        check=True,
        capture_output=True,
    )
    # The linked worktree does not inherit core.hooksPath unless set there.
    # Point this worktree at its own hooks dir via the default git-path.
    subprocess.run(
        ["git", "config", "--unset", "core.hooksPath"],
        cwd=work,
        check=True,
        capture_output=True,
    )
    wt_install = runner.invoke(app, ["hooks", "install", "--path", str(work)])
    assert wt_install.exit_code == 0, wt_install.stdout
    wt_hooks = _hooks_dir(work)
    assert wt_hooks != hooks
    assert (wt_hooks / "pre-commit").is_file()
    assert (wt_hooks / "commit-msg").is_file()
    wt_msg = (wt_hooks / "commit-msg").read_text(encoding="utf-8")
    assert "$1" in wt_msg
    assert "COMMIT_EDITMSG" not in wt_msg


def test_pre_commit_chains_user_hook_and_blocks_staged_suppressions(
    tmp_path: Path,
) -> None:
    _git(tmp_path)
    initialize_project(tmp_path)
    hooks = _hooks_dir(tmp_path)
    hooks.mkdir(parents=True, exist_ok=True)
    user = hooks / "pre-commit"
    user.write_text(
        "#!/bin/sh\necho user-hook >> hook-log\n",
        encoding="utf-8",
        newline="\n",
    )
    installed = runner.invoke(app, ["hooks", "install", "--path", str(tmp_path)])
    assert installed.exit_code == 0, installed.stdout
    text = user.read_text(encoding="utf-8")
    assert "user-hook" in text
    assert "gate suppressions --staged" in text

    clean = subprocess.run(
        ["sh", str(user)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert clean.returncode == 0, clean.stdout + clean.stderr
    assert "user-hook" in (tmp_path / "hook-log").read_text(encoding="utf-8")

    flagged = tmp_path / "flagged.py"
    flagged.write_text("x = 1  # " + "no" + "qa" + "\n", encoding="utf-8")
    subprocess.run(["git", "add", "flagged.py"], cwd=tmp_path, check=True, capture_output=True)
    (tmp_path / "hook-log").unlink()
    blocked = subprocess.run(
        ["sh", str(user)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert blocked.returncode != 0, blocked.stdout + blocked.stderr
    assert not (tmp_path / "hook-log").exists()

    removed = runner.invoke(app, ["hooks", "remove", "--path", str(tmp_path)])
    assert removed.exit_code == 0, removed.stdout
    restored = user.read_text(encoding="utf-8")
    assert BEGIN not in restored
    assert "user-hook" in restored


def test_pre_commit_scope_runs_when_a_change_is_active(tmp_path: Path) -> None:
    _git(tmp_path)
    initialize_project(tmp_path)
    created = ChangeWorkflow(tmp_path).create_change(
        title="Hook scope",
        demand_statement="Keep commits inside declared resources",
        situation="The pre-commit hook runs scope for the active change",
        what="Only README may change",
        done_criteria=["README stays the declared resource"],
        action_objective="Edit README",
        task_specs=[TaskSpec("Readme", resources=["README"])],
    )
    assert created.contract.active
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "change"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    installed = runner.invoke(app, ["hooks", "install", "--path", str(tmp_path)])
    assert installed.exit_code == 0, installed.stdout
    outside = tmp_path / "other.txt"
    outside.write_text("nope\n", encoding="utf-8")
    subprocess.run(["git", "add", "other.txt"], cwd=tmp_path, check=True, capture_output=True)
    hook = _hooks_dir(tmp_path) / "pre-commit"
    blocked = subprocess.run(
        ["sh", str(hook)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")},
    )
    assert blocked.returncode != 0, blocked.stdout + blocked.stderr
    assert "out of scope: other.txt" in blocked.stdout + blocked.stderr
