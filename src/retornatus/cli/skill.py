"""CLI command group: skill."""

from __future__ import annotations

from pathlib import Path

import typer

from retornatus.application.adaptation.skills import SkillService
from retornatus.bootstrap.init import initialize_project, is_initialized
from retornatus.cli.common import resolve_root
from retornatus.cli.groups import skill_app
from retornatus.infrastructure.persistence.repository import FileRepository


@skill_app.command("create")
def skill_create(
    specialization: str = typer.Option(
        ...,
        "--need",
        "-n",
        help="Specialization the agent must research and encode.",
    ),
    title: str | None = typer.Option(None, "--title", "-t"),
    action_id: str | None = typer.Option(None, "--action", "-a"),
    change_id: str | None = typer.Option(None, "--change", "-c"),
    research_seed: str | None = typer.Option(
        None,
        "--research-seed",
        help="Hints for where/how the agent should research.",
    ),
    activate: bool = typer.Option(False, "--activate", help="Mark ACTIVE immediately."),
    path: Path | None = typer.Option(None, "--path", "-p"),
) -> None:
    """Create one specialization Skill (agent fills RESEARCH via web tools)."""
    root = resolve_root(path)
    if not is_initialized(root):
        initialize_project(root)
    if action_id and not change_id and "/" in action_id:
        change_id = action_id.split("/", 1)[0]
    skill, _ = SkillService(root).create_for_specialization(
        specialization=specialization,
        title=title,
        change_id=change_id,
        action_id=action_id,
        research_seed=research_seed,
        activate=activate,
    )
    typer.echo(f"Created {skill.id} ({skill.status.value}) at .retornatus/adaptation/skills/{skill.id}/SKILL.md")
    typer.echo("Agent next step: research current sources and fill RESEARCH + PROCEDURE.")


@skill_app.command("list")
def skill_list(path: Path | None = typer.Option(None, "--path", "-p")) -> None:
    """List project Skills."""
    root = resolve_root(path)
    skills = FileRepository(root).list_skills()
    if not skills:
        typer.echo("No skills.")
        return
    for skill in skills:
        typer.echo(f"{skill.id}\tv{skill.version}\t{skill.status.value}\t{skill.title}")


@skill_app.command("need")
def skill_need(
    action_id: str | None = typer.Option(
        None,
        "--action",
        "-a",
        help="Action id (optional when using --prompt / --demand).",
    ),
    prompt: str | None = typer.Option(
        None,
        "--prompt",
        help="Freeform user request — assess Skill need before an Action exists.",
    ),
    demand: str | None = typer.Option(
        None,
        "--demand",
        "-d",
        help="Demand text for early Skill need (with optional --what).",
    ),
    what: str | None = typer.Option(
        None,
        "--what",
        "-w",
        help="Proposed WHAT (pairs with --demand or alone as prompt text).",
    ),
    path: Path | None = typer.Option(None, "--path", "-p"),
) -> None:
    """Assess whether an on-demand Skill is required (complexity-sensitive).

    Action is optional: use --prompt / --demand when the need appears in chat
    before Contract/Action.
    """
    from retornatus.application.adaptation.skill_need import assess_skill_need

    root = resolve_root(path)
    if not action_id and not prompt and not demand and not what:
        typer.echo("Provide --action or --prompt/--demand/--what")
        raise typer.Exit(2)
    try:
        assessment = assess_skill_need(
            root,
            action_id,
            prompt=prompt,
            demand=demand,
            what=what,
        )
    except ValueError as exc:
        typer.echo(str(exc))
        raise typer.Exit(2) from exc
    typer.echo(f"required={assessment.required}")
    typer.echo(f"source={assessment.source}")
    typer.echo(assessment.rationale)
    if assessment.suggested_need:
        typer.echo(f"suggested_need={assessment.suggested_need}")
    raise typer.Exit(code=0 if not assessment.required else 2)


