"""File-edit scope hook: host payloads, path checks, modes, and install."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from retornatus.application.agent_hooks.config import (
    CLAUDE_FILE_EDIT_MATCHER,
    CODEX_FILE_EDIT_MATCHER,
    CURSOR_FILE_EDIT_MATCHER,
    file_edit_command,
    hook_config_path,
    session_start_command,
    stop_command,
)
from retornatus.bootstrap.doctor import run_doctor
from retornatus.bootstrap.init import initialize_project
from retornatus.cli.main import app

runner = CliRunner()

_DONE = "pytest exits 0 for the health command"
_WARNING_TAIL = (
    "Revert the edit, or update the Change scope (Task resources) to include this path."
)


def _create(root: Path, *resources: str, draft: bool = False, title: str = "Scoped") -> None:
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
        "--task",
        "Implement the health command",
    ]
    for resource in resources:
        args.extend(["--resource", f"0:{resource}"])
    if draft:
        args.append("--draft-contract")
    created = runner.invoke(app, args)
    assert created.exit_code == 0, created.stdout + created.stderr


def _edit(root: Path, host: str, payload: object, *, path: Path | None = None) -> object:
    args = ["hook", "file-edit", "--host", host]
    if path is not None:
        args.extend(["--path", str(path)])
    raw = payload if isinstance(payload, str) else json.dumps(payload)
    return runner.invoke(app, args, input=raw)


def _mode(root: Path, value: str) -> None:
    _hooks_table(root, f'scope_mode = "{value}"')


def _hooks_table(root: Path, body: str) -> None:
    config = root / ".retornatus" / "config.toml"
    text = config.read_text(encoding="utf-8")
    marker = "\n[hooks]\n"
    if marker in text:
        text = text.split(marker, 1)[0].rstrip() + "\n"
    config.write_text(text + f"\n[hooks]\n{body}\n", encoding="utf-8")


def _load(stdout: str) -> dict[str, object]:
    document = json.loads(stdout)
    assert isinstance(document, dict)
    return document


def _warning(stdout: str, host: str, *, deny: bool = False) -> str:
    body = _load(stdout)
    if host == "cursor":
        if deny:
            assert set(body) == {"permission", "agent_message"}
            assert body["permission"] == "deny"
            text = body["agent_message"]
        else:
            assert set(body) == {"additional_context"}
            text = body["additional_context"]
    else:
        assert set(body) == {"hookSpecificOutput"}
        inner = body["hookSpecificOutput"]
        assert isinstance(inner, dict)
        if deny:
            assert set(inner) == {"hookEventName", "permissionDecision", "permissionDecisionReason"}
            assert inner["hookEventName"] == "PreToolUse"
            assert inner["permissionDecision"] == "deny"
            text = inner["permissionDecisionReason"]
        else:
            assert set(inner) == {"hookEventName", "additionalContext"}
            text = inner["additionalContext"]
    assert isinstance(text, str)
    return text


def test_hosts_warn_with_their_documented_payload(tmp_path: Path) -> None:
    _create(tmp_path, "src/")
    outside = "docs/other.py"
    claude = _edit(
        tmp_path,
        "claude",
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Edit",
            "tool_input": {"file_path": outside, "old_string": "a", "new_string": "b"},
            "unused": True,
        },
        path=tmp_path,
    )
    assert claude.exit_code == 0, claude.output
    assert claude.stderr == ""
    text = _warning(claude.stdout, "claude")
    assert "docs/other.py is outside C-0001 scope (src/)" in text
    assert _WARNING_TAIL in text

    cursor = _edit(
        tmp_path,
        "cursor",
        {
            "hook_event_name": "postToolUse",
            "tool_name": "Write",
            "tool_input": {"path": outside},
        },
        path=tmp_path,
    )
    assert "docs/other.py is outside C-0001 scope (src/)" in _warning(cursor.stdout, "cursor")

    patch = "*** Begin Patch\n*** Update File: docs/other.py\n@@\n-a\n+b\n*** End Patch\n"
    codex = _edit(
        tmp_path,
        "codex",
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "apply_patch",
            "tool_input": {"command": patch},
        },
        path=tmp_path,
    )
    assert "docs/other.py is outside C-0001 scope (src/)" in _warning(codex.stdout, "codex")


def test_in_scope_retornatus_and_no_active_change_are_silent(tmp_path: Path) -> None:
    _create(tmp_path, "src/", "tests/**")
    inside = [
        {"tool_name": "Write", "tool_input": {"file_path": "src/app.py"}},
        {"tool_name": "MultiEdit", "tool_input": {"file_path": "src/pkg/app.py"}},
        {"tool_name": "Edit", "tool_input": {"file_path": ".retornatus/config.toml"}},
        {"tool_name": "Edit", "tool_input": {"file_path": "tests/test_app.py"}},
        {"tool_name": "Read", "tool_input": {"file_path": "docs/readme.md"}},
    ]
    for payload in inside:
        result = _edit(tmp_path, "claude", payload, path=tmp_path)
        assert result.exit_code == 0, result.output
        assert result.stdout == ""
        assert result.stderr == ""

    missing = _edit(tmp_path / "empty", "codex", {"tool_name": "apply_patch"}, path=tmp_path / "empty")
    assert missing.stdout == ""
    assert missing.stderr == ""

    draft = tmp_path / "draft"
    draft.mkdir()
    _create(draft, "src/", draft=True)
    quiet = _edit(
        draft,
        "cursor",
        {"hook_event_name": "postToolUse", "tool_name": "Write", "tool_input": {"file_path": "nope.py"}},
        path=draft,
    )
    assert quiet.stdout == ""
    assert quiet.stderr == ""


def test_path_normalization_absolute_windows_and_outside(tmp_path: Path) -> None:
    _create(tmp_path, "src/")
    absolute = _edit(
        tmp_path,
        "claude",
        {"tool_name": "Write", "tool_input": {"file_path": str(tmp_path / "src" / "app.py")}},
        path=tmp_path,
    )
    assert absolute.stdout == ""

    windows = _edit(
        tmp_path,
        "claude",
        {"tool_name": "Edit", "tool_input": {"file_path": "src\\pkg\\app.py"}},
        path=tmp_path,
    )
    assert windows.stdout == ""

    slashed = str(tmp_path / "src" / "app.py").replace("/", "\\")
    mixed = _edit(
        tmp_path,
        "cursor",
        {"hook_event_name": "postToolUse", "tool_name": "Write", "tool_input": {"file_path": slashed}},
        path=tmp_path,
    )
    assert mixed.stdout == ""

    outside = _edit(
        tmp_path,
        "claude",
        {"tool_name": "Write", "tool_input": {"file_path": str(tmp_path.parent / "outside.py")}},
        path=tmp_path,
    )
    text = _warning(outside.stdout, "claude")
    assert "outside.py is outside C-0001 scope (src/)" in text

    escaped = _edit(
        tmp_path,
        "codex",
        {
            "tool_name": "apply_patch",
            "tool_input": {"command": "*** Update File: ../outside.py\n"},
        },
        path=tmp_path,
    )
    assert "../outside.py is outside C-0001 scope (src/)" in _warning(escaped.stdout, "codex")

    drive = _edit(
        tmp_path,
        "claude",
        {"tool_name": "Write", "tool_input": {"file_path": "C:\\project\\src\\index.ts"}},
        path=tmp_path,
    )
    drive_text = _warning(drive.stdout, "claude")
    assert "C:/project/src/index.ts is outside C-0001 scope (src/)" in drive_text


def test_codex_patch_shapes_and_partial_scope(tmp_path: Path) -> None:
    _create(tmp_path, "src/")
    patch = (
        "*** Begin Patch\n"
        "*** Update File: src/app.py\n"
        "*** Move to: src/renamed.py\n"
        "*** Add File: docs/new.md\n"
        "*** Delete File: src/app.py\n"
        "*** End Patch\n"
    )
    listed = _edit(
        tmp_path,
        "codex",
        {"tool_name": "apply_patch", "tool_input": {"command": ["apply_patch", patch]}},
        path=tmp_path,
    )
    text = _warning(listed.stdout, "codex")
    assert "docs/new.md is outside C-0001 scope (src/)" in text
    assert "src/app.py" not in text
    assert "src/renamed.py" not in text

    raw = _edit(
        tmp_path,
        "codex",
        {"tool_name": "Write", "tool_input": "*** Add File: notes.md\n"},
        path=tmp_path,
    )
    assert "notes.md is outside C-0001 scope (src/)" in _warning(raw.stdout, "codex")

    ignored = _edit(
        tmp_path,
        "codex",
        {"tool_name": "Bash", "tool_input": {"command": "rm src/app.py"}},
        path=tmp_path,
    )
    assert ignored.stdout == ""


def test_several_active_changes_must_all_cover_the_path(tmp_path: Path) -> None:
    _create(tmp_path, "src/")
    second = runner.invoke(
        app,
        [
            "change",
            "create",
            "--path",
            str(tmp_path),
            "--title",
            "Tests",
            "--demand",
            "Operators need a health command with a clear exit code",
            "--what",
            "The health command exits 0",
            "--done",
            _DONE,
            "--situation",
            "Operators run one health command and read its exit code.",
            "--task",
            "Cover the tests",
            "--resource",
            "0:tests/",
        ],
    )
    assert second.exit_code == 0, second.stdout + second.stderr
    missed = _edit(
        tmp_path,
        "claude",
        {"tool_name": "Edit", "tool_input": {"file_path": "src/app.py"}},
        path=tmp_path,
    )
    text = _warning(missed.stdout, "claude")
    assert "src/app.py is outside C-0002 scope (tests/)" in text
    assert "C-0001" not in text

    both = _edit(
        tmp_path,
        "claude",
        {"tool_name": "Edit", "tool_input": {"file_path": "README.md"}},
        path=tmp_path,
    )
    both_text = _warning(both.stdout, "claude")
    assert "C-0001 scope (src/)" in both_text
    assert "C-0002 scope (tests/)" in both_text


def test_modes_block_off_and_fail_open(tmp_path: Path, monkeypatch) -> None:
    _create(tmp_path, "src/")
    payload = {
        "hook_event_name": "PreToolUse",
        "tool_name": "Edit",
        "tool_input": {"file_path": "docs/guide.md"},
    }
    _mode(tmp_path, "block")
    denied = _edit(tmp_path, "claude", payload, path=tmp_path)
    assert "docs/guide.md is outside C-0001 scope (src/)" in _warning(denied.stdout, "claude", deny=True)

    cursor_pre = _edit(
        tmp_path,
        "cursor",
        {"hook_event_name": "preToolUse", "tool_name": "Write", "tool_input": {"file_path": "docs/guide.md"}},
        path=tmp_path,
    )
    assert "docs/guide.md" in _warning(cursor_pre.stdout, "cursor", deny=True)

    cursor_post = _edit(
        tmp_path,
        "cursor",
        {"hook_event_name": "postToolUse", "tool_name": "Write", "tool_input": {"file_path": "docs/guide.md"}},
        path=tmp_path,
    )
    assert "docs/guide.md" in _warning(cursor_post.stdout, "cursor", deny=False)

    codex_post = _edit(
        tmp_path,
        "codex",
        {
            "hook_event_name": "PostToolUse",
            "tool_name": "apply_patch",
            "tool_input": {"command": "*** Add File: docs/guide.md\n"},
        },
        path=tmp_path,
    )
    body = _load(codex_post.stdout)
    inner = body["hookSpecificOutput"]
    assert isinstance(inner, dict)
    assert inner["hookEventName"] == "PostToolUse"
    assert "additionalContext" in inner
    assert "permissionDecision" not in inner

    _mode(tmp_path, "off")
    silent = _edit(tmp_path, "claude", payload, path=tmp_path)
    assert silent.stdout == ""
    assert silent.stderr == ""

    _hooks_table(tmp_path, "scope_mode = false")
    bad = _edit(tmp_path, "codex", payload, path=tmp_path)
    assert bad.exit_code == 0
    assert bad.stdout == ""
    assert "fail-open" in bad.stderr
    assert "scope_mode" in bad.stderr

    config = tmp_path / ".retornatus" / "config.toml"
    config.write_text('hooks = "nope"\n', encoding="utf-8")
    broken = _edit(tmp_path, "claude", payload, path=tmp_path)
    assert broken.stdout == ""
    assert "expected a table" in broken.stderr

    config.write_text("schema_version = 1\n\n[project]\ninitialized = true\n", encoding="utf-8")
    unknown = _edit(tmp_path, "copilot", payload, path=tmp_path)
    assert "unknown host" in unknown.stderr
    assert unknown.stdout == ""

    broken_json = _edit(tmp_path, "claude", "{", path=tmp_path)
    assert "invalid JSON" in broken_json.stderr
    listed = _edit(tmp_path, "cursor", "[]", path=tmp_path)
    assert listed.stdout == ""
    assert listed.stderr == ""

    def boom(*_args: object, **_kwargs: object) -> bool:
        raise RuntimeError("disk failed")

    monkeypatch.setattr("retornatus.application.agent_hooks.file_edit.path_in_scope", boom)
    crashed = _edit(tmp_path, "claude", payload, path=tmp_path)
    assert crashed.exit_code == 0
    assert crashed.stdout == ""
    assert "disk failed" in crashed.stderr


def test_cursor_events_without_an_agent_message_stay_silent(tmp_path: Path) -> None:
    _create(tmp_path, "src/")
    for event in ("afterFileEdit", "beforeReadFile"):
        result = _edit(
            tmp_path,
            "cursor",
            {"hook_event_name": event, "file_path": str(tmp_path / "docs" / "out.md"), "edits": []},
            path=tmp_path,
        )
        assert result.exit_code == 0, result.output
        assert result.stdout == ""
        assert result.stderr == ""

    _mode(tmp_path, "block")
    blocked = _edit(
        tmp_path,
        "cursor",
        {"hook_event_name": "afterFileEdit", "file_path": "docs/out.md"},
        path=tmp_path,
    )
    assert blocked.stdout == ""

    _mode(tmp_path, "warn")
    pre = _edit(
        tmp_path,
        "cursor",
        {"hook_event_name": "preToolUse", "tool_name": "Write", "tool_input": {"file_path": "docs/out.md"}},
        path=tmp_path,
    )
    assert pre.stdout == ""


def test_cursor_string_tool_input_and_shell_are_ignored(tmp_path: Path) -> None:
    _create(tmp_path, "src/")
    encoded = _edit(
        tmp_path,
        "cursor",
        {
            "hook_event_name": "postToolUse",
            "tool_name": "Write",
            "tool_input": json.dumps({"filePath": "docs/out.md"}),
        },
        path=tmp_path,
    )
    assert "docs/out.md is outside C-0001 scope (src/)" in _warning(encoded.stdout, "cursor")

    shell = _edit(
        tmp_path,
        "cursor",
        {"hook_event_name": "preToolUse", "tool_name": "Shell", "tool_input": {"command": "rm docs/out.md"}},
        path=tmp_path,
    )
    assert shell.stdout == ""


def test_none_declared_scope_and_walk_up(tmp_path: Path, monkeypatch) -> None:
    _create(tmp_path)
    result = _edit(
        tmp_path,
        "claude",
        {"tool_name": "Write", "tool_input": {"file_path": "src/app.py"}},
        path=tmp_path,
    )
    text = _warning(result.stdout, "claude")
    assert "src/app.py is outside C-0001 scope (none declared)" in text
    kept = _edit(
        tmp_path,
        "claude",
        {"tool_name": "Write", "tool_input": {"file_path": ".retornatus/changes/C-0001/change.json"}},
        path=tmp_path,
    )
    assert kept.stdout == ""

    nested = tmp_path / "src" / "pkg"
    nested.mkdir(parents=True)
    monkeypatch.chdir(nested)
    walked = runner.invoke(
        app,
        ["hook", "file-edit", "--host", "codex"],
        input=json.dumps(
            {"tool_name": "apply_patch", "tool_input": {"command": "*** Add File: src/app.py\n"}}
        ),
    )
    assert walked.exit_code == 0, walked.output
    assert "none declared" in _warning(walked.stdout, "codex")


def test_does_not_call_git(tmp_path: Path, monkeypatch) -> None:
    _create(tmp_path, "src/")

    def boom(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("git called")

    monkeypatch.setattr("retornatus.application.governance.diff.run_git", boom)
    result = _edit(
        tmp_path,
        "claude",
        {"tool_name": "Edit", "tool_input": {"file_path": "docs/out.md"}},
        path=tmp_path,
    )
    assert result.exit_code == 0
    assert "docs/out.md" in _warning(result.stdout, "claude")


def test_install_and_remove_are_idempotent(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    hook_config_path(tmp_path, "claude").parent.mkdir(parents=True)
    hook_config_path(tmp_path, "claude").write_text(
        json.dumps(
            {
                "permissions": {"allow": ["Bash"]},
                "hooks": {
                    "PreToolUse": [
                        {"matcher": "Bash", "hooks": [{"type": "command", "command": "echo user-pre"}]}
                    ]
                },
            }
        ),
        encoding="utf-8",
    )
    hook_config_path(tmp_path, "cursor").parent.mkdir(parents=True)
    hook_config_path(tmp_path, "cursor").write_text(
        json.dumps({"version": 2, "hooks": {"stop": [{"command": "./audit.sh"}]}}),
        encoding="utf-8",
    )

    installed = runner.invoke(app, ["integrate", "--hooks", "--path", str(tmp_path)])
    assert installed.exit_code == 0, installed.stdout
    again = runner.invoke(app, ["integrate", "--hooks", "--path", str(tmp_path)])
    assert again.exit_code == 0, again.stdout

    claude = json.loads(hook_config_path(tmp_path, "claude").read_text(encoding="utf-8"))
    assert claude["permissions"] == {"allow": ["Bash"]}
    user = claude["hooks"]["PreToolUse"][0]
    assert user["matcher"] == "Bash"
    assert user["hooks"][0]["command"] == "echo user-pre"
    ours = [
        item["command"]
        for group in claude["hooks"]["PreToolUse"]
        for item in group["hooks"]
        if item["command"] == file_edit_command("claude")
    ]
    assert ours == [file_edit_command("claude")]
    matched = [
        group
        for group in claude["hooks"]["PreToolUse"]
        if any(item.get("command") == file_edit_command("claude") for item in group["hooks"])
    ]
    assert matched[0]["matcher"] == CLAUDE_FILE_EDIT_MATCHER
    first = hook_config_path(tmp_path, "claude").read_text(encoding="utf-8")
    runner.invoke(app, ["integrate", "--hooks", "--host", "claude", "--path", str(tmp_path)])
    assert hook_config_path(tmp_path, "claude").read_text(encoding="utf-8") == first

    cursor = json.loads(hook_config_path(tmp_path, "cursor").read_text(encoding="utf-8"))
    assert cursor["version"] == 2
    assert [item["command"] for item in cursor["hooks"]["stop"]] == [
        "./audit.sh",
        stop_command("cursor"),
    ]
    for event in ("preToolUse", "postToolUse"):
        commands = [item["command"] for item in cursor["hooks"][event]]
        assert commands == [file_edit_command("cursor")]
        assert cursor["hooks"][event][0]["matcher"] == CURSOR_FILE_EDIT_MATCHER

    codex = json.loads(hook_config_path(tmp_path, "codex").read_text(encoding="utf-8"))
    codex_groups = [
        group
        for group in codex["hooks"]["PreToolUse"]
        if any(item.get("command") == file_edit_command("codex") for item in group["hooks"])
    ]
    assert codex_groups[0]["matcher"] == CODEX_FILE_EDIT_MATCHER
    assert session_start_command("codex") in json.dumps(codex["hooks"]["SessionStart"])

    removed = runner.invoke(app, ["integrate", "--remove-hooks", "--path", str(tmp_path)])
    assert removed.exit_code == 0, removed.stdout
    claude_left = json.loads(hook_config_path(tmp_path, "claude").read_text(encoding="utf-8"))
    assert claude_left["permissions"] == {"allow": ["Bash"]}
    assert claude_left["hooks"]["PreToolUse"] == [
        {"matcher": "Bash", "hooks": [{"type": "command", "command": "echo user-pre"}]}
    ]
    assert "Stop" not in claude_left["hooks"]
    cursor_left = json.loads(hook_config_path(tmp_path, "cursor").read_text(encoding="utf-8"))
    assert list(cursor_left["hooks"]) == ["stop"]
    assert file_edit_command("cursor") not in hook_config_path(tmp_path, "cursor").read_text(encoding="utf-8")
    again_removed = runner.invoke(
        app, ["integrate", "--remove-hooks", "--host", "claude", "--path", str(tmp_path)]
    )
    assert again_removed.exit_code == 0
    assert "absent" in again_removed.stdout


def test_doctor_reports_file_edit_and_scope_mode(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    before = run_doctor(tmp_path)
    rendered = before.render()
    assert "hooks scope_mode: warn" in rendered
    assert "claude: absent" in rendered

    installed = runner.invoke(app, ["integrate", "--hooks", "--path", str(tmp_path)])
    assert installed.exit_code == 0, installed.stdout
    after = run_doctor(tmp_path)
    assert "file-edit=installed" in after.agent_hooks["claude"]
    assert "file-edit=installed" in after.agent_hooks["cursor"]
    assert "file-edit=installed" in after.agent_hooks["codex"]
    assert "hooks scope_mode: warn" in after.render()

    _mode(tmp_path, "block")
    assert "hooks scope_mode: block" in run_doctor(tmp_path).render()
    _hooks_table(tmp_path, "scope_mode = false")
    assert "hooks scope_mode: invalid" in run_doctor(tmp_path).render()


def test_edge_payloads_and_long_scope(tmp_path: Path) -> None:
    _create(tmp_path, "src/")
    dotted = _edit(
        tmp_path,
        "claude",
        {"tool_name": "Edit", "tool_input": {"file_path": "./docs/out.md"}},
        path=tmp_path,
    )
    assert "docs/out.md is outside C-0001 scope (src/)" in _warning(dotted.stdout, "claude")
    blank = _edit(
        tmp_path,
        "claude",
        {"tool_name": "Write", "tool_input": {"file_path": "."}},
        path=tmp_path,
    )
    assert blank.stdout == ""
    empty = _edit(tmp_path, "codex", "", path=tmp_path)
    assert empty.stdout == ""
    assert empty.stderr == ""

    _mode(tmp_path, "block")
    missing_event = _edit(
        tmp_path,
        "cursor",
        {"tool_name": "Write", "tool_input": {"file_path": "docs/out.md"}},
        path=tmp_path,
    )
    assert "docs/out.md" in _warning(missing_event.stdout, "cursor", deny=True)
    _mode(tmp_path, "warn")
    missing_warn = _edit(
        tmp_path,
        "cursor",
        {"hook_event_name": "workspaceOpen", "tool_name": "Write", "tool_input": {"file_path": "docs/out.md"}},
        path=tmp_path,
    )
    assert "docs/out.md" in _warning(missing_warn.stdout, "cursor")

    quiet_patch = _edit(
        tmp_path,
        "codex",
        {"tool_name": "apply_patch", "tool_input": {"command": ["echo", "hello"], "file_path": ""}},
        path=tmp_path,
    )
    assert quiet_patch.stdout == ""
    bad_input = _edit(
        tmp_path,
        "claude",
        {"tool_name": "Edit", "tool_input": "{not json"},
        path=tmp_path,
    )
    assert bad_input.stdout == ""

    wide = tmp_path / "wide"
    wide.mkdir()
    _create(wide, *[f"pkg{index}/" for index in range(13)])
    long_scope = _edit(
        wide,
        "claude",
        {"tool_name": "Write", "tool_input": {"file_path": "other.py"}},
        path=wide,
    )
    text = _warning(long_scope.stdout, "claude")
    assert "pkg0/" in text
    assert "+1 more" in text

    config = wide / ".retornatus" / "config.toml"
    config.write_text(config.read_text(encoding="utf-8") + "\n[hooks]\nallow_questions = true\n", encoding="utf-8")
    still = _edit(
        wide,
        "claude",
        {"tool_name": "Write", "tool_input": {"file_path": "other.py"}},
        path=wide,
    )
    assert still.stdout
    assert "fail-open" not in still.stderr


def test_guide_names_the_hook_and_the_host_docs() -> None:
    text = Path("docs/guide/Agent-hooks.md").read_text(encoding="utf-8")
    for token in (
        "file-edit",
        "scope_mode",
        "additionalContext",
        "additional_context",
        "permissionDecision",
        "afterFileEdit",
        "https://code.claude.com/docs/en/hooks",
        "https://cursor.com/docs/hooks",
        "https://developers.openai.com/codex/hooks",
    ):
        assert token in text
    changelog = Path("CHANGELOG.md").read_text(encoding="utf-8")
    assert "## [Unreleased]" in changelog
    assert "hook file-edit" in changelog.split("## [1.7.0]", 1)[0]
