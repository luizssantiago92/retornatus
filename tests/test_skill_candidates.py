"""Repetition detector, candidate queue, and the stop / session-start line."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from typer.testing import CliRunner

from retornatus.application.adaptation.skill_candidates import (
    accept_candidate,
    correction_counts,
    format_candidates,
    list_candidates,
    looks_like_report,
    normalize_command,
    pending_notice,
    reject_candidate,
    scan_skill_candidates,
    user_texts_from_transcript,
)
from retornatus.application.adaptation.skills import SkillService
from retornatus.application.assurance.evaluate import infer_claim_subject
from retornatus.application.assurance.evidence import EvidenceService
from retornatus.application.change.workflow import ChangeWorkflow
from retornatus.bootstrap.init import initialize_project
from retornatus.cli.main import app
from retornatus.domain.enums import EvidenceProvenance
from retornatus.domain.models import Evidence
from retornatus.infrastructure.persistence.repository import FileRepository

runner = CliRunner()
ROOT = Path(__file__).resolve().parents[1]
WIDGET = ["python", "scripts/widget_catalog_migrate.py"]
INVOICE = ["python", "scripts/invoice_export.py"]
NOTICE = "1 skill candidate pending: run `retornatus skill candidates`"
_DONE = "pytest exits 0 for the health command"


def _stamp(index: int) -> datetime:
    return datetime(2026, 1, 1, tzinfo=UTC) + timedelta(minutes=index)


def _init(root: Path) -> FileRepository:
    initialize_project(root)
    return FileRepository(root)


def _configure(root: Path, **values: object) -> None:
    repo = FileRepository(root)
    data, revision = repo.load_config()
    data["adaptation"] = {"skill_candidates": values}
    repo.save_config(data, expected=revision)


def _change(root: Path, title: str, *, activate: bool = True) -> str:
    result = ChangeWorkflow(root).create_change(
        title=title,
        demand_statement=f"The user runs the CLI and must finish {title} with a recorded result",
        situation="The operator runs one command and reads the recorded evidence.",
        what=f"Deliver {title} for the operator CLI",
        done_criteria=[_DONE],
        action_objective=f"Deliver {title}",
        activate_contract=activate,
    )
    return result.change.id


def _record(root: Path, change_id: str, argv: list[str], exit_code: int, index: int) -> None:
    number = len(EvidenceService(root).list_for_change(change_id)) + 1
    evidence = Evidence(
        id=f"{change_id}/E-{number:03d}",
        type="test_result",
        subject="behavior",
        source="test",
        producer="test",
        provenance=EvidenceProvenance.EXECUTED,
        command=list(argv),
        exit_code=exit_code,
        observed_at=_stamp(index),
    )
    FileRepository(root).save_evidence(evidence)


def _repeat(
    root: Path,
    argv: list[str],
    title: str,
    *,
    times: int = 3,
    exit_code: int = 0,
    activate: bool = True,
) -> list[str]:
    change_ids: list[str] = []
    for offset in range(times):
        change_id = _change(root, f"{title} {offset}", activate=activate)
        _record(root, change_id, argv, exit_code, len(change_ids) + 1)
        change_ids.append(change_id)
    return change_ids


def test_normalize_command_keeps_stable_relative_paths_and_collapses_variables() -> None:
    assert normalize_command(WIDGET) == "python scripts/widget_catalog_migrate.py"
    assert normalize_command(["pytest", "/tmp/C-0001/test_12.py", "#12"]) == "pytest <PATH>/test_12.py <PR>"
    assert normalize_command(["python", "/tmp/a/versions.py"]) != normalize_command(["python", "/tmp/a/changelog.py"])
    assert normalize_command(["python", "/tmp/a/versions.py"]) == normalize_command(["python", "/tmp/b/versions.py"])
    assert normalize_command(["echo", "sha", "abcdef1234567890"]) == "echo sha <HASH>"
    assert normalize_command(["build", "2026-10-01", "C-0004/claim-done-1"]) == "build <DATE> <ID>"


def test_correction_counts_group_the_same_pattern() -> None:
    counts = correction_counts(
        [
            "no, use the widget script",
            "No, use the catalog",
            "não, use o outro",
            "don't rewrite it",
            "do not skip the check",
            "actually the path is scripts/",
            "na verdade use o catalogo",
        ]
    )
    assert counts["use-correction"] == 3
    assert counts["dont"] == 2
    assert counts["actually"] == 2


def test_transcript_user_lines_skip_assistant_and_malformed_json(tmp_path: Path) -> None:
    path = tmp_path / "session.jsonl"
    path.write_text(
        "\n".join(
            [
                "{not json",
                json.dumps({"type": "assistant", "message": {"role": "assistant", "content": "done"}}),
                json.dumps({"type": "user", "message": {"role": "user", "content": "no, use pytest"}}),
                json.dumps({"role": "human", "text": "actually use ruff"}),
            ]
        ),
        encoding="utf-8",
    )
    assert user_texts_from_transcript(path) == ["no, use pytest", "actually use ruff"]
    assert user_texts_from_transcript(tmp_path / "missing.jsonl") == []


def test_report_filter_blocks_identifier_dumps_and_keeps_programs() -> None:
    report = "echo shipped C-0001 C-0002 C-0003 PR #12 #13 on 2026-10-01"
    assert looks_like_report([report])
    assert not looks_like_report([" ".join(WIDGET)])


def test_sequence_of_three_green_changes_queues_one_candidate(tmp_path: Path) -> None:
    _init(tmp_path)
    change_ids = _repeat(tmp_path, WIDGET, "Migrate the widget catalog")
    result = scan_skill_candidates(tmp_path, focal_change_id=change_ids[-1], session_id="s")
    assert result.created_id == "K-0001"
    assert result.notice == NOTICE
    queued = list_candidates(tmp_path)
    assert len(queued) == 1
    assert queued[0].status == "pending"
    assert queued[0].kind == "new"
    assert "sequence" in queued[0].signals
    assert queued[0].count == 3
    assert set(queued[0].origin_changes) == set(change_ids)
    assert "python scripts/widget_catalog_migrate.py" in queued[0].commands
    assert (tmp_path / ".retornatus/adaptation/skill-candidates/K-0001.md").is_file()


def test_two_changes_and_failed_only_changes_suggest_nothing(tmp_path: Path) -> None:
    _init(tmp_path)
    _repeat(tmp_path, WIDGET, "Migrate the widget catalog", times=2)
    short = scan_skill_candidates(tmp_path, session_id="s")
    assert short.created_id is None
    assert short.skipped_reason == "nothing"
    _repeat(tmp_path, INVOICE, "Export the invoice batch", times=3, exit_code=1)
    failed = scan_skill_candidates(tmp_path, session_id="s2")
    assert failed.created_id is None
    assert list_candidates(tmp_path) == []


def test_threshold_can_hold_back_a_repeated_sequence(tmp_path: Path) -> None:
    _init(tmp_path)
    _configure(tmp_path, threshold=9)
    _repeat(tmp_path, WIDGET, "Migrate the widget catalog")
    result = scan_skill_candidates(tmp_path, session_id="s")
    assert result.created_id is None
    assert result.skipped_reason == "below-threshold"
    assert list_candidates(tmp_path) == []


def test_retry_scores_and_stays_under_the_default_threshold(tmp_path: Path) -> None:
    _init(tmp_path)
    change_id = _change(tmp_path, "Migrate the widget catalog")
    _record(tmp_path, change_id, WIDGET, 1, 1)
    _record(tmp_path, change_id, WIDGET, 0, 2)
    held = scan_skill_candidates(tmp_path, focal_change_id=change_id, session_id="s")
    assert held.created_id is None
    assert held.skipped_reason == "below-threshold"
    _configure(tmp_path, threshold=2)
    queued = scan_skill_candidates(tmp_path, focal_change_id=change_id, session_id="s2")
    assert queued.created_id == "K-0001"
    assert "retry" in list_candidates(tmp_path)[0].signals


def test_retry_adds_to_a_repeated_sequence(tmp_path: Path) -> None:
    _init(tmp_path)
    change_ids = _repeat(tmp_path, WIDGET, "Migrate the widget catalog", times=2)
    retried = _change(tmp_path, "Migrate the widget catalog again")
    _record(tmp_path, retried, WIDGET, 1, 10)
    _record(tmp_path, retried, WIDGET, 0, 11)
    result = scan_skill_candidates(tmp_path, focal_change_id=retried, session_id="s")
    assert result.created_id == "K-0001"
    item = list_candidates(tmp_path)[0]
    assert "sequence" in item.signals
    assert "retry" in item.signals
    assert set(item.origin_changes) == set([*change_ids, retried])


def test_correction_signal_runs_only_when_text_is_passed(tmp_path: Path) -> None:
    _init(tmp_path)
    _configure(tmp_path, threshold=2)
    missing = scan_skill_candidates(tmp_path, session_id="s")
    assert missing.created_id is None
    assert missing.skipped_reason == "nothing"
    queued = scan_skill_candidates(
        tmp_path,
        session_id="s2",
        user_texts=["no, use the widget script", "No, use the catalog"],
    )
    assert queued.created_id == "K-0001"
    item = list_candidates(tmp_path)[0]
    assert item.signals == ("correction",)
    assert "use-correction" in item.reason


def test_required_checks_and_trivial_changes_are_excluded(tmp_path: Path) -> None:
    repo = _init(tmp_path)
    data, revision = repo.load_config()
    data["assurance"] = {
        "required_checks": [{"name": "pytest", "run": ["uv", "run", "pytest", "-q"], "types": ["test_result"]}]
    }
    repo.save_config(data, expected=revision)
    _repeat(tmp_path, ["uv", "run", "pytest", "-q"], "Ship the health command")
    checks = scan_skill_candidates(tmp_path, session_id="s")
    assert checks.created_id is None
    _repeat(tmp_path, WIDGET, "Typo fix", times=3)
    trivial = scan_skill_candidates(tmp_path, session_id="s2")
    assert trivial.created_id is None
    assert list_candidates(tmp_path) == []


def test_report_sequences_are_not_queued(tmp_path: Path) -> None:
    _init(tmp_path)
    report = ["echo", "shipped", "C-0001", "C-0002", "C-0003", "PR", "#12", "#13", "on", "2026-10-01"]
    _repeat(tmp_path, report, "Publish the weekly status")
    result = scan_skill_candidates(tmp_path, session_id="s")
    assert result.created_id is None
    assert result.skipped_reason == "report"
    assert list_candidates(tmp_path) == []


def test_session_limit_allows_one_new_candidate(tmp_path: Path) -> None:
    _init(tmp_path)
    _repeat(tmp_path, WIDGET, "Migrate the widget catalog")
    first = scan_skill_candidates(tmp_path, session_id="session-a")
    assert first.created_id == "K-0001"
    _repeat(tmp_path, INVOICE, "Export the invoice batch")
    blocked = scan_skill_candidates(tmp_path, session_id="session-a")
    assert blocked.created_id is None
    assert blocked.skipped_reason == "session-limit"
    assert [item.id for item in list_candidates(tmp_path)] == ["K-0001"]
    opened = scan_skill_candidates(tmp_path, session_id="session-b")
    assert opened.created_id == "K-0002"


def test_reject_waits_for_two_new_changes(tmp_path: Path) -> None:
    _init(tmp_path)
    _repeat(tmp_path, WIDGET, "Migrate the widget catalog")
    scan_skill_candidates(tmp_path, session_id="session-a")
    reject_candidate(tmp_path, "K-0001")
    _repeat(tmp_path, WIDGET, "Migrate the widget catalog extra", times=1)
    waiting = scan_skill_candidates(tmp_path, session_id="session-c")
    assert waiting.created_id is None
    assert waiting.skipped_reason == "rejected-wait"
    _repeat(tmp_path, WIDGET, "Migrate the widget catalog later", times=1)
    returned = scan_skill_candidates(tmp_path, session_id="session-d")
    assert returned.created_id == "K-0002"
    pending = [item for item in list_candidates(tmp_path) if item.status == "pending"]
    assert [item.id for item in pending] == ["K-0002"]


def test_accept_writes_a_draft_skill_and_reject_is_terminal(tmp_path: Path) -> None:
    _init(tmp_path)
    _repeat(tmp_path, WIDGET, "Migrate the widget catalog")
    scan_skill_candidates(tmp_path, session_id="s")
    created = accept_candidate(tmp_path, "K-0001")
    assert created.action == "created"
    assert created.skill_status == "DRAFT"
    skill, body, _revision = FileRepository(tmp_path).load_skill(created.skill_id)
    assert skill.status.value == "DRAFT"
    assert "widget_catalog_migrate" in body
    assert "PROCEDURE" in body
    with pytest.raises(ValueError, match="accepted"):
        accept_candidate(tmp_path, "K-0001")
    with pytest.raises(ValueError, match="accepted"):
        reject_candidate(tmp_path, "K-0001")
    again = scan_skill_candidates(tmp_path, session_id="later")
    assert again.skipped_reason == "accepted-exists"


def test_accept_evolves_an_existing_skill_instead_of_creating_one(tmp_path: Path) -> None:
    _init(tmp_path)
    SkillService(tmp_path).create_for_specialization(
        specialization="widget catalog migration",
        title="Widget catalog",
    )
    _repeat(tmp_path, WIDGET, "Migrate the widget catalog")
    scan_skill_candidates(tmp_path, session_id="s")
    queued = list_candidates(tmp_path)[0]
    assert queued.kind == "improve"
    assert queued.existing_skill_id == "S-0001"
    evolved = accept_candidate(tmp_path, queued.id)
    assert evolved.action == "evolved"
    assert evolved.skill_id == "S-0001"
    assert evolved.skill_version == 2
    assert len(FileRepository(tmp_path).list_skills()) == 1
    _skill, body, _revision = FileRepository(tmp_path).load_skill("S-0001")
    assert "widget_catalog_migrate" in body


def test_disabled_detector_is_silent(tmp_path: Path) -> None:
    _init(tmp_path)
    _repeat(tmp_path, WIDGET, "Migrate the widget catalog")
    scan_skill_candidates(tmp_path, session_id="s")
    _configure(tmp_path, enabled=False)
    assert pending_notice(tmp_path) == ""
    result = scan_skill_candidates(tmp_path, session_id="s2")
    assert result.created_id is None
    assert result.skipped_reason == "disabled"
    assert result.notice == ""


def test_cli_lists_accepts_and_rejects(tmp_path: Path) -> None:
    _init(tmp_path)
    empty = runner.invoke(app, ["skill", "candidates", "--path", str(tmp_path)])
    assert empty.exit_code == 0
    assert empty.stdout.strip() == "No skill candidates."
    _repeat(tmp_path, WIDGET, "Migrate the widget catalog")
    scan_skill_candidates(tmp_path, session_id="s")
    listed = runner.invoke(app, ["skill", "candidates", "--path", str(tmp_path)])
    assert listed.exit_code == 0
    assert "K-0001" in listed.stdout
    assert "pending" in listed.stdout
    missing = runner.invoke(app, ["skill", "accept", "K-9999", "--path", str(tmp_path)])
    assert missing.exit_code == 1
    rejected = runner.invoke(app, ["skill", "reject", "K-0001", "--path", str(tmp_path)])
    assert rejected.exit_code == 0
    assert "Rejected K-0001" in rejected.stdout
    assert format_candidates(list_candidates(tmp_path)).splitlines()[0].startswith("K-0001\trejected")


def test_stop_and_session_start_mention_a_pending_candidate_without_blocking(tmp_path: Path) -> None:
    _init(tmp_path)
    active = _change(tmp_path, "Health command", activate=True)
    EvidenceService(tmp_path).run(
        change_id=active,
        evidence_type="test_result",
        subject=infer_claim_subject(_DONE),
        command=[sys.executable, "-c", "print('ok')"],
        supports_claim_id=f"{active}/claim-done-1",
    )
    _repeat(tmp_path, WIDGET, "Migrate the widget catalog", activate=False)
    scan_skill_candidates(tmp_path, session_id="setup")
    payload = {"status": "completed", "loop_count": 0, "session_id": "cursor-session"}
    first = runner.invoke(
        app,
        ["hook", "stop", "--host", "cursor", "--path", str(tmp_path)],
        input=json.dumps(payload),
    )
    assert first.exit_code == 0, first.output
    body = json.loads(first.stdout)
    assert body == {"followup_message": NOTICE}
    second = runner.invoke(
        app,
        ["hook", "stop", "--host", "cursor", "--path", str(tmp_path)],
        input=json.dumps(payload),
    )
    assert second.exit_code == 0, second.output
    assert second.stdout == ""

    claude = runner.invoke(
        app,
        ["hook", "stop", "--host", "claude", "--path", str(tmp_path)],
        input=json.dumps({"stop_hook_active": False, "session_id": "claude-session"}),
    )
    assert claude.exit_code == 0, claude.output
    claude_body = json.loads(claude.stdout)
    assert claude_body == {"additionalContext": NOTICE}
    assert "decision" not in claude_body

    subagent = runner.invoke(
        app,
        ["hook", "subagent-stop", "--host", "cursor", "--path", str(tmp_path)],
        input=json.dumps({"status": "completed", "loop_count": 0, "session_id": "sub"}),
    )
    assert subagent.exit_code == 0, subagent.output
    assert subagent.stdout == ""

    started = runner.invoke(
        app,
        ["hook", "session-start", "--host", "cursor", "--path", str(tmp_path)],
        input=json.dumps({"session_id": "cursor-session"}),
    )
    assert started.exit_code == 0, started.output
    context = json.loads(started.stdout)["additional_context"]
    assert NOTICE in context


def test_unsatisfied_stop_does_not_mention_the_candidate(tmp_path: Path) -> None:
    _init(tmp_path)
    _change(tmp_path, "Health command", activate=True)
    _repeat(tmp_path, WIDGET, "Migrate the widget catalog", activate=False)
    scan_skill_candidates(tmp_path, session_id="setup")
    blocked = runner.invoke(
        app,
        ["hook", "stop", "--host", "cursor", "--path", str(tmp_path)],
        input=json.dumps({"status": "completed", "loop_count": 0, "session_id": "s"}),
    )
    assert blocked.exit_code == 0, blocked.output
    message = json.loads(blocked.stdout)["followup_message"]
    assert "claim-done-1" in message
    assert "skill candidate" not in message


def test_hub_skill_tells_the_agent_not_to_accept_alone() -> None:
    text = (ROOT / "src/retornatus/infrastructure/environment/hub/SKILL.md").read_text(encoding="utf-8")
    assert "retornatus skill candidates" in text
    assert "Never run `skill accept`" in text
