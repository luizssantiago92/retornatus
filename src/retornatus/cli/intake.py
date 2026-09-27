"""CLI command group: intake."""

from __future__ import annotations

from pathlib import Path

import typer

from retornatus.bootstrap.init import initialize_project, is_initialized
from retornatus.cli.common import resolve_root
from retornatus.cli.groups import intake_app


@intake_app.command("analyze")
def intake_analyze(
    prompt: str = typer.Option(
        ...,
        "--prompt",
        "-p",
        help="Freeform user request to analyze before Skill/Contract work.",
    ),
    answer: list[str] | None = typer.Option(
        None,
        "--answer",
        help="Human answer TOPIC=text (repeatable). Example: CREATE=yes — create DRAFT now",
    ),
    create_skill: bool = typer.Option(
        False,
        "--create-skill",
        help="Create DRAFT Skill only when intake authorized CREATE=yes.",
    ),
    change_id: str | None = typer.Option(None, "--change", "-c"),
    action_id: str | None = typer.Option(None, "--action", "-a"),
    path: Path | None = typer.Option(None, "--path"),
) -> None:
    """Analyze a chat prompt through intake stages; propose Skill with human control.

    Two worlds: manual ``skill create``, or this analyzed path (propose → ask → create).
    """
    from retornatus.application.adaptation.intake import (
        IntakeVerdict,
        analyze_prompt_intake,
        create_skill_from_intake,
    )

    root = resolve_root(path)
    if not is_initialized(root):
        initialize_project(root)

    answers: dict[str, str] = {}
    for item in answer or []:
        if "=" not in item:
            typer.echo(f"Invalid --answer {item!r}; expected TOPIC=text")
            raise typer.Exit(2)
        topic, text = item.split("=", 1)
        answers[topic.strip()] = text.strip()

    try:
        analysis = analyze_prompt_intake(root, prompt, answers=answers or None)
    except ValueError as exc:
        typer.echo(str(exc))
        raise typer.Exit(2) from exc

    typer.echo(analysis.to_markdown())
    typer.echo(f"verdict={analysis.verdict.value}")
    typer.echo(f"create_authorized={analysis.create_authorized}")

    if create_skill:
        try:
            skill = create_skill_from_intake(
                root,
                analysis,
                change_id=change_id,
                action_id=action_id,
            )
        except ValueError as exc:
            typer.echo(str(exc))
            raise typer.Exit(1) from exc
        typer.echo(
            f"Created {skill.id} ({skill.status.value}) — research RESEARCH + PROCEDURE next"
        )
        raise typer.Exit(0)

    # Exit codes: 0 routine/reuse/authorized; 2 propose (questions remain); 1 error
    if analysis.verdict is IntakeVerdict.PROPOSE_SKILL and analysis.focused_questions:
        raise typer.Exit(2)
    if analysis.verdict is IntakeVerdict.CREATE_SKILL and analysis.create_authorized:
        typer.echo("Hint: re-run with --create-skill to write the DRAFT Skill.")
        raise typer.Exit(0)
    raise typer.Exit(0)
