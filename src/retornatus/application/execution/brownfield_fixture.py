"""Brownfield sandbox seeding for construction dogfood (no LLM)."""

from __future__ import annotations

import subprocess
from pathlib import Path


def seed_brownfield_service(root: Path, *, init_git: bool = True) -> Path:
    """
    Create a realistic existing Python service *without* a health endpoint.

    Mimics brownfield entry: stack, tests, CI, docs, conventions already present.
    """
    root = root.resolve()
    root.mkdir(parents=True, exist_ok=True)

    (root / "app").mkdir(exist_ok=True)
    (root / "tests").mkdir(exist_ok=True)
    (root / "docs").mkdir(exist_ok=True)
    (root / ".github" / "workflows").mkdir(parents=True, exist_ok=True)

    (root / "README.md").write_text(
        "# Acme Service\n\nInternal HTTP service for ops tooling.\n",
        encoding="utf-8",
    )
    (root / "pyproject.toml").write_text(
        '[project]\n'
        'name = "acme-service"\n'
        'version = "0.1.0"\n'
        'requires-python = ">=3.11"\n'
        "dependencies = []\n\n"
        "[project.optional-dependencies]\n"
        'dev = ["pytest>=8.0"]\n\n'
        "[tool.pytest.ini_options]\n"
        'testpaths = ["tests"]\n'
        'pythonpath = ["."]\n',
        encoding="utf-8",
    )
    (root / "app" / "__init__.py").write_text("", encoding="utf-8")
    (root / "app" / "main.py").write_text(
        '"""Acme service entrypoints."""\n\n'
        "def version() -> dict:\n"
        '    return {"service": "acme", "version": "0.1.0"}\n',
        encoding="utf-8",
    )
    (root / "tests" / "test_version.py").write_text(
        "from app.main import version\n\n"
        "def test_version_payload() -> None:\n"
        "    payload = version()\n"
        '    assert payload["service"] == "acme"\n',
        encoding="utf-8",
    )
    (root / "docs" / "overview.md").write_text(
        "# Overview\n\nAcme Service exposes internal tooling APIs.\n",
        encoding="utf-8",
    )
    (root / ".github" / "workflows" / "ci.yml").write_text(
        "name: ci\n"
        "on: [push]\n"
        "jobs:\n"
        "  test:\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        "      - uses: actions/checkout@v4\n"
        "      - run: pip install pytest && pytest -q\n",
        encoding="utf-8",
    )
    (root / "AGENTS.md").write_text(
        "# Agent conventions\n\nPrefer pytest. Do not invent frameworks.\n",
        encoding="utf-8",
    )

    if init_git:
        _git_init_commit(root)

    return root


def _git_init_commit(root: Path) -> str | None:
    try:
        subprocess.run(
            ["git", "init"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "dogfood@retornatus.local"],
            cwd=root,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Retornatus Dogfood"],
            cwd=root,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "add", "-A"],
            cwd=root,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "Initial brownfield service"],
            cwd=root,
            check=True,
            capture_output=True,
        )
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
        return head.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def git_commit_all(root: Path, message: str) -> str | None:
    """Commit all changes; return new HEAD sha or None."""
    try:
        subprocess.run(
            ["git", "add", "-A"],
            cwd=root,
            check=True,
            capture_output=True,
        )
        # Allow empty? No — only if there are changes
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
        if not status.stdout.strip():
            head = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            )
            return head.stdout.strip()
        subprocess.run(
            ["git", "commit", "-m", message],
            cwd=root,
            check=True,
            capture_output=True,
        )
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
        return head.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None
