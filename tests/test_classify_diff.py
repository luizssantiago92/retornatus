"""Diff signals combined with text heuristics for change classify."""

from __future__ import annotations

import subprocess
from pathlib import Path

from typer.testing import CliRunner

from retornatus.application.change.classify import (
    DiffSignals,
    classify_change,
    collect_diff_signals,
)
from retornatus.cli.main import app
from retornatus.domain.enums import ComplexityLane

runner = CliRunner()


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)


def _init_repo(root: Path) -> None:
    _git(root, "init")
    _git(root, "config", "user.email", "classify@retornatus.local")
    _git(root, "config", "user.name", "Classify Test")
    (root / "README.md").write_text("hello\n", encoding="utf-8")
    _git(root, "add", "README.md")
    _git(root, "commit", "-m", "init")


def test_sensitive_diff_overrides_quick_wording() -> None:
    result = classify_change(
        demand="Fix typo in README",
        what="typo only",
        diff=DiffSignals(
            file_count=1,
            lines_changed=2,
            sensitive_paths=["auth/login.py"],
        ),
    )
    assert result.lane is ComplexityLane.COMPLEX
    assert "sensitive" in result.rationale.lower()
    assert "auth/login.py" in result.rationale


def test_large_diff_is_complex_even_without_keywords() -> None:
    result = classify_change(
        demand="Rename a helper",
        diff=DiffSignals(file_count=20, lines_changed=10, sensitive_paths=[]),
    )
    assert result.lane is ComplexityLane.COMPLEX
    assert "20 files" in result.rationale


def test_small_diff_keeps_quick_lane() -> None:
    result = classify_change(
        demand="Fix typo in README",
        what="typo only",
        diff=DiffSignals(file_count=1, lines_changed=3, sensitive_paths=[]),
    )
    assert result.lane is ComplexityLane.QUICK


def test_medium_diff_lifts_quick_text_to_standard() -> None:
    result = classify_change(
        demand="Fix typo in README",
        what="typo only",
        diff=DiffSignals(file_count=8, lines_changed=120, sensitive_paths=[]),
    )
    assert result.lane is ComplexityLane.STANDARD
    assert "wider than a quick fix" in result.rationale


def test_text_only_classification_is_unchanged() -> None:
    assert classify_change(demand="Fix typo in README", what="typo only").lane is ComplexityLane.QUICK
    assert (
        classify_change(demand="Add OAuth login", what="OAuth for payments").lane
        is ComplexityLane.COMPLEX
    )


def test_from_diff_cli_uses_scope_globs(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    (tmp_path / ".retornatus").mkdir()
    (tmp_path / ".retornatus" / "config.toml").write_text(
        "[governance.scope]\nsensitive_globs = [\"**/billing/**\"]\n",
        encoding="utf-8",
    )
    billing = tmp_path / "billing"
    billing.mkdir()
    (billing / "invoice.py").write_text("amount = 1\n", encoding="utf-8")
    _git(tmp_path, "add", "billing/invoice.py", ".retornatus/config.toml")
    _git(tmp_path, "commit", "-m", "billing")

    signals = collect_diff_signals(tmp_path, "HEAD~1")
    assert signals.file_count >= 1
    assert signals.lines_changed >= 1
    assert any(path.endswith("billing/invoice.py") for path in signals.sensitive_paths)

    result = runner.invoke(
        app,
        [
            "change",
            "classify",
            "--path",
            str(tmp_path),
            "--demand",
            "Fix typo in README",
            "--what",
            "typo only",
            "--from-diff",
            "HEAD~1",
        ],
    )
    assert result.exit_code == 0, result.stdout + result.stderr
    assert "COMPLEX" in result.stdout
    assert "billing/invoice.py" in result.stdout
