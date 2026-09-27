"""Agent bridge blocks refresh, including the GitHub Copilot adapter."""

from __future__ import annotations

from pathlib import Path

import pytest

from retornatus.bootstrap.init import initialize_project
from retornatus.infrastructure.environment.adapters import (
    BRIDGE_BEGIN,
    BRIDGE_END,
    ClaudeCodeAdapter,
    CodexAdapter,
    GitHubCopilotAdapter,
    detect_environment,
)
from retornatus.infrastructure.environment.rule_projection import RULES_BEGIN


def test_claude_replaces_legacy_block_and_does_not_append(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    path = tmp_path / "CLAUDE.md"
    path.write_text(
        "# Project\n\n"
        "<!-- retornatus-bridge -->\n"
        "## Retornatus\n"
        "OLD BODY that must not stick around\n"
        "<!-- retornatus-bridge -->\n",
        encoding="utf-8",
    )
    ClaudeCodeAdapter().ensure_bridge_files(tmp_path)
    text = path.read_text(encoding="utf-8")
    assert "OLD BODY" not in text
    assert text.count(BRIDGE_BEGIN) == 1
    assert text.count(BRIDGE_END) == 1
    assert "Respect Contracts" in text
    assert RULES_BEGIN in text

    stale = text.replace("Respect Contracts", "STALE SENTENCE")
    path.write_text(stale, encoding="utf-8")
    ClaudeCodeAdapter().ensure_bridge_files(tmp_path)
    refreshed = path.read_text(encoding="utf-8")
    assert "STALE SENTENCE" not in refreshed
    assert refreshed.count(BRIDGE_BEGIN) == 1
    assert refreshed.count("## Retornatus") == 1
    assert "Respect Contracts" in refreshed


def test_codex_bridge_refreshes_in_place(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    CodexAdapter().ensure_bridge_files(tmp_path)
    path = tmp_path / "AGENTS.md"
    text = path.read_text(encoding="utf-8")
    path.write_text(text.replace("canonical governance state", "STALE"), encoding="utf-8")
    CodexAdapter().ensure_bridge_files(tmp_path)
    refreshed = path.read_text(encoding="utf-8")
    assert "STALE" not in refreshed
    assert refreshed.count(BRIDGE_BEGIN) == 1
    assert "canonical governance state" in refreshed


def test_copilot_adapter_writes_instructions(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CURSOR_TRACE_ID", raising=False)
    initialize_project(tmp_path)
    (tmp_path / ".github").mkdir()
    adapter, caps = detect_environment(tmp_path)
    assert adapter.kind.value == "github_copilot"
    assert caps.bridge_files == (".github/copilot-instructions.md",)

    written = GitHubCopilotAdapter().ensure_bridge_files(tmp_path)
    path = tmp_path / ".github" / "copilot-instructions.md"
    assert path in written
    text = path.read_text(encoding="utf-8")
    assert BRIDGE_BEGIN in text and BRIDGE_END in text
    assert "Govern the work" in text
    assert RULES_BEGIN in text

    path.write_text(text.replace("Govern the work", "STALE COPILOT"), encoding="utf-8")
    GitHubCopilotAdapter().ensure_bridge_files(tmp_path)
    refreshed = path.read_text(encoding="utf-8")
    assert "STALE COPILOT" not in refreshed
    assert refreshed.count(BRIDGE_BEGIN) == 1
