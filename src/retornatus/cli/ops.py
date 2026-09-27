"""CLI command group: ops."""

from __future__ import annotations

from pathlib import Path

import typer

from retornatus.cli.common import resolve_root
from retornatus.cli.groups import ops_app

@ops_app.command("list")
def ops_list() -> None:
    """List built-in operational hygiene loops."""
    from retornatus.application.operations import list_ops_loops

    for loop in list_ops_loops():
        typer.echo(f"{loop.id}\t{loop.title}\t{loop.description}")


@ops_app.command("show")
def ops_show(
    loop_id: str = typer.Argument(..., help="e.g. doctor-hygiene"),
) -> None:
    """Show one operational loop recipe."""
    from retornatus.application.operations import show_ops_loop

    try:
        loop = show_ops_loop(loop_id)
    except ValueError as exc:
        typer.echo(str(exc))
        raise typer.Exit(1) from exc
    typer.echo(f"{loop.id}: {loop.title}")
    typer.echo(loop.description)
    typer.echo("steps:")
    for step in loop.steps:
        typer.echo(f"  - {step}")


@ops_app.command("run")
def ops_run(
    loop_id: str = typer.Argument(..., help="e.g. gate-scan"),
    path: Path | None = typer.Option(None, "--path", "-p"),
) -> None:
    """Run an operational hygiene loop."""
    from retornatus.application.operations import run_ops_loop

    root = resolve_root(path)
    try:
        result = run_ops_loop(root, loop_id)
    except ValueError as exc:
        typer.echo(str(exc))
        raise typer.Exit(1) from exc
    typer.echo(result.output)
    raise typer.Exit(code=0 if result.ok else 1)
