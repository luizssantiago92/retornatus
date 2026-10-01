"""CLI command group: loop."""

from __future__ import annotations

from pathlib import Path

import typer

from retornatus.cli.groups import loop_app


@loop_app.command("next")
def loop_next(
    change_id: str = typer.Argument(...),
    path: Path | None = typer.Option(None, "--path", "-p"),
    all_ready: bool = typer.Option(
        False,
        "--all-ready",
        help="List all READY tasks (parallelizable projection).",
    ),
) -> None:
    """Project the next ready Question, Task, or Action (not a Loop Engine)."""
    from retornatus.application.change.loop import project_next_work

    projection = project_next_work(path or Path.cwd(), change_id)
    if projection.primary is None:
        typer.echo("Nothing found.")
        raise typer.Exit(1)
    if all_ready and len(projection.ready) > 1:
        for item in projection.ready:
            typer.echo(f"{item.kind}\t{item.id}\t{item.summary}")
        if projection.parallelizable_task_ids:
            typer.echo("parallelizable\t" + ",".join(projection.parallelizable_task_ids))
        return
    item = projection.primary
    typer.echo(f"{item.kind}\t{item.id}\t{item.summary}")
    if len(projection.ready) > 1:
        typer.echo(f"# also ready: {len(projection.ready) - 1} more (use --all-ready)")
