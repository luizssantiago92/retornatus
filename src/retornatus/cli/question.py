"""CLI command group: question."""

from __future__ import annotations

from pathlib import Path

import typer

from retornatus.cli.groups import question_app


@question_app.command("open")
def question_open(
    change_id: str = typer.Option(..., "--change", "-c"),
    statement: str = typer.Option(..., "--statement", "-s"),
    finding: list[str] = typer.Option(..., "--finding", "-f"),
    number: int | None = typer.Option(
        None,
        "--number",
        help="Question number (default: auto-increment next free).",
    ),
    path: Path | None = typer.Option(None, "--path", "-p"),
) -> None:
    """Open a Question grounded in one or more Findings."""
    from retornatus.application.question.loop import QuestionLoop

    q = QuestionLoop(path or Path.cwd()).open_question(
        change_id=change_id,
        statement=statement,
        finding_ids=list(finding),
        number=number,
    )
    typer.echo(f"Opened {q.id}")


@question_app.command("resolve")
def question_resolve(
    question_id: str = typer.Argument(...),
    summary: str = typer.Option(..., "--summary", "-s"),
    evidence: list[str] | None = typer.Option(None, "--evidence", "-e"),
    path: Path | None = typer.Option(None, "--path", "-p"),
) -> None:
    """Resolve a Question with established summary + Evidence when required."""
    from retornatus.application.question.loop import (
        QuestionLoop,
        ResolutionIncompleteError,
    )

    try:
        q = QuestionLoop(path or Path.cwd()).resolve_question(
            question_id,
            summary=summary,
            evidence_ids=list(evidence or []),
        )
    except ResolutionIncompleteError as exc:
        typer.echo(str(exc))
        raise typer.Exit(1) from exc
    typer.echo(f"Resolved {q.id}")


@question_app.command("reopen")
def question_reopen(
    question_id: str = typer.Argument(...),
    path: Path | None = typer.Option(None, "--path", "-p"),
) -> None:
    """Reopen a resolved Question (clears Resolution; condition may have reappeared)."""
    from retornatus.application.question.loop import QuestionLoop

    q = QuestionLoop(path or Path.cwd()).reopen_question(question_id)
    typer.echo(f"Reopened {q.id} (lifecycle={q.lifecycle.value})")