@skill_app.command("activate")
def skill_activate(
    skill_id: str = typer.Argument(...),
    path: Path | None = typer.Option(None, "--path", "-p"),
    force: bool = typer.Option(False, "--force", help="Governed bypass of research gate."),
    reason: str | None = typer.Option(
        None,
        "--reason",
        help="Required with --force: why the gate is bypassed.",
    ),
) -> None:
    """Mark a Skill ACTIVE for Execution consumption."""
    root = path or Path.cwd()
    try:
        skill = SkillService(root).activate(
            skill_id,
            force=force,
            bypass_reason=reason,
        )
    except Exception as exc:  # noqa: BLE001 — surface governance errors
        typer.echo(str(exc))
        raise typer.Exit(1) from exc
    typer.echo(f"Activated {skill.id}")
    if force:
        typer.echo("Governed bypass recorded for skill-research gate.")


@skill_app.command("evolve")
def skill_evolve(
    skill_id: str = typer.Argument(...),
    note: str = typer.Option(..., "--note", "-n"),
    learning_id: str | None = typer.Option(None, "--from-learning", "-l"),
    append: str | None = typer.Option(None, "--append", help="Extra procedure text."),
    path: Path | None = typer.Option(None, "--path", "-p"),
) -> None:
    """Evolve a Skill from validated experience (Adaptation)."""
    skill = SkillService(path or Path.cwd()).evolve(
        skill_id,
        note=note,
        from_learning_id=learning_id,
        body_append=append,
    )
    typer.echo(f"Evolved {skill.id} to v{skill.version}")


@skill_app.command("export")
def skill_export(
    skill_id: str = typer.Argument(...),
    target: str = typer.Option("cursor", "--target"),
    path: Path | None = typer.Option(None, "--path", "-p"),
) -> None:
    """Export Skill to a native environment skill surface (e.g. .cursor/skills/)."""
    dest = SkillService(path or Path.cwd()).export_native(skill_id, target=target)
    typer.echo(f"Exported to {dest}")


@skill_app.command("candidates")
def skill_candidates(path: Path | None = typer.Option(None, "--path", "-p")) -> None:
    """List skill candidates. An empty list is a normal result.

    Candidates are suggestions. This command does not create a Skill.
    """
    from retornatus.application.adaptation.skill_candidates import format_candidates, list_candidates

    root = resolve_root(path)
    typer.echo(format_candidates(list_candidates(root)))


@skill_app.command("accept")
def skill_accept(
    candidate_id: str = typer.Argument(..., help="Candidate id, for example K-0001."),
    path: Path | None = typer.Option(None, "--path", "-p"),
) -> None:
    """Approve a pending candidate and write a draft Skill, or evolve an existing one.

    This is the only command that creates a Skill from a candidate.
    """
    from retornatus.application.adaptation.skill_candidates import accept_candidate

    root = resolve_root(path)
    try:
        result = accept_candidate(root, candidate_id)
    except ValueError as exc:
        typer.echo(str(exc))
        raise typer.Exit(1) from exc
    typer.echo(f"Accepted {result.candidate_id}")
    if result.action == "evolved":
        typer.echo(f"Evolved {result.skill_id} to v{result.skill_version} ({result.skill_status})")
        return
    typer.echo(
        f"Created {result.skill_id} ({result.skill_status}) at .retornatus/adaptation/skills/{result.skill_id}/SKILL.md"
    )


@skill_app.command("reject")
def skill_reject(
    candidate_id: str = typer.Argument(..., help="Candidate id, for example K-0001."),
    path: Path | None = typer.Option(None, "--path", "-p"),
) -> None:
    """Reject a pending candidate. The same theme waits for new occurrences."""
    from retornatus.application.adaptation.skill_candidates import reject_candidate

    root = resolve_root(path)
    try:
        result = reject_candidate(root, candidate_id)
    except ValueError as exc:
        typer.echo(str(exc))
        raise typer.Exit(1) from exc
    typer.echo(f"Rejected {result.id}")
