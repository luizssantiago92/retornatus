"""CLI command group: checks."""

from __future__ import annotations

from pathlib import Path

import typer

from retornatus.cli.common import resolve_root
from retornatus.cli.groups import checks_app


@checks_app.command("run")
def checks_run(
    change_id: str = typer.Option(..., "--change", "-c"),
    timeout: float = typer.Option(
        120.0,
        "--timeout",
        help="Seconds before each required check is killed.",
    ),
    path: Path | None = typer.Option(None, "--path", "-p"),
) -> None:
    """Run [assurance] required_checks and record executed Evidence."""
    from retornatus.application.assurance.checks import run_required_checks

    root = resolve_root(path)
    outcome = run_required_checks(root, change_id, timeout_seconds=timeout)
    for note in outcome.notes:
        typer.echo(f"WARN {note}")
    for evidence in outcome.evidence:
        typer.echo(
            f"Recorded {evidence.id} argv={' '.join(evidence.command or [])} "
            f"exit_code={evidence.exit_code}"
        )
    raise typer.Exit(0 if outcome.all_passed else 1)
