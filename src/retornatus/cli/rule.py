"""CLI command group: rule."""

from __future__ import annotations

from pathlib import Path

import typer

from retornatus.application.adaptation.service import AdaptationService
from retornatus.cli.common import resolve_root
from retornatus.cli.groups import rule_app

@rule_app.command("propose")
def rule_propose(
    statement: str = typer.Option(..., "--statement", "-s"),
    applicability: str = typer.Option(..., "--applicability", "-a"),
    learning_id: str | None = typer.Option(None, "--from-learning", "-l"),
    path: Path | None = typer.Option(None, "--path", "-p"),
) -> None:
    """Propose a Rule Candidate (never auto-activates)."""
    root = resolve_root(path)
    candidate = AdaptationService(root).propose_rule_candidate(
        statement=statement,
        applicability=applicability,
        from_learning_id=learning_id,
    )
    typer.echo(f"Proposed candidate {candidate.id} (active={candidate.active})")


@rule_app.command("activate")
def rule_activate(
    rule_id: str = typer.Argument(...),
    decision_id: str = typer.Option(
        ...,
        "--decision",
        "-d",
        help="Human Decision id approving activation.",
    ),
    path: Path | None = typer.Option(None, "--path", "-p"),
) -> None:
    """Activate a Rule Candidate via HUMAN Decision boundary."""
    from retornatus.application.adaptation.service import HumanAuthorityError

    root = resolve_root(path)
    try:
        rule = AdaptationService(root).activate_rule(
            rule_id, human_decision_id=decision_id
        )
    except HumanAuthorityError as exc:
        typer.echo(str(exc))
        raise typer.Exit(1) from exc
    typer.echo(f"Activated {rule.id}")
