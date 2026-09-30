"""Stop hook: question heuristic, transcript tail, and per-host payloads."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from typer.testing import CliRunner

from retornatus.application.agent_hooks.questions import (
    TRANSCRIPT_TAIL_BYTES,
    is_question_to_user,
    last_assistant_text_from_jsonl,
)
from retornatus.application.assurance.evaluate import infer_claim_subject
from retornatus.application.assurance.evidence import EvidenceService
from retornatus.bootstrap.doctor import run_doctor
from retornatus.bootstrap.init import initialize_project
from retornatus.cli.main import app

runner = CliRunner()

_DONE = "pytest exits 0 for the health command"


def _create(root: Path) -> None:
    initialize_project(root)
    created = runner.invoke(
        app,
        [
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
        ],
    )
    assert created.exit_code == 0, created.stdout + created.stderr


def _satisfy(root: Path) -> None:
    EvidenceService(root).run(
        change_id="C-0001",
        evidence_type="test_result",
        subject=infer_claim_subject(_DONE),
        command=[sys.executable, "-c", "print('ok')"],
        supports_claim_id="C-0001/claim-done-1",
    )


def _stop(root: Path, host: str, payload: object) -> object:
    raw = payload if isinstance(payload, str) else json.dumps(payload)
    return runner.invoke(
        app,
        ["hook", "stop", "--host", host, "--path", str(root)],
        input=raw,
    )


def _jsonl(path: Path, lines: list[object]) -> None:
    path.write_text(
        "".join(json.dumps(line) + "\n" for line in lines),
        encoding="utf-8",
    )


def _assistant(text: str) -> dict[str, object]:
    return {
        "type": "assistant",
        "message": {
            "role": "assistant",
            "content": [{"type": "text", "text": text}],
        },
    }


def test_question_heuristic_positives_and_negatives() -> None:
    positives = [
        "Should I continue?",
        "Posso seguir?",
        "Quer que eu abra o PR？",
        "The work is done.\n\nDo you want me to commit?",
        "Should I continue?\n\n```python\nprint('x?')\n```",
        "Posso seguir com o próximo passo",
        "I finished the patch. Should I open the PR",
        "Ready??",
        'Did you want this?"',
        "```\nkeep?\n```\n\nShall I merge?",
        "Should I continue?\n\n```python\nprint(1)",
    ]
    negatives = [
        "The tests pass.",
        "What about `a?` in the name.",
        "See https://example.com/search?q=1 for the notes.",
        "See https://example.com/search?",
        "I fixed the bug.\n\nAll tests pass.",
        "Did the tests fail?\n\nAll tests pass.",
        "Done.\n\n```python\nif ready?\n    pass\n```",
        "```\nif ready?\n```",
        "```python\nprint('?')",
        "The comment mentioned should i yesterday and I ignored it.",
        "",
        "   ",
    ]
    for text in positives:
        assert is_question_to_user(text), text
    for text in negatives:
        assert not is_question_to_user(text), text


def test_transcript_tail_skips_malformed_lines_and_keeps_last_assistant() -> None:
    body = "\n".join(
        [
            json.dumps(_assistant("Should I start?")),
            "{not json",
            json.dumps({"type": "user", "message": {"role": "user", "content": "no?"}}),
            json.dumps(
                {
                    "role": "assistant",
                    "message": {"content": [{"type": "tool_use", "name": "Bash", "input": {}}]},
                }
            ),
            "[]",
            json.dumps(_assistant("All tests pass.")),
        ]
    )
    assert last_assistant_text_from_jsonl(body) == "All tests pass."
    trailing_user = "\n".join(
        [
            "",
            json.dumps(_assistant("Should I continue?")),
            json.dumps({"type": "user", "message": {"role": "user", "content": "no?"}}),
            json.dumps({"role": "assistant", "content": [{"type": "text", "text": "Quer que eu siga?"}, 1, " extra"]}),
        ]
    )
    assert last_assistant_text_from_jsonl(trailing_user) == "Quer que eu siga?\nextra"
    plain = json.dumps({"role": "assistant", "text": "Shall I merge?"})
    assert last_assistant_text_from_jsonl(plain) == "Shall I merge?"
    assert last_assistant_text_from_jsonl("{broken\n") is None
    assert last_assistant_text_from_jsonl("") is None


def test_each_host_question_field_allows_and_absence_blocks(tmp_path: Path) -> None:
    _create(tmp_path)
    transcript = tmp_path / "session.jsonl"
    _jsonl(transcript, [_assistant("Should I continue?")])
    statement = tmp_path / "statement.jsonl"
    _jsonl(statement, [_assistant("All tests pass.")])

    claude_field = _stop(
        tmp_path,
        "claude",
        {
            "session_id": "s",
            "transcript_path": str(statement),
            "cwd": str(tmp_path),
            "hook_event_name": "Stop",
            "stop_hook_active": False,
            "last_assistant_message": "Should I continue?",
        },
    )
    assert claude_field.exit_code == 0
    assert claude_field.stdout == ""

    claude_file = _stop(
        tmp_path,
        "claude",
        {
            "stop_hook_active": False,
            "transcript_path": str(transcript),
            "last_assistant_message": None,
        },
    )
    assert claude_file.exit_code == 0
    assert claude_file.stdout == ""

    claude_missing = _stop(tmp_path, "claude", {"stop_hook_active": False})
    assert claude_missing.exit_code == 0
    assert json.loads(claude_missing.stdout)["decision"] == "block"

    codex_field = _stop(
        tmp_path,
        "codex",
        {
            "session_id": "s",
            "transcript_path": None,
            "cwd": str(tmp_path),
            "hook_event_name": "Stop",
            "turn_id": "t",
            "stop_hook_active": False,
            "last_assistant_message": "Posso seguir?",
        },
    )
    assert codex_field.exit_code == 0
    assert codex_field.stdout == ""

    codex_file = _stop(
        tmp_path,
        "codex",
        {"stop_hook_active": False, "transcript_path": str(transcript)},
    )
    assert codex_file.exit_code == 0
    assert codex_file.stdout == ""

    codex_missing = _stop(tmp_path, "codex", {"turn_id": "t", "stop_hook_active": False})
    assert json.loads(codex_missing.stdout)["decision"] == "block"

    cursor_file = _stop(
        tmp_path,
        "cursor",
        {
            "status": "completed",
            "loop_count": 0,
            "conversation_id": "c",
            "transcript_path": str(transcript),
            "last_assistant_message": "this cursor field is not documented",
        },
    )
    assert cursor_file.exit_code == 0
    assert cursor_file.stdout == ""

    cursor_missing = _stop(
        tmp_path,
        "cursor",
        {"status": "completed", "loop_count": 2, "transcript_path": None},
    )
    body = json.loads(cursor_missing.stdout)
    assert set(body) == {"followup_message"}
    assert "C-0001/claim-done-1" in str(body["followup_message"])

    cursor_statement = _stop(
        tmp_path,
        "cursor",
        {"status": "completed", "loop_count": 0, "transcript_path": str(statement)},
    )
    assert "followup_message" in json.loads(cursor_statement.stdout)


def test_direct_field_beats_an_older_transcript_question(tmp_path: Path) -> None:
    _create(tmp_path)
    transcript = tmp_path / "old.jsonl"
    _jsonl(transcript, [_assistant("Should I continue?")])
    result = _stop(
        tmp_path,
        "claude",
        {
            "last_assistant_message": "All tests pass.",
            "transcript_path": str(transcript),
            "stop_hook_active": False,
        },
    )
    assert json.loads(result.stdout)["decision"] == "block"


def test_transcript_tail_ignores_bytes_before_the_window(tmp_path: Path) -> None:
    _create(tmp_path)
    path = tmp_path / "long.jsonl"
    head = json.dumps(_assistant("Should I continue?")) + "\n"
    pad = ("x" * 200) + "\n"
    tail = json.dumps(_assistant("All tests pass.")) + "\n"
    filler = pad * ((TRANSCRIPT_TAIL_BYTES // len(pad)) + 4)
    path.write_bytes((head + filler + tail).encode("utf-8"))
    assert path.stat().st_size > TRANSCRIPT_TAIL_BYTES
    blocked = _stop(
        tmp_path,
        "cursor",
        {"status": "completed", "loop_count": 0, "transcript_path": str(path)},
    )
    assert "followup_message" in json.loads(blocked.stdout)

    question_tail = json.dumps(_assistant("Quer que eu siga?")) + "\n"
    path.write_bytes((filler + question_tail).encode("utf-8"))
    allowed = _stop(
        tmp_path,
        "codex",
        {"stop_hook_active": False, "transcript_path": str(path)},
    )
    assert allowed.stdout == ""


def test_missing_transcript_and_malformed_tail_do_not_allow(tmp_path: Path) -> None:
    _create(tmp_path)
    missing = _stop(
        tmp_path,
        "cursor",
        {"status": "completed", "loop_count": 0, "transcript_path": str(tmp_path / "nope.jsonl")},
    )
    assert json.loads(missing.stdout)["followup_message"]

    broken = tmp_path / "broken.jsonl"
    broken.write_text("{not json\n[1, 2]\n", encoding="utf-8")
    still = _stop(
        tmp_path,
        "claude",
        {"stop_hook_active": False, "transcript_path": str(broken)},
    )
    assert json.loads(still.stdout)["decision"] == "block"


def test_allow_questions_false_blocks_and_other_values_stay_open(tmp_path: Path) -> None:
    _create(tmp_path)
    config = tmp_path / ".retornatus" / "config.toml"
    payload = {"last_assistant_message": "Should I continue?", "stop_hook_active": False}

    config.write_text(config.read_text(encoding="utf-8") + "\n[hooks]\nallow_questions = false\n", encoding="utf-8")
    blocked = _stop(tmp_path, "claude", payload)
    assert json.loads(blocked.stdout)["decision"] == "block"
    assert "hooks allow_questions: false" in run_doctor(tmp_path).render()

    for status in ("aborted", "error"):
        allowed = _stop(tmp_path, "cursor", {"status": status, "loop_count": 0})
        assert allowed.stdout == ""

    active = _stop(tmp_path, "codex", {"stop_hook_active": True, "last_assistant_message": "done"})
    assert active.stdout == ""

    config.write_text(
        config.read_text(encoding="utf-8").replace(
            "allow_questions = false",
            'allow_questions = "false"',
        ),
        encoding="utf-8",
    )
    still_open = _stop(tmp_path, "claude", payload)
    assert still_open.stdout == ""
    assert "hooks allow_questions: true" in run_doctor(tmp_path).render()


def test_doctor_reports_default_allow_questions(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    rendered = run_doctor(tmp_path).render()
    assert "hooks allow_questions: true" in rendered


def test_satisfied_change_still_allows_a_statement(tmp_path: Path) -> None:
    _create(tmp_path)
    _satisfy(tmp_path)
    result = _stop(
        tmp_path,
        "claude",
        {"last_assistant_message": "All tests pass.", "stop_hook_active": False},
    )
    assert result.exit_code == 0
    assert result.stdout == ""
