"""CLI command group: task."""

from __future__ import annotations

from pathlib import Path

import typer

from retornatus.cli.groups import task_app


@task_app.command("start")
def task_start(
    task_id: str = typer.Argument(...),
    path: Path | None = typer.Option(None, "--path", "-p"),
) -> None:
    """Mark a Task ACTIVE."""
    from retornatus.application.change.tasks import TaskLifecycleError, TaskService

    try:
        action = TaskService(path or Path.cwd()).start(task_id)
    except TaskLifecycleError as exc:
        typer.echo(str(exc))
        raise typer.Exit(1) from exc
    typer.echo(f"Started {task_id} on {action.id}")


@task_app.command("complete")
def task_complete(
    task_id: str = typer.Argument(...),
    path: Path | None = typer.Option(None, "--path", "-p"),
) -> None:
    """Mark a Task COMPLETED."""
    from retornatus.application.change.tasks import TaskLifecycleError, TaskService

    try:
        action = TaskService(path or Path.cwd()).complete(task_id)
    except TaskLifecycleError as exc:
        typer.echo(str(exc))
        raise typer.Exit(1) from exc
    typer.echo(f"Completed {task_id} on {action.id}")


@task_app.command("fail")
def task_fail(
    task_id: str = typer.Argument(...),
    path: Path | None = typer.Option(None, "--path", "-p"),
) -> None:
    """Mark a Task FAILED."""
    from retornatus.application.change.tasks import TaskLifecycleError, TaskService

    try:
        action = TaskService(path or Path.cwd()).fail(task_id)
    except TaskLifecycleError as exc:
        typer.echo(str(exc))
        raise typer.Exit(1) from exc
    typer.echo(f"Failed {task_id} on {action.id}")


@task_app.command("reopen")
def task_reopen(
    task_id: str = typer.Argument(...),
    path: Path | None = typer.Option(None, "--path", "-p"),
) -> None:
    """Reopen a COMPLETED/FAILED Task to PENDING."""
    from retornatus.application.change.tasks import TaskLifecycleError, TaskService

    try:
        action = TaskService(path or Path.cwd()).reopen(task_id)
    except TaskLifecycleError as exc:
        typer.echo(str(exc))
        raise typer.Exit(1) from exc
    typer.echo(f"Reopened {task_id} on {action.id}")
