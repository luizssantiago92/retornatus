"""CLI command group: hooks."""

from __future__ import annotations

from pathlib import Path

import typer

from retornatus.cli.common import resolve_root
from retornatus.cli.groups import hooks_app


@hooks_app.command("install")
def hooks_install(
    path: Path | None = typer.Option(None, "--path", "-p"),
) -> None:
    """Install pre-commit and commit-msg hooks (chains existing user hooks)."""
    from retornatus.bootstrap.hooks import install_hooks

    report = install_hooks(resolve_root(path))
    typer.echo(report.render())


@hooks_app.command("remove")
def hooks_remove(
    path: Path | None = typer.Option(None, "--path", "-p"),
) -> None:
    """Remove the Retornatus hook block and keep any user hook text."""
    from retornatus.bootstrap.hooks import remove_hooks

    report = remove_hooks(resolve_root(path))
    typer.echo(report.render())


@hooks_app.command("status")
def hooks_status(
    path: Path | None = typer.Option(None, "--path", "-p"),
) -> None:
    """Show the resolved hooks directory and whether Retornatus hooks are installed."""
    from retornatus.bootstrap.hooks import status

    typer.echo(status(resolve_root(path)).render())


@hooks_app.command("scope")
def hooks_scope(
    path: Path | None = typer.Option(None, "--path", "-p"),
) -> None:
    """Run the scope gate for each active Change against the staged diff.

    Used by the pre-commit hook. Exits 0 when no Contract is active.
    """
    from retornatus.application.governance.gates import gate_scope
    from retornatus.bootstrap.hooks import active_change_ids

    root = resolve_root(path)
    change_ids = active_change_ids(root)
    if not change_ids:
        typer.echo("no active change; scope gate skipped")
        raise typer.Exit(0)
    failed = False
    for change_id in change_ids:
        result = gate_scope(root, change_id, staged=True)
        typer.echo(f"{change_id}:")
        for message in result.messages:
            typer.echo(message)
        if not result.passed:
            failed = True
    raise typer.Exit(1 if failed else 0)


@hooks_app.command("commit-msg")
def hooks_commit_msg(
    message_file: Path = typer.Option(
        ...,
        "--message-file",
        help="Path passed by git as $1. This command reads that file only.",
    ),
    path: Path | None = typer.Option(None, "--path", "-p"),
) -> None:
    """Validate a commit message file (the commit-msg hook's $1)."""
    from retornatus.bootstrap.hooks import check_commit_message

    resolve_root(path)
    errors = check_commit_message(message_file)
    if errors:
        for error in errors:
            typer.echo(error, err=True)
        raise typer.Exit(1)
    typer.echo("commit message ok")
