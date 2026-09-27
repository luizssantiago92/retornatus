"""CLI command group: action."""

from __future__ import annotations

from pathlib import Path

import typer

from retornatus.cli.groups import action_app

@action_app.command("budget")
def action_budget_cmd(
    action_id: str = typer.Argument(..., help="Action id (C-xxxx/A-yyy)."),
    max_attempts: int | None = typer.Option(
        None,
        "--max",
        help="Maximum attempts before gate budget STOPs. Omit with --clear.",
    ),
    clear: bool = typer.Option(
        False,
        "--clear",
        help="Remove the attempt ceiling (unlimited).",
    ),
    path: Path | None = typer.Option(None, "--path", "-p"),
) -> None:
    """Set or clear an Action attempt budget."""
    from retornatus.application.change.tasks import TaskService

    if clear:
        action = TaskService(path or Path.cwd()).set_max_attempts(action_id, None)
    elif max_attempts is None:
        typer.echo("Provide --max N or --clear")
        raise typer.Exit(code=1)
    else:
        action = TaskService(path or Path.cwd()).set_max_attempts(
            action_id, max_attempts
        )
    typer.echo(
        f"{action.id}: max_attempts={action.max_attempts!r} "
        f"attempt_count={action.attempt_count}"
    )
