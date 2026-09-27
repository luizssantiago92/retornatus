"""CLI command group: execution."""

from __future__ import annotations

from pathlib import Path

import typer

from retornatus.cli.common import resolve_root
from retornatus.cli.groups import execution_app


@execution_app.command("record")
def execution_record(
    action_id: str = typer.Option(..., "--action", "-a"),
    summary: str = typer.Option(..., "--summary", "-s"),
    ok: bool = typer.Option(True, "--ok/--failed"),
    artifact: list[str] | None = typer.Option(
        None,
        "--artifact",
        help="Artifact path produced by Host execution (repeatable).",
    ),
    producer: str = typer.Option("host", "--producer"),
    path: Path | None = typer.Option(None, "--path", "-p"),
) -> None:
    """Record that Environment-native Host work completed for an Action."""
    from retornatus.application.execution.host_record import HostExecutionService

    root = resolve_root(path)
    record = HostExecutionService(root).record(
        action_id=action_id,
        summary=summary,
        ok=ok,
        artifact_paths=list(artifact or []),
        producer=producer,
        capture_git=True,
    )
    typer.echo(f"Recorded {record.id} for {record.action_id} ok={record.ok}")
    if record.subject_state:
        typer.echo(f"subject_state={record.subject_state}")


@execution_app.command("list")
def execution_list(
    action_id: str = typer.Argument(...),
    path: Path | None = typer.Option(None, "--path", "-p"),
) -> None:
    """List Host Execution records for an Action."""
    from retornatus.application.execution.host_record import HostExecutionService

    root = resolve_root(path)
    records = HostExecutionService(root).list_for_action(action_id)
    if not records:
        typer.echo("No host executions.")
        return
    for record in records:
        typer.echo(f"{record.id}\tok={record.ok}\t{record.summary}")
