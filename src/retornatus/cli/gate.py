"""CLI command group: gate."""

from __future__ import annotations

from pathlib import Path

import typer

from retornatus.cli.groups import gate_app

@gate_app.command("policy")
def gate_policy_cmd(
    action_id: str = typer.Argument(..., help="Action id to evaluate Policy against."),
    path: Path | None = typer.Option(None, "--path", "-p"),
) -> None:
    """Gate: Policy ALLOW for Action objective (exit 1 = STOP)."""
    from retornatus.application.governance.gates import gate_policy

    result = gate_policy(path or Path.cwd(), action_id)
    for msg in result.messages:
        typer.echo(msg)
    raise typer.Exit(result.exit_code)


@gate_app.command("contract")
def gate_contract_cmd(
    change_id: str = typer.Argument(...),
    path: Path | None = typer.Option(None, "--path", "-p"),
) -> None:
    """Gate: active Contract with WHAT + DONE (exit 1 = STOP)."""
    from retornatus.application.governance.gates import gate_contract

    result = gate_contract(path or Path.cwd(), change_id)
    for msg in result.messages:
        typer.echo(msg)
    raise typer.Exit(result.exit_code)


@gate_app.command("evidence")
def gate_evidence_cmd(
    change_id: str = typer.Argument(...),
    path: Path | None = typer.Option(None, "--path", "-p"),
) -> None:
    """Gate: Evidence artifacts exist (exit 1 = STOP)."""
    from retornatus.application.governance.gates import gate_evidence

    result = gate_evidence(path or Path.cwd(), change_id)
    for msg in result.messages:
        typer.echo(msg)
    raise typer.Exit(result.exit_code)


@gate_app.command("skill-research")
def gate_skill_research_cmd(
    skill_id: str = typer.Argument(...),
    path: Path | None = typer.Option(None, "--path", "-p"),
) -> None:
    """Gate: Skill RESEARCH filled with sources (exit 1 = STOP)."""
    from retornatus.application.governance.gates import gate_skill_research

    result = gate_skill_research(path or Path.cwd(), skill_id)
    for msg in result.messages:
        typer.echo(msg)
    raise typer.Exit(result.exit_code)


@gate_app.command("assurance")
def gate_assurance_cmd(
    change_id: str = typer.Argument(...),
    path: Path | None = typer.Option(None, "--path", "-p"),
) -> None:
    """Gate: Assurance SATISFIED (exit 1 = STOP)."""
    from retornatus.application.governance.gates import gate_assurance

    result = gate_assurance(path or Path.cwd(), change_id)
    for msg in result.messages:
        typer.echo(msg)
    raise typer.Exit(result.exit_code)


@gate_app.command("budget")
def gate_budget_cmd(
    action_id: str = typer.Argument(...),
    path: Path | None = typer.Option(None, "--path", "-p"),
) -> None:
    """Gate: Action attempt budget not exhausted (exit 1 = STOP)."""
    from retornatus.application.governance.gates import gate_budget

    result = gate_budget(path or Path.cwd(), action_id)
    for msg in result.messages:
        typer.echo(msg)
    raise typer.Exit(result.exit_code)
