"""Situation as requirements analysis — vague asks, options, kickoff, answers."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from retornatus.application.change.situation import (
    MAX_FOCUSED_QUESTIONS,
    apply_answers,
    assess_situation,
    collect_repo_signals,
    discover_kickoff,
    merge_answers_into_inputs,
    parse_answer_option,
)
from retornatus.bootstrap.init import initialize_project
from retornatus.cli.main import app


def test_vague_demand_asks_focused_questions_with_options() -> None:
    assessment = assess_situation(demand="Add login")
    assert not assessment.sufficient_for_contract
    assert 1 <= len(assessment.focused_questions) <= MAX_FOCUSED_QUESTIONS
    assert any(q.options for q in assessment.focused_questions)
    topics = {q.topic.lower() for q in assessment.focused_questions}
    assert topics & {"actors", "scope", "out_of_scope", "success", "what", "done"}
    md = assessment.to_markdown(demand="Add login")
    assert "Focused questions" in md
    assert "1." in md


def test_short_demand_with_clear_what_and_done_skips_workshop() -> None:
    assessment = assess_situation(
        demand="Add login",
        what="Email and password session for end users",
        done_criteria=["pytest covers successful login returns a session"],
    )
    assert assessment.sufficient_for_contract
    assert not assessment.focused_questions


def test_clear_demand_with_what_and_done_is_sufficient() -> None:
    assessment = assess_situation(
        demand="Add a health endpoint for ops liveness checks",
        what='GET /health returns 200 and {"status":"ok"}',
        done_criteria=[
            "Automated pytest covers GET /health returns 200",
            "Endpoint documented in docs/health.md",
        ],
        repo_signals=["stack manifests: `pyproject.toml`", "tests: pytest"],
    )
    assert assessment.sufficient_for_contract
    assert not any(q.topic.lower() == "language" for q in assessment.focused_questions)


def test_kickoff_facts_suppress_reask(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "brief.md").write_text(
        "# Brief\n\n"
        "- Primary actor: end users of the reports page\n"
        "- Out of scope: PDF export and scheduled emails\n"
        "- Acceptance: CSV download for selected date range\n",
        encoding="utf-8",
    )
    sources, facts = discover_kickoff(tmp_path)
    assert "docs/brief.md" in sources
    assert any("actor" in f.lower() or "users" in f.lower() for f in facts)

    assessment = assess_situation(
        demand="Add export",
        kickoff_sources=sources,
        kickoff_facts=facts,
    )
    topics = {q.topic.lower() for q in assessment.focused_questions}
    # Kickoff already spoke to actors / out_of_scope — do not re-ask
    assert "actors" not in topics
    assert "out_of_scope" not in topics
    assert not assessment.sufficient_for_contract


def test_answers_can_clear_questions_and_become_sufficient() -> None:
    first = assess_situation(demand="Improve search")
    assert not first.sufficient_for_contract
    assert first.focused_questions

    what_m, done_m, constraints_m, remaining = merge_answers_into_inputs(
        what=None,
        done_criteria=[],
        constraints=[],
        answers={
            "WHAT": "Search returns matching titles within 200ms on the sample index",
            "DONE": "pytest covers empty query and one hit",
            "actors": "End user of the product",
            "scope": "Happy path only for title search",
            "out_of_scope": "No ranking ML changes",
            "success": "Automated test proves the behavior",
        },
    )
    second = assess_situation(
        demand="Improve search",
        what=what_m,
        done_criteria=done_m,
        constraints=constraints_m,
        answered_topics={t.lower() for t in remaining},
    )
    second = apply_answers(second, remaining)
    assert second.sufficient_for_contract
    assert not second.focused_questions


def test_repo_signals_do_not_ask_language(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
    signals = collect_repo_signals(tmp_path)
    assessment = assess_situation(
        demand="Add a health endpoint for ops liveness",
        what="GET /health returns 200",
        done_criteria=["pytest covers GET /health"],
        repo_signals=signals,
    )
    assert not any(q.topic.lower() == "language" for q in assessment.focused_questions)
    assert any("pytest" in c.lower() for c in assessment.constraints)


def test_parse_answer_option() -> None:
    assert parse_answer_option("scope=Happy path only") == ("scope", "Happy path only")
    assert parse_answer_option("DONE: pytest covers it") == ("DONE", "pytest covers it")


def test_cli_elicit_answer_and_write(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    runner = CliRunner()
    out_path = tmp_path / "situation-draft.md"
    result = runner.invoke(
        app,
        [
            "change",
            "elicit",
            "--path",
            str(tmp_path),
            "--demand",
            "Add login",
            "--answer",
            "WHAT=Email+password session for end users",
            "--answer",
            "DONE=pytest covers successful login",
            "--answer",
            "actors=End user of the product",
            "--answer",
            "scope=Happy path only for one primary flow",
            "--answer",
            "out_of_scope=No new auth providers",
            "--answer",
            "success=Automated test proves the behavior",
            "--write",
            str(out_path),
        ],
    )
    assert result.exit_code == 0, result.output
    assert out_path.is_file()
    assert "Sufficient: **yes**" in out_path.read_text(encoding="utf-8")


def test_cli_elicit_vague_exits_one(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "change",
            "elicit",
            "--path",
            str(tmp_path),
            "--demand",
            "Add login",
        ],
    )
    assert result.exit_code == 1
    assert "Focused questions" in result.output
