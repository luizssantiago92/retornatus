"""Public CLI entrypoint — intentions, not internal machinery (PRD §62)."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from retornatus import __version__
from retornatus.bootstrap.init import initialize_project

app = typer.Typer(
    name="retornatus",
    help=(
        "Repo-native governance harness for AI-assisted software development.\n\n"
        "Govern the work. Bound the agent. Verify the outcome."
    ),
    no_args_is_help=True,
    add_completion=False,
)


def version_callback(value: bool) -> None:
    if value:
        typer.echo(f"retornatus {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-V",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """Retornatus CLI."""


@app.command()
def init(
    path: Optional[Path] = typer.Argument(
        None,
        help="Project root to initialize (default: current directory).",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Recreate canonical files even if already initialized.",
    ),
) -> None:
    """Initialize a minimal `.retornatus/` project in the repository."""
    result = initialize_project(path, force=force)

    if result.already_initialized and not force:
        typer.echo(f"Already initialized: {result.retornatus_dir}")
        typer.echo("Use --force to recreate canonical files.")
        raise typer.Exit(code=0)

    typer.echo(f"Initialized Retornatus at {result.retornatus_dir}")


@app.command()
def wake() -> None:
    """Reconstruct project continuity from repository-native state (M4)."""
    typer.echo("wake is not implemented yet (planned for M4).")
    raise typer.Exit(code=1)


@app.command()
def status() -> None:
    """Report derived project status (M4+)."""
    typer.echo("status is not implemented yet.")
    raise typer.Exit(code=1)


@app.command()
def doctor() -> None:
    """Run diagnostics on Retornatus state and environment."""
    typer.echo("doctor is not implemented yet.")
    raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
