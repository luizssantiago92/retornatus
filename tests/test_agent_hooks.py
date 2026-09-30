"""Agent Stop hook: stdin decisions, fail-open, and integrate merge."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from typer.testing import CliRunner

from retornatus.application.agent_hooks.config import (
    CURSOR_LOOP_LIMIT,
    hook_config_path,
    session_start_command,
    stop_command,
)
from retornatus.application.agent_hooks.session import CONTEXT_BYTE_CAP
from retornatus.application.assurance.evaluate import infer_claim_subject
from retornatus.application.assurance.evidence import EvidenceService
from retornatus.bootstrap.doctor import run_doctor
from retornatus.bootstrap.init import initialize_project
from retornatus.cli.main import app

runner = CliRunner()

_DONE = "pytest exits 0 for the health command"


def _create(root: Path, *, draft: bool = False, title: str = "Health") -> None:
    initialize_project(root)
    args = [
        "change",
        "create",
        "--path",
        str(root),
        "--title",
        title,
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


def _stop(root: Path, host: str, payload: object, *, path: Path | None = None) -> object:
    args = ["hook", "stop", "--host", host]
    if path is not None:
        args.extend(["--path", str(path)])
    raw = payload if isinstance(payload, str) else json.dumps(payload)
    return runner.invoke(app, args, input=raw)


def _load(stdout: str) -> dict[str, object]:
    document = json.loads(stdout)
    assert isinstance(document, dict)
    return document


def test_satisfied_allows_with_extra_stdin_fields(tmp_path: Path) -> None:
    _create(tmp_path)
    _satisfy(tmp_path)
    payload = {
        "session_id": "abc",
        "stop_hook_active": False,
        "last_assistant_message": "done",
        "unused": {"nested": True},
    }
    for host in ("claude", "cursor", "codex"):
        result = _stop(tmp_path, host, payload, path=tmp_path)
        assert result.exit_code == 0, result.output
        assert result.stdout == ""
        assert result.stderr == ""


def test_not_satisfied_blocks_with_host_json(tmp_path: Path) -> None:
    _create(tmp_path)
    claude = _stop(tmp_path, "Claude", {"cwd": str(tmp_path)}, path=tmp_path)
    assert claude.exit_code == 0, claude.output
    claude_body = _load(claude.stdout)
    assert set(claude_body) == {"decision", "reason"}
    assert claude_body["decision"] == "block"
    reason = str(claude_body["reason"])
    assert "C-0001/claim-done-1" in reason
    assert "INCONCLUSIVE" in reason
    assert "retornatus evidence run" in reason
    assert "pytest -q" in reason

    cursor = _stop(tmp_path, "cursor", {"status": "completed", "loop_count": 0}, path=tmp_path)
    assert cursor.exit_code == 0, cursor.output
    cursor_body = _load(cursor.stdout)
    assert set(cursor_body) == {"followup_message"}
    assert "C-0001/claim-done-1" in str(cursor_body["followup_message"])
    assert "decision" not in cursor_body

    codex = _stop(tmp_path, "codex", {}, path=tmp_path)
    assert codex.exit_code == 0, codex.output
    codex_body = _load(codex.stdout)
    assert codex_body["decision"] == "block"
    assert "evidence run" in str(codex_body["reason"])


def test_stop_hook_active_allows_a_second_time(tmp_path: Path) -> None:
    _create(tmp_path)
    for host in ("claude", "codex"):
        result = _stop(tmp_path, host, {"stop_hook_active": True}, path=tmp_path)
        assert result.exit_code == 0, result.output
        assert result.stdout == ""
        assert result.stderr == ""


def test_cursor_aborted_or_error_allows(tmp_path: Path) -> None:
    _create(tmp_path)
    for status in ("aborted", "error"):
        result = _stop(tmp_path, "cursor", {"status": status, "loop_count": 0}, path=tmp_path)
        assert result.exit_code == 0, result.output
        assert result.stdout == ""


def test_missing_retornatus_and_draft_contract_allow(tmp_path: Path) -> None:
    empty = _stop(tmp_path, "claude", {"stop_hook_active": False}, path=tmp_path)
    assert empty.exit_code == 0
    assert empty.stdout == ""

    _create(tmp_path, draft=True)
    draft = _stop(tmp_path, "codex", {}, path=tmp_path)
    assert draft.exit_code == 0, draft.output
    assert draft.stdout == ""


def test_non_object_stdin_still_blocks_and_bad_json_fails_open(tmp_path: Path) -> None:
    _create(tmp_path)
    listed = _stop(tmp_path, "claude", "[]", path=tmp_path)
    assert listed.exit_code == 0
    assert _load(listed.stdout)["decision"] == "block"

    empty = _stop(tmp_path, "claude", "", path=tmp_path)
    assert empty.exit_code == 0
    assert _load(empty.stdout)["decision"] == "block"

    broken = _stop(tmp_path, "claude", "{", path=tmp_path)
    assert broken.exit_code == 0
    assert broken.stdout == ""
    assert "fail-open" in broken.stderr
    assert "invalid JSON" in broken.stderr


def test_unknown_host_and_crash_fail_open(tmp_path: Path, monkeypatch) -> None:
    _create(tmp_path)
    unknown = _stop(tmp_path, "copilot", {}, path=tmp_path)
    assert unknown.exit_code == 0
    assert unknown.stdout == ""
    assert "fail-open" in unknown.stderr
    assert "unknown host" in unknown.stderr

    def boom(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("disk failed")

    monkeypatch.setattr(
        "retornatus.application.agent_hooks.stop.evaluate_change_assurance",
        boom,
    )
    crashed = _stop(tmp_path, "cursor", {"status": "completed"}, path=tmp_path)
    assert crashed.exit_code == 0
    assert crashed.stdout == ""
    assert "fail-open" in crashed.stderr
    assert "disk failed" in crashed.stderr


def test_walks_up_to_project_and_one_unsatisfied_change_blocks(
    tmp_path: Path,
    monkeypatch,
) -> None:
    project = tmp_path / "proj"
    project.mkdir()
    _create(project)
    _satisfy(project)
    nested = project / "src" / "pkg"
    nested.mkdir(parents=True)
    monkeypatch.chdir(nested)
    walked = runner.invoke(app, ["hook", "stop", "--host", "claude"], input="{}")
    assert walked.exit_code == 0, walked.output
    assert walked.stdout == ""

    monkeypatch.chdir(tmp_path)
    outside = runner.invoke(app, ["hook", "stop", "--host", "claude"], input="{}")
    assert outside.exit_code == 0
    assert outside.stdout == ""

    second = runner.invoke(
        app,
        [
            "change",
            "create",
            "--path",
            str(project),
            "--title",
            "Second",
            "--demand",
            "Operators need a second health command with a clear exit code",
            "--what",
            "The second health command exits 0",
            "--done",
            _DONE,
            "--situation",
            "Operators run one health command and read its exit code.",
        ],
    )
    assert second.exit_code == 0, second.stdout + second.stderr
    blocked = _stop(project, "codex", {}, path=project)
    body = _load(blocked.stdout)
    reason = str(body["reason"])
    assert "C-0002" in reason
    assert "C-0001 is" not in reason


def test_invalid_required_checks_fail_open(tmp_path: Path) -> None:
    _create(tmp_path)
    config = tmp_path / ".retornatus" / "config.toml"
    config.write_text(
        config.read_text(encoding="utf-8") + '\n[assurance]\nrequired_checks = "nope"\n',
        encoding="utf-8",
    )
    result = _stop(tmp_path, "claude", {}, path=tmp_path)
    assert result.exit_code == 0
    assert result.stdout == ""
    assert "fail-open" in result.stderr


def test_malformed_hook_files_are_left_unchanged(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    claude = hook_config_path(tmp_path, "claude")
    claude.parent.mkdir(parents=True)
    claude.write_text(json.dumps({"hooks": []}), encoding="utf-8")
    rejected = runner.invoke(
        app, ["integrate", "--hooks", "--host", "claude", "--path", str(tmp_path)]
    )
    assert rejected.exit_code == 2
    assert json.loads(claude.read_text(encoding="utf-8")) == {"hooks": []}

    claude.write_text(json.dumps({"hooks": {"Stop": {}}}), encoding="utf-8")
    rejected_stop = runner.invoke(
        app, ["integrate", "--hooks", "--host", "claude", "--path", str(tmp_path)]
    )
    assert rejected_stop.exit_code == 2
    assert "must be a list" in rejected_stop.stderr

    cursor = hook_config_path(tmp_path, "cursor")
    cursor.parent.mkdir(parents=True, exist_ok=True)
    cursor.write_text("[]", encoding="utf-8")
    rejected_cursor = runner.invoke(
        app, ["integrate", "--hooks", "--host", "cursor", "--path", str(tmp_path)]
    )
    assert rejected_cursor.exit_code == 2
    assert cursor.read_text(encoding="utf-8") == "[]"
    assert "JSON object" in rejected_cursor.stderr


def test_required_check_argv_is_the_next_command(tmp_path: Path) -> None:
    _create(tmp_path)
    config = tmp_path / ".retornatus" / "config.toml"
    config.write_text(
        config.read_text(encoding="utf-8")
        + "\n[assurance]\n"
        + 'required_checks = [{name = "unit", run = ["uv", "run", "pytest", "-q"]}]\n',
        encoding="utf-8",
    )
    result = _stop(tmp_path, "claude", {}, path=tmp_path)
    reason = str(_load(result.stdout)["reason"])
    assert "uv run pytest -q" in reason


def test_integrate_merges_idempotently_and_preserves_user_hooks(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    claude = {
        "permissions": {"allow": ["Bash"]},
        "hooks": {
            "PreToolUse": [
                {
                    "matcher": "Bash",
                    "hooks": [{"type": "command", "command": "echo user-pre"}],
                }
            ],
            "Stop": [
                {"hooks": [{"type": "command", "command": "echo user-stop"}]},
                {
                    "matcher": "ignored",
                    "hooks": [{"type": "command", "command": stop_command("claude")}],
                },
            ],
        },
    }
    cursor = {
        "version": 2,
        "hooks": {
            "sessionStart": [{"command": "./session-init.sh"}],
            "stop": [{"command": "./audit.sh", "loop_limit": 10}],
        },
    }
    codex = {
        "description": "workspace hooks",
        "hooks": {"Stop": [{"hooks": [{"type": "command", "command": "echo codex-user"}]}]},
    }
    hook_config_path(tmp_path, "claude").parent.mkdir(parents=True)
    hook_config_path(tmp_path, "claude").write_text(json.dumps(claude), encoding="utf-8")
    hook_config_path(tmp_path, "cursor").parent.mkdir(parents=True)
    hook_config_path(tmp_path, "cursor").write_text(json.dumps(cursor), encoding="utf-8")
    hook_config_path(tmp_path, "codex").parent.mkdir(parents=True)
    hook_config_path(tmp_path, "codex").write_text(json.dumps(codex), encoding="utf-8")

    plain = runner.invoke(app, ["integrate", "--path", str(tmp_path)])
    assert plain.exit_code == 0, plain.stdout
    assert "echo user-stop" in hook_config_path(tmp_path, "claude").read_text(encoding="utf-8")
    assert stop_command("cursor") not in hook_config_path(tmp_path, "cursor").read_text(
        encoding="utf-8"
    )

    installed = runner.invoke(app, ["integrate", "--hooks", "--path", str(tmp_path)])
    assert installed.exit_code == 0, installed.stdout
    again = runner.invoke(app, ["integrate", "--hooks", "--path", str(tmp_path)])
    assert again.exit_code == 0, again.stdout

    claude_body = json.loads(hook_config_path(tmp_path, "claude").read_text(encoding="utf-8"))
    assert claude_body["permissions"] == {"allow": ["Bash"]}
    commands = [
        item["command"]
        for group in claude_body["hooks"]["Stop"]
        for item in group["hooks"]
    ]
    assert commands.count(stop_command("claude")) == 1
    assert "echo user-stop" in commands
    session_commands_claude = [
        item["command"]
        for group in claude_body["hooks"]["SessionStart"]
        for item in group["hooks"]
    ]
    assert session_commands_claude == [session_start_command("claude")]
    assert "echo user-pre" in json.dumps(claude_body["hooks"]["PreToolUse"])
    ours = [
        item
        for group in claude_body["hooks"]["Stop"]
        for item in group["hooks"]
        if item["command"] == stop_command("claude")
    ]
    assert ours == [
        {"type": "command", "command": stop_command("claude"), "timeout": 30}
    ]
    first_text = hook_config_path(tmp_path, "claude").read_text(encoding="utf-8")
    runner.invoke(app, ["integrate", "--hooks", "--host", "claude", "--path", str(tmp_path)])
    assert hook_config_path(tmp_path, "claude").read_text(encoding="utf-8") == first_text

    cursor_body = json.loads(hook_config_path(tmp_path, "cursor").read_text(encoding="utf-8"))
    assert cursor_body["version"] == 2
    session_commands = [item["command"] for item in cursor_body["hooks"]["sessionStart"]]
    assert session_commands == ["./session-init.sh", session_start_command("cursor")]
    assert cursor_body["hooks"]["sessionStart"][1]["timeout"] == 30
    assert "loop_limit" not in cursor_body["hooks"]["sessionStart"][1]
    stop_commands = [item["command"] for item in cursor_body["hooks"]["stop"]]
    assert stop_commands == ["./audit.sh", stop_command("cursor")]
    retornatus_stop = cursor_body["hooks"]["stop"][1]
    assert retornatus_stop["loop_limit"] == CURSOR_LOOP_LIMIT

    codex_body = json.loads(hook_config_path(tmp_path, "codex").read_text(encoding="utf-8"))
    assert codex_body["description"] == "workspace hooks"
    codex_commands = [
        item["command"]
        for group in codex_body["hooks"]["Stop"]
        for item in group["hooks"]
    ]
    assert "echo codex-user" in codex_commands
    assert codex_commands.count(stop_command("codex")) == 1
    codex_session = [
        item["command"]
        for group in codex_body["hooks"]["SessionStart"]
        for item in group["hooks"]
    ]
    assert codex_session == [session_start_command("codex")]


def test_remove_hooks_keeps_user_entries_and_deletes_ours_only(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    only = runner.invoke(
        app,
        ["integrate", "--hooks", "--host", "cursor", "--path", str(tmp_path)],
    )
    assert only.exit_code == 0, only.stdout
    assert hook_config_path(tmp_path, "cursor").is_file()
    assert not hook_config_path(tmp_path, "claude").exists()
    assert not hook_config_path(tmp_path, "codex").exists()

    hook_config_path(tmp_path, "claude").parent.mkdir(parents=True, exist_ok=True)
    hook_config_path(tmp_path, "claude").write_text(
        json.dumps(
            {
                "permissions": {"deny": ["Read"]},
                "hooks": {
                    "Stop": [
                        {
                            "matcher": "only-ours",
                            "hooks": [{"type": "command", "command": stop_command("claude")}],
                        },
                        {"hooks": [{"type": "command", "command": "echo stay"}]},
                    ],
                    "SessionStart": [
                        {
                            "hooks": [
                                {"type": "command", "command": session_start_command("claude")},
                                {"type": "command", "command": "echo session-stay"},
                            ]
                        }
                    ],
                },
            }
        ),
        encoding="utf-8",
    )
    removed = runner.invoke(app, ["integrate", "--remove-hooks", "--path", str(tmp_path)])
    assert removed.exit_code == 0, removed.stdout
    assert not hook_config_path(tmp_path, "cursor").exists()
    claude_body = json.loads(hook_config_path(tmp_path, "claude").read_text(encoding="utf-8"))
    assert claude_body["permissions"] == {"deny": ["Read"]}
    assert claude_body["hooks"]["Stop"] == [
        {"hooks": [{"type": "command", "command": "echo stay"}]}
    ]
    assert claude_body["hooks"]["SessionStart"] == [
        {"hooks": [{"type": "command", "command": "echo session-stay"}]}
    ]
    assert "removed" in removed.stdout
    again = runner.invoke(app, ["integrate", "--remove-hooks", "--host", "claude", "--path", str(tmp_path)])
    assert again.exit_code == 0, again.stdout
    assert "absent" in again.stdout


def test_invalid_hook_json_is_not_overwritten(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    path = hook_config_path(tmp_path, "codex")
    path.parent.mkdir(parents=True)
    path.write_text("{not json", encoding="utf-8")
    result = runner.invoke(app, ["integrate", "--hooks", "--host", "codex", "--path", str(tmp_path)])
    assert result.exit_code == 2
    assert path.read_text(encoding="utf-8") == "{not json"
    assert "not valid JSON" in result.stderr


def test_hook_flags_reject_conflicts(tmp_path: Path) -> None:
    both = runner.invoke(
        app,
        ["integrate", "--hooks", "--remove-hooks", "--path", str(tmp_path)],
    )
    assert both.exit_code == 2
    lonely = runner.invoke(app, ["integrate", "--host", "cursor", "--path", str(tmp_path)])
    assert lonely.exit_code == 2
    unknown = runner.invoke(
        app,
        ["integrate", "--hooks", "--host", "kiro", "--path", str(tmp_path)],
    )
    assert unknown.exit_code == 2
    assert "Unknown host" in unknown.stderr


def test_doctor_reports_agent_hook_installation(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    before = run_doctor(tmp_path)
    rendered = before.render()
    assert "agent hooks:" in rendered
    assert "claude: absent" in rendered
    assert "cursor: absent" in rendered
    assert "codex: absent" in rendered

    installed = runner.invoke(app, ["integrate", "--hooks", "--path", str(tmp_path)])
    assert installed.exit_code == 0, installed.stdout
    after = runner.invoke(app, ["doctor", "--path", str(tmp_path)])
    assert after.exit_code == 0, after.stdout
    assert "claude: stop=installed session-start=installed" in after.stdout
    assert "cursor: stop=installed session-start=installed" in after.stdout
    assert "codex: stop=installed session-start=installed" in after.stdout

    hook_config_path(tmp_path, "claude").write_text("{", encoding="utf-8")
    broken = run_doctor(tmp_path)
    assert broken.agent_hooks["claude"] == "unreadable"
    assert "claude: unreadable" in broken.render()


def _start(root: Path, host: str, payload: object, *, path: Path | None = None) -> object:
    args = ["hook", "session-start", "--host", host]
    if path is not None:
        args.extend(["--path", str(path)])
    raw = payload if isinstance(payload, str) else json.dumps(payload)
    return runner.invoke(app, args, input=raw)


_CLAUDE_PAYLOAD = {
    "session_id": "abc123",
    "transcript_path": "/tmp/session.jsonl",
    "cwd": "/tmp/proj",
    "hook_event_name": "SessionStart",
    "source": "startup",
    "model": "claude-sonnet-5",
    "unused": True,
}
_CURSOR_PAYLOAD = {
    "session_id": "conv-1",
    "is_background_agent": False,
    "composer_mode": "agent",
}
_CODEX_PAYLOAD = {
    "session_id": "abc123",
    "cwd": "/tmp/proj",
    "hook_event_name": "SessionStart",
    "source": "resume",
}


def _context(stdout: str, host: str) -> str:
    body = _load(stdout)
    if host == "cursor":
        assert set(body) == {"additional_context"}
        text = body["additional_context"]
    else:
        assert set(body) == {"hookSpecificOutput"}
        inner = body["hookSpecificOutput"]
        assert isinstance(inner, dict)
        assert set(inner) == {"hookEventName", "additionalContext"}
        assert inner["hookEventName"] == "SessionStart"
        text = inner["additionalContext"]
    assert isinstance(text, str)
    return text


def test_session_start_shapes_name_the_finish_line(tmp_path: Path) -> None:
    _create(
        tmp_path,
        title="Health command",
    )
    created = runner.invoke(
        app,
        [
            "change",
            "create",
            "--path",
            str(tmp_path),
            "--title",
            "Ignored draft",
            "--demand",
            "Operators need a second command that stays a draft",
            "--what",
            "The second command stays a draft",
            "--done",
            _DONE,
            "--situation",
            "Operators run one health command and read its exit code.",
            "--draft-contract",
        ],
    )
    assert created.exit_code == 0, created.stdout + created.stderr
    payloads = {
        "claude": _CLAUDE_PAYLOAD,
        "cursor": _CURSOR_PAYLOAD,
        "codex": _CODEX_PAYLOAD,
    }
    for host, payload in payloads.items():
        result = _start(tmp_path, host, payload, path=tmp_path)
        assert result.exit_code == 0, result.output
        assert result.stderr == ""
        text = _context(result.stdout, host)
        assert len(text.encode("utf-8")) <= CONTEXT_BYTE_CAP
        assert "C-0001 Health command — INCONCLUSIVE" in text
        assert "goal: The health command exits 0" in text
        assert "scope: (none declared)" in text
        assert "C-0001/claim-done-1 (INCONCLUSIVE)" in text
        assert "retornatus evidence run" in text
        assert "pytest -q" in text
        assert "C-0002" not in text


def test_session_start_includes_declared_scope_and_satisfied_changes(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    created = runner.invoke(
        app,
        [
            "change",
            "create",
            "--path",
            str(tmp_path),
            "--title",
            "Scoped",
            "--demand",
            "Operators need a health command with a clear exit code",
            "--what",
            "The health command exits 0",
            "--done",
            _DONE,
            "--situation",
            "Operators run one health command and read its exit code.",
            "--task",
            "Implement the health command",
            "--resource",
            "0:src/retornatus/",
            "--resource",
            "0:tests/",
        ],
    )
    assert created.exit_code == 0, created.stdout + created.stderr
    _satisfy(tmp_path)
    result = _start(tmp_path, "cursor", _CURSOR_PAYLOAD, path=tmp_path)
    text = _context(result.stdout, "cursor")
    assert "C-0001 Scoped — SATISFIED" in text
    assert "scope: src/retornatus/, tests/" in text
    assert "unproven: none" in text


def test_session_start_empty_without_an_active_change(tmp_path: Path) -> None:
    missing = _start(tmp_path, "claude", _CLAUDE_PAYLOAD, path=tmp_path)
    assert missing.exit_code == 0
    assert missing.stdout == ""
    assert missing.stderr == ""

    _create(tmp_path, draft=True)
    draft = _start(tmp_path, "codex", "", path=tmp_path)
    assert draft.exit_code == 0, draft.output
    assert draft.stdout == ""

    listed = _start(tmp_path, "cursor", "[]", path=tmp_path)
    assert listed.exit_code == 0
    assert listed.stdout == ""


def test_session_start_respects_session_context_flag(tmp_path: Path) -> None:
    _create(tmp_path)
    config = tmp_path / ".retornatus" / "config.toml"
    original = config.read_text(encoding="utf-8")
    config.write_text(original + "\n[hooks]\nsession_context = false\n", encoding="utf-8")
    disabled = _start(tmp_path, "claude", _CLAUDE_PAYLOAD, path=tmp_path)
    assert disabled.exit_code == 0
    assert disabled.stdout == ""
    assert disabled.stderr == ""

    config.write_text(original + "\n[hooks]\nsession_context = true\n", encoding="utf-8")
    enabled = _start(tmp_path, "codex", _CODEX_PAYLOAD, path=tmp_path)
    assert "C-0001" in _context(enabled.stdout, "codex")

    config.write_text(original + '\n[hooks]\nsession_context = "yes"\n', encoding="utf-8")
    invalid = _start(tmp_path, "cursor", _CURSOR_PAYLOAD, path=tmp_path)
    assert invalid.exit_code == 0
    assert invalid.stdout == ""
    assert "fail-open" in invalid.stderr
    assert "session_context" in invalid.stderr


def test_session_start_fails_open(tmp_path: Path, monkeypatch) -> None:
    _create(tmp_path)
    broken = _start(tmp_path, "claude", "{", path=tmp_path)
    assert broken.exit_code == 0
    assert broken.stdout == ""
    assert "fail-open" in broken.stderr
    assert "invalid JSON" in broken.stderr

    unknown = _start(tmp_path, "copilot", _CLAUDE_PAYLOAD, path=tmp_path)
    assert unknown.exit_code == 0
    assert unknown.stdout == ""
    assert "unknown host" in unknown.stderr

    def boom(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("disk failed")

    monkeypatch.setattr(
        "retornatus.application.agent_hooks.session.evaluate_change_assurance",
        boom,
    )
    crashed = _start(tmp_path, "cursor", _CURSOR_PAYLOAD, path=tmp_path)
    assert crashed.exit_code == 0
    assert crashed.stdout == ""
    assert "disk failed" in crashed.stderr
    assert "fail-open" in crashed.stderr


def test_session_start_caps_context(tmp_path: Path) -> None:
    _create(tmp_path)
    contract_path = tmp_path / ".retornatus" / "changes" / "C-0001" / "contract.json"
    document = json.loads(contract_path.read_text(encoding="utf-8"))
    document["what"] = "goal " * 4000
    contract_path.write_text(json.dumps(document), encoding="utf-8")
    result = _start(tmp_path, "claude", _CLAUDE_PAYLOAD, path=tmp_path)
    assert result.exit_code == 0, result.output
    text = _context(result.stdout, "claude")
    assert len(text.encode("utf-8")) <= CONTEXT_BYTE_CAP
    assert text.endswith("…(truncated)\n")
    assert "C-0001" in text


def test_session_start_edges(tmp_path: Path, monkeypatch) -> None:
    from retornatus.application.agent_hooks.session import cap_utf8

    assert cap_utf8("abcdef", limit=4) == "\n…"

    initialize_project(tmp_path)
    config = tmp_path / ".retornatus" / "config.toml"
    _create_resources = runner.invoke(
        app,
        [
            "change",
            "create",
            "--path",
            str(tmp_path),
            "--title",
            "Edges",
            "--demand",
            "Operators need a health command with a clear exit code",
            "--what",
            "The health command exits 0",
            "--done",
            _DONE,
            "--situation",
            "Operators run one health command and read its exit code.",
            "--task",
            "Implement the health command",
            *[
                item
                for index in range(13)
                for item in ("--resource", f"0:pkg{index}/")
            ],
        ],
    )
    assert _create_resources.exit_code == 0, _create_resources.stdout
    original = config.read_text(encoding="utf-8")
    config.write_text('hooks = "nope"\n\n' + original, encoding="utf-8")
    broken_table = _start(tmp_path, "claude", _CLAUDE_PAYLOAD, path=tmp_path)
    assert broken_table.exit_code == 0
    assert broken_table.stdout == ""
    assert "expected a table" in broken_table.stderr

    config.write_text(original + '\n[hooks]\nnote = "keep"\n', encoding="utf-8")
    kept = _start(tmp_path, "claude", _CLAUDE_PAYLOAD, path=tmp_path)
    text = _context(kept.stdout, "claude")
    assert "pkg0/" in text
    assert "+1 more" in text

    nested = tmp_path / "src" / "pkg"
    nested.mkdir(parents=True)
    monkeypatch.chdir(nested)
    walked = runner.invoke(app, ["hook", "session-start", "--host", "codex"], input="{}")
    assert walked.exit_code == 0, walked.output
    assert "C-0001" in _context(walked.stdout, "codex")


def test_doctor_reports_a_stop_only_install(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    path = hook_config_path(tmp_path, "cursor")
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "version": 1,
                "hooks": {"stop": [{"command": stop_command("cursor"), "loop_limit": 1}]},
            }
        ),
        encoding="utf-8",
    )
    report = run_doctor(tmp_path)
    assert report.agent_hooks["cursor"] == "stop=installed session-start=absent"
    assert "cursor: stop=installed session-start=absent" in report.render()
