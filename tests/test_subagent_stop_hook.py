"""Subagent-stop hook: same reminder as Stop, opt-out, and host config."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from typer.testing import CliRunner

from retornatus.application.agent_hooks.config import (
    CURSOR_LOOP_LIMIT,
    hook_config_path,
    subagent_stop_command,
)
from retornatus.application.assurance.evaluate import infer_claim_subject
from retornatus.application.assurance.evidence import EvidenceService
from retornatus.bootstrap.doctor import run_doctor
from retornatus.bootstrap.init import initialize_project
from retornatus.cli.main import app

runner = CliRunner()

_DONE = "pytest exits 0 for the health command"


def _create(root: Path, *, draft: bool = False) -> None:
    initialize_project(root)
    args = [
        "change",
        "create",
        "--path",
        str(root),
        "--title",
        "Health",
        "--demand",
        "Operators need a health command with a clear exit code",
        "--what",
        "The health command exits 0",
        "--done",
        _DONE,
        "--situation",
        "Operators run one health command and read its exit code.",
    ]
    if draft:
        args.append("--draft-contract")
    created = runner.invoke(app, args)
    assert created.exit_code == 0, created.stdout + created.stderr


def _satisfy(root: Path, change_id: str = "C-0001") -> None:
    EvidenceService(root).run(
        change_id=change_id,
        evidence_type="test_result",
        subject=infer_claim_subject(_DONE),
        command=[sys.executable, "-c", "print('ok')"],
        supports_claim_id=f"{change_id}/claim-done-1",
    )


def _subagent(root: Path, host: str, payload: object, *, path: Path | None = None) -> object:
    args = ["hook", "subagent-stop", "--host", host]
    if path is not None:
        args.extend(["--path", str(path)])
    raw = payload if isinstance(payload, str) else json.dumps(payload)
    return runner.invoke(app, args, input=raw)


def _load(stdout: str) -> dict[str, object]:
    document = json.loads(stdout)
    assert isinstance(document, dict)
    return document


def _hooks_table(root: Path, body: str) -> None:
    config = root / ".retornatus" / "config.toml"
    original = config.read_text(encoding="utf-8")
    config.write_text(original + "\n[hooks]\n" + body + "\n", encoding="utf-8")


def test_open_obligations_remind_each_host(tmp_path: Path) -> None:
    _create(tmp_path)
    claude = _subagent(
        tmp_path,
        "claude",
        {
            "hook_event_name": "SubagentStop",
            "stop_hook_active": False,
            "agent_id": "def456",
            "agent_type": "Explore",
            "last_assistant_message": "Analysis complete.",
        },
        path=tmp_path,
    )
    assert claude.exit_code == 0, claude.output
    claude_body = _load(claude.stdout)
    assert set(claude_body) == {"decision", "reason"}
    assert claude_body["decision"] == "block"
    reason = str(claude_body["reason"])
    assert "C-0001/claim-done-1" in reason
    assert "INCONCLUSIVE" in reason
    assert "retornatus evidence run" in reason

    cursor = _subagent(
        tmp_path,
        "cursor",
        {
            "subagent_type": "generalPurpose",
            "status": "completed",
            "loop_count": 0,
            "modified_files": ["src/auth.ts"],
            "summary": "Explored the auth flow.",
        },
        path=tmp_path,
    )
    assert cursor.exit_code == 0, cursor.output
    cursor_body = _load(cursor.stdout)
    assert set(cursor_body) == {"followup_message"}
    assert "C-0001/claim-done-1" in str(cursor_body["followup_message"])
    assert "decision" not in cursor_body

    codex = _subagent(
        tmp_path,
        "codex",
        {
            "hook_event_name": "SubagentStop",
            "stop_hook_active": False,
            "agent_id": "agent-1",
            "agent_type": "explorer",
            "last_assistant_message": "Done looking.",
        },
        path=tmp_path,
    )
    assert codex.exit_code == 0, codex.output
    assert _load(codex.stdout)["decision"] == "block"


def test_no_change_and_satisfied_allow(tmp_path: Path) -> None:
    missing = _subagent(tmp_path, "claude", {"stop_hook_active": False}, path=tmp_path)
    assert missing.exit_code == 0
    assert missing.stdout == ""

    draft_root = tmp_path / "draft"
    draft_root.mkdir()
    _create(draft_root, draft=True)
    draft = _subagent(draft_root, "codex", {"stop_hook_active": False}, path=draft_root)
    assert draft.exit_code == 0, draft.output
    assert draft.stdout == ""

    proven = tmp_path / "proven"
    proven.mkdir()
    _create(proven)
    _satisfy(proven)
    satisfied = _subagent(
        proven,
        "cursor",
        {"status": "completed", "loop_count": 0, "summary": "All claims are proven."},
        path=proven,
    )
    assert satisfied.exit_code == 0, satisfied.output
    assert satisfied.stdout == ""


def test_question_ending_allows_an_unsatisfied_change(tmp_path: Path) -> None:
    _create(tmp_path)
    claude = _subagent(
        tmp_path,
        "claude",
        {"stop_hook_active": False, "last_assistant_message": "Should I keep going?"},
        path=tmp_path,
    )
    assert claude.exit_code == 0, claude.output
    assert claude.stdout == ""

    cursor = _subagent(
        tmp_path,
        "cursor",
        {"status": "completed", "loop_count": 0, "summary": "Want me to continue?"},
        path=tmp_path,
    )
    assert cursor.exit_code == 0, cursor.output
    assert cursor.stdout == ""

    transcript = tmp_path / "agent.jsonl"
    transcript.write_text(
        json.dumps({"type": "assistant", "message": {"role": "assistant", "content": "Posso seguir?"}}) + "\n",
        encoding="utf-8",
    )
    codex = _subagent(
        tmp_path,
        "codex",
        {"stop_hook_active": False, "agent_transcript_path": str(transcript)},
        path=tmp_path,
    )
    assert codex.exit_code == 0, codex.output
    assert codex.stdout == ""


def test_cursor_abort_and_stop_hook_active_allow(tmp_path: Path) -> None:
    _create(tmp_path)
    for status in ("aborted", "error"):
        result = _subagent(tmp_path, "cursor", {"status": status, "loop_count": 0}, path=tmp_path)
        assert result.exit_code == 0, result.output
        assert result.stdout == ""
    for host in ("claude", "codex"):
        result = _subagent(tmp_path, host, {"stop_hook_active": True, "last_assistant_message": "done"}, path=tmp_path)
        assert result.exit_code == 0, result.output
        assert result.stdout == ""


def test_subagent_stop_toggle_and_doctor(tmp_path: Path) -> None:
    _create(tmp_path)
    assert "hooks subagent_stop: true" in run_doctor(tmp_path).render()

    _hooks_table(tmp_path, "subagent_stop = false")
    disabled = _subagent(
        tmp_path,
        "claude",
        {"stop_hook_active": False, "last_assistant_message": "Still unproven."},
        path=tmp_path,
    )
    assert disabled.exit_code == 0, disabled.output
    assert disabled.stdout == ""
    assert "hooks subagent_stop: false" in run_doctor(tmp_path).render()

    config = tmp_path / ".retornatus" / "config.toml"
    text = config.read_text(encoding="utf-8").replace("subagent_stop = false", "subagent_stop = true")
    config.write_text(text, encoding="utf-8")
    enabled = _subagent(
        tmp_path,
        "cursor",
        {"status": "completed", "summary": "Still unproven."},
        path=tmp_path,
    )
    assert "followup_message" in json.loads(enabled.stdout)

    config.write_text(text.replace("subagent_stop = true", 'subagent_stop = "yes"'), encoding="utf-8")
    invalid = _subagent(tmp_path, "codex", {"stop_hook_active": False}, path=tmp_path)
    assert invalid.exit_code == 0
    assert invalid.stdout == ""
    assert "fail-open" in invalid.stderr
    assert "subagent_stop" in invalid.stderr
    assert "hooks subagent_stop: invalid" in run_doctor(tmp_path).render()


def test_generated_hook_config_sets_loop_limit(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    installed = runner.invoke(app, ["integrate", "--hooks", "--path", str(tmp_path)])
    assert installed.exit_code == 0, installed.stdout
    again = runner.invoke(app, ["integrate", "--hooks", "--path", str(tmp_path)])
    assert again.exit_code == 0, again.stdout

    cursor = json.loads(hook_config_path(tmp_path, "cursor").read_text(encoding="utf-8"))
    cursor_entries = cursor["hooks"]["subagentStop"]
    assert cursor_entries == [{"command": subagent_stop_command("cursor"), "loop_limit": CURSOR_LOOP_LIMIT}]
    assert CURSOR_LOOP_LIMIT == 1

    for host, event in (("claude", "SubagentStop"), ("codex", "SubagentStop")):
        body = json.loads(hook_config_path(tmp_path, host).read_text(encoding="utf-8"))
        groups = body["hooks"][event]
        commands = [item["command"] for group in groups for item in group["hooks"]]
        assert commands.count(subagent_stop_command(host)) == 1
        ours = [item for group in groups for item in group["hooks"] if item["command"] == subagent_stop_command(host)]
        assert ours == [
            {
                "type": "command",
                "command": subagent_stop_command(host),
                "timeout": 30,
            }
        ]

    report = run_doctor(tmp_path)
    for host in ("claude", "cursor", "codex"):
        assert "subagent-stop=installed" in report.agent_hooks[host]

    removed = runner.invoke(app, ["integrate", "--remove-hooks", "--path", str(tmp_path)])
    assert removed.exit_code == 0, removed.stdout
    assert not hook_config_path(tmp_path, "cursor").exists()
    assert run_doctor(tmp_path).agent_hooks["claude"] == "absent"
