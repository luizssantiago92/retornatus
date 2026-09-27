"""CLI command group: finding."""

from __future__ import annotations

from pathlib import Path

import typer

from retornatus.cli.groups import finding_app

@finding_app.command("add")
def finding_add(
    change_id: str = typer.Option(..., "--change", "-c"),
    observation: str = typer.Option(..., "--observation", "-o"),
    source: str | None = typer.Option(None, "--source"),
    number: int | None = typer.Option(
        None,
        "--number",
        help="Finding number (default: auto-increment next free).",
    ),
    path: Path | None = typer.Option(None, "--path", "-p"),
) -> None:
    """Record a Finding (relevant observation)."""
    from retornatus.application.question.loop import QuestionLoop

    finding = QuestionLoop(path or Path.cwd()).record_finding(
        change_id=change_id,
        observation=observation,
        number=number,
        source=source,
    )
    typer.echo(f"Recorded {finding.id}")
