"""CLI command group: policy."""

from __future__ import annotations

from pathlib import Path

import typer

from retornatus.cli.common import resolve_root
from retornatus.cli.groups import policy_app
from retornatus.infrastructure.persistence.repository import FileRepository

@policy_app.command("check")
def policy_check(
    effect: str | None = typer.Option(
        None,
        "--effect",
        "-e",
        help="Freeform governed effect to evaluate.",
    ),
    action_id: str | None = typer.Option(
        None,
        "--action",
        "-a",
        help="Evaluate Policy against an Action objective.",
    ),
    effect_type: str | None = typer.Option(
        None,
        "--effect-type",
        help="Structured effect type (for example write or exec).",
    ),
    resource: list[str] | None = typer.Option(
        None,
        "--resource",
        help="Declared path, repeatable. With --action, added to Task.resources.",
    ),
    command: list[str] | None = typer.Option(
        None,
        "--command",
        help="Command line for structured command_patterns, repeatable.",
    ),
    path: Path | None = typer.Option(None, "--path", "-p"),
) -> None:
    """Evaluate Policy (ALLOW / DENY / REQUIRE_HUMAN). Exit 0 only on ALLOW."""
    from retornatus.application.governance.policy import (
        PolicyVerdict,
        evaluate_action_policy,
        evaluate_policy,
    )
    from retornatus.domain.enums import AuthorityCategory
    from retornatus.domain.models import Authority

    root = resolve_root(path)
    if bool(effect) == bool(action_id):
        typer.echo("Provide exactly one of --effect or --action")
        raise typer.Exit(2)
    if action_id:
        decision = evaluate_action_policy(
            root,
            action_id,
            effect_type=effect_type,
            extra_paths=list(resource or []),
            extra_commands=list(command or []),
        )
    else:
        assert effect is not None
        decision = evaluate_policy(
            effect=effect,
            rules=FileRepository(root).list_rules(),
            authority=Authority(category=AuthorityCategory.DELEGATED, rationale="cli"),
            paths=list(resource or []),
            commands=list(command or []),
            effect_type=effect_type,
        )
    typer.echo(f"verdict={decision.verdict.value}")
    typer.echo(decision.rationale)
    if decision.matched_rule_ids:
        typer.echo("matched_rules: " + ", ".join(decision.matched_rule_ids))
    for warning in decision.warnings:
        typer.echo(f"WARN {warning}")
    raise typer.Exit(code=0 if decision.verdict is PolicyVerdict.ALLOW else 1)
