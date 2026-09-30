"""Run published CLI examples in a temporary git repository.

Command sequences are parsed from fenced bash blocks in
``docs/guide/tutorials/01-first-change.md`` and ``docs/guide/Quick-start.md``
so the docs and this test stay aligned. The documentation claim must use
``docs/health.md documents GET /health`` (subject ``/health.md``). The older
wording ``Endpoint documented`` does not match evidence subject
``docs/health.md``, and ``verify`` then exits 1.
"""

from __future__ import annotations

import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TUTORIAL = ROOT / "docs" / "guide" / "tutorials" / "01-first-change.md"
QUICK_START = ROOT / "docs" / "guide" / "Quick-start.md"
HOW_IT_WORKS = ROOT / "docs" / "guide" / "How-it-works.md"
DONE = "docs/health.md documents GET /health"

_BASH_FENCE = re.compile(r"```bash\n(.*?)```", re.DOTALL)


def _bash_blocks(markdown: str) -> list[list[list[str]]]:
    blocks: list[list[list[str]]] = []
    for match in _BASH_FENCE.finditer(markdown):
        logical: list[str] = []
        buffer = ""
        for raw in match.group(1).splitlines():
            stripped = raw.strip()
            if stripped.endswith("\\"):
                buffer += stripped[:-1].rstrip() + " "
                continue
            buffer += stripped
            if buffer:
                logical.append(buffer)
            buffer = ""
        if buffer:
            logical.append(buffer)
        commands: list[list[str]] = []
        for line in logical:
            if not line or line.startswith("#"):
                continue
            # comments=True drops trailing notes such as "# 1.4.1".
            commands.append(shlex.split(line, comments=True, posix=True))
        blocks.append(commands)
    return blocks


def _retornatus_commands(markdown: str) -> list[list[str]]:
    """Retornatus argv lists, skipping optional skill and brownfield blocks."""
    selected: list[list[str]] = []
    for block in _bash_blocks(markdown):
        tokens = [part for command in block for part in command]
        if "skill" in tokens or "project-init" in tokens:
            continue
        for command in block:
            if command and command[0] == "retornatus":
                selected.append(command)
    return selected


def _git(root: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _prepare_repo(root: Path) -> None:
    _git(root, "init", "-b", "main")
    _git(root, "config", "user.email", "doc-examples@example.com")
    _git(root, "config", "user.name", "Doc Examples")
    _git(root, "config", "commit.gpgsign", "false")
    (root / "README.md").write_text("# health example\n", encoding="utf-8")
    tests = root / "tests"
    tests.mkdir()
    (tests / "test_health.py").write_text(
        "def test_health_ok() -> None:\n    assert True\n",
        encoding="utf-8",
    )
    # A local config stops pytest from walking into a parent checkout.
    (root / "pytest.ini").write_text("[pytest]\ntestpaths = tests\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-m", "Initial example repository")
    _install_python_shim(root)


def _install_python_shim(root: Path) -> None:
    """Make the docs' ``python`` invoke the interpreter that is running pytest.

    On Windows CI, ``python`` on PATH is not the uv venv, so ``python -m pytest``
    from the published example exits 1. The shim directory is prepended to PATH
    for the example commands only.
    """
    bindir = root / ".doc-example-bin"
    bindir.mkdir(exist_ok=True)
    executable = sys.executable
    if os.name == "nt":
        (bindir / "python.cmd").write_text(
            f'@echo off\r\n"{executable}" %*\r\n',
            encoding="utf-8",
        )
        return
    script = bindir / "python"
    script.write_text(
        "#!/bin/sh\n" + f"exec {shlex.quote(executable)} \"$@\"\n",
        encoding="utf-8",
    )
    script.chmod(0o755)


def _run(root: Path, argv: list[str]) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.pop("PYTEST_ADDOPTS", None)
    bindir = root / ".doc-example-bin"
    env["PATH"] = str(bindir) + os.pathsep + env.get("PATH", "")
    return subprocess.run(
        [sys.executable, "-m", "retornatus", *argv[1:]],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
        check=False,
    )


def _run_sequence(root: Path, commands: list[list[str]]) -> str:
    verify_stdout = ""
    for command in commands:
        result = _run(root, command)
        rendered = " ".join(command)
        if result.returncode != 0:
            captured = []
            evidence = root / ".retornatus" / "changes"
            if evidence.is_dir():
                for path in sorted(evidence.glob("*/evidence/*.output.txt")):
                    text = path.read_text(encoding="utf-8", errors="replace")
                    captured.append(f"{path.name}:\n{text}")
            detail = "\n".join(captured)
            raise AssertionError(
                f"{rendered} exited {result.returncode}\n"
                f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}\n"
                f"evidence output:\n{detail}"
            )
        if len(command) >= 2 and command[1] == "verify":
            verify_stdout = result.stdout
    assert verify_stdout, "sequence did not run verify"
    assert '"verdict": "SATISFIED"' in verify_stdout
    return verify_stdout


def test_doc_examples_name_the_matching_done_criterion() -> None:
    tutorial = TUTORIAL.read_text(encoding="utf-8")
    how = HOW_IT_WORKS.read_text(encoding="utf-8")
    assert DONE in tutorial
    assert DONE in how
    assert "Endpoint documented" not in tutorial


def test_tutorial_01_verify_is_satisfied(tmp_path: Path) -> None:
    commands = _retornatus_commands(TUTORIAL.read_text(encoding="utf-8"))
    assert any(DONE in part for command in commands for part in command)
    _prepare_repo(tmp_path)
    stdout = _run_sequence(tmp_path, commands)
    assert '"C-0001/claim-done-2": "SATISFIED"' in stdout


def test_quick_start_verify_is_satisfied(tmp_path: Path) -> None:
    commands = _retornatus_commands(QUICK_START.read_text(encoding="utf-8"))
    assert any(part == "verify" for command in commands for part in command)
    _prepare_repo(tmp_path)
    _run_sequence(tmp_path, commands)
