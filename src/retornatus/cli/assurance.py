"""CLI command group: assurance."""

from __future__ import annotations

from pathlib import Path

import typer

from retornatus.cli.common import resolve_root
from retornatus.cli.groups import assurance_app


@assurance_app.command("plan")
def assurance_plan(
    change_id: str = typer.Argument(...),
    action_id: str | None = typer.Option(None, "--action", "-a"),
    path: Path | None = typer.Option(None, "--path", "-p"),
) -> None:
    """Project whether independent Assurance Execution is required."""
    from retornatus.application.assurance.independent import plan_independent_assurance

    root = resolve_root(path)
    plan = plan_independent_assurance(root, change_id, action_id=action_id)
    typer.echo(f"required={plan.required}")
    typer.echo(plan.rationale)
    if plan.claims_needing_review:
        typer.echo("claims: " + ", ".join(plan.claims_needing_review))
    if plan.action_id:
        typer.echo(f"action={plan.action_id}")
    if plan.execution_context is not None:
        typer.echo(
            f"fresh_context independent={plan.execution_context.independent_assurance}"
        )
    raise typer.Exit(code=0 if not plan.required else 2)


@assurance_app.command("review")
def assurance_review(
    change_id: str = typer.Argument(...),
    claim_id: str = typer.Option(..., "--claim"),
    subject: str = typer.Option(..., "--subject", "-s"),
    summary: str = typer.Option(..., "--summary"),
    verdict: str = typer.Option("approved", "--verdict"),
    path: Path | None = typer.Option(None, "--path", "-p"),
) -> None:
    """Record review_result Evidence from an independent Assurance Execution."""
    from retornatus.application.assurance.independent import (
        record_independent_review_evidence,
    )

    root = resolve_root(path)
    eid = record_independent_review_evidence(
        root,
        change_id=change_id,
        claim_id=claim_id,
        subject=subject,
        summary=summary,
        verdict=verdict,
    )
    typer.echo(f"Recorded {eid}")
