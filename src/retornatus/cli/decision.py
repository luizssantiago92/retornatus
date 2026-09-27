"""CLI command group: decision."""

from __future__ import annotations

from pathlib import Path

import typer

from retornatus.application.adaptation.service import AdaptationService
from retornatus.cli.common import resolve_root
from retornatus.cli.groups import decision_app

@decision_app.command("record")
def decision_record(
    kind: str = typer.Option(
        ...,
        "--kind",
        "-k",
        help="APPROVE_RULE_ACTIVATION | GOVERNANCE_BYPASS | CONTRACT_APPROVAL | OTHER",
    ),
    subject_id: str = typer.Option(..., "--subject", "-s"),
    summary: str = typer.Option(..., "--summary"),
    confirm: str = typer.Option(
        ...,
        "--confirm",
        help="Must equal --subject for activation/bypass decisions.",
    ),
    path: Path | None = typer.Option(None, "--path", "-p"),
) -> None:
    """Record a HUMAN Decision (local harness authority boundary)."""
    from retornatus.domain.enums import DecisionKind

    root = resolve_root(path)
    try:
        decision_kind = DecisionKind(kind)
    except ValueError as exc:
        typer.echo(f"Unknown decision kind: {kind}")
        raise typer.Exit(1) from exc
    decision = AdaptationService(root).record_human_decision(
        kind=decision_kind,
        subject_id=subject_id,
        summary=summary,
        confirmation_token=confirm,
    )
    typer.echo(f"Recorded {decision.id}")
