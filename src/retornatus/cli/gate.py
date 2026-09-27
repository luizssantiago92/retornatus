"""CLI command group: gate."""

from __future__ import annotations

from pathlib import Path

import typer

from retornatus.cli.common import resolve_root
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


@gate_app.command("suppressions")
def gate_suppressions_cmd(
    path: Path | None = typer.Option(None, "--path", "-p"),
    staged: bool = typer.Option(
        False,
        "--staged",
        help="Scan the index (staged diff) instead of HEAD plus unstaged edits.",
    ),
    base: str | None = typer.Option(
        None,
        "--base",
        help="Scan added lines in git diff base...HEAD.",
    ),
) -> None:
    """Gate: added diff lines must not introduce suppression markers (exit 1 = STOP)."""
    from retornatus.application.governance.gates import gate_suppressions

    result = gate_suppressions(resolve_root(path), base=base, staged=staged)
    for msg in result.messages:
        typer.echo(msg)
    raise typer.Exit(result.exit_code)


@gate_app.command("scope")
def gate_scope_cmd(
    change_id: str = typer.Argument(...),
    path: Path | None = typer.Option(None, "--path", "-p"),
    base: str | None = typer.Option(
        None,
        "--base",
        help="Compare git diff --name-only base...HEAD with Task.resources.",
    ),
    staged: bool = typer.Option(
        False,
        "--staged",
        help="Compare the index only. Without --base or --staged, staged and unstaged changes are used.",
    ),
) -> None:
    """Gate: diff stays inside Task.resources and .retornatus (exit 1 = STOP)."""
    from retornatus.application.governance.gates import gate_scope

    result = gate_scope(resolve_root(path), change_id, base=base, staged=staged)
    for msg in result.messages:
        typer.echo(msg)
    raise typer.Exit(result.exit_code)
