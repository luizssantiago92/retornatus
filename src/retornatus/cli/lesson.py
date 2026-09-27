"""CLI command group: lesson."""

from __future__ import annotations

from pathlib import Path

import typer

from retornatus.cli.common import resolve_root
from retornatus.cli.groups import lesson_app


@lesson_app.command("from-gate")
def lesson_from_gate(
    gate: str = typer.Option(
        ...,
        "--gate",
        "-g",
        help="contract | evidence | assurance | skill-research | policy",
    ),
    title: str = typer.Option(..., "--title", "-t"),
    note: str = typer.Option(..., "--note", "-n"),
    change_id: str | None = typer.Option(None, "--change", "-c"),
    skill_id: str | None = typer.Option(None, "--skill", "-s"),
    action_id: str | None = typer.Option(None, "--action", "-a"),
    propose_rule: bool = typer.Option(
        False,
        "--propose-rule",
        help="Also create an inactive Rule Candidate (needs Human Decision to activate).",
    ),
    no_recheck: bool = typer.Option(
        False,
        "--no-recheck",
        help="Skip re-running the gate (record note only).",
    ),
    path: Path | None = typer.Option(None, "--path", "-p"),
) -> None:
    """Record a Learning from a gate failure; optionally propose a Rule Candidate."""
    from retornatus.application.adaptation.lessons import record_lesson_from_gate

    root = resolve_root(path)
    try:
        result = record_lesson_from_gate(
            root,
            gate=gate,
            title=title,
            note=note,
            change_id=change_id,
            skill_id=skill_id,
            action_id=action_id,
            propose_rule=propose_rule,
            recheck=not no_recheck,
        )
    except ValueError as exc:
        typer.echo(str(exc))
        raise typer.Exit(1) from exc
    typer.echo(f"Recorded {result.learning.id}")
    if result.gate_passed is not None:
        typer.echo(f"Gate recheck passed: {result.gate_passed}")
    if result.gate_messages:
        for msg in result.gate_messages:
            typer.echo(f"  - {msg}")
    if result.rule_candidate:
        typer.echo(
            f"Rule Candidate {result.rule_candidate.id} (inactive — needs Decision)"
        )
