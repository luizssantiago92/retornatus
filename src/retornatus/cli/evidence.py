"""CLI command group: evidence."""

from __future__ import annotations

from pathlib import Path

import typer

from retornatus.cli.groups import evidence_app


@evidence_app.command("add")
def evidence_add(
    change_id: str = typer.Option(..., "--change", "-c"),
    evidence_type: str = typer.Option(..., "--type", "-t"),
    subject: str = typer.Option(..., "--subject", "-s"),
    source: str = typer.Option(..., "--source"),
    producer: str = typer.Option("agent", "--producer"),
    subject_state: str | None = typer.Option(None, "--state"),
    action_id: str | None = typer.Option(None, "--action", "-a"),
    claim_id: str | None = typer.Option(
        None,
        "--claim",
        help="Claim id this Evidence SUPPORTS (required for Assurance binding).",
    ),
    git_state: bool = typer.Option(
        False,
        "--git-state",
        help="Record subject_state as commit:<HEAD> when --state is omitted.",
    ),
    path: Path | None = typer.Option(None, "--path", "-p"),
) -> None:
    """Record attributable Evidence for a Change."""
    from retornatus.application.assurance.evidence import EvidenceService

    ev = EvidenceService(path or Path.cwd()).add(
        change_id=change_id,
        evidence_type=evidence_type,
        subject=subject,
        source=source,
        producer=producer,
        subject_state=subject_state,
        supports_action_id=action_id,
        supports_claim_id=claim_id,
        capture_git=git_state,
    )
    typer.echo(f"Recorded {ev.id}")
    typer.echo(f"provenance={ev.provenance.value}")
    if ev.subject_state:
        typer.echo(f"subject_state={ev.subject_state}")


@evidence_app.command(
    "run",
    context_settings={
        "allow_extra_args": True,
        "ignore_unknown_options": True,
    },
)
def evidence_run(
    ctx: typer.Context,
    change_id: str = typer.Option(..., "--change", "-c"),
    evidence_type: str = typer.Option(..., "--type", "-t"),
    subject: str = typer.Option(..., "--subject", "-s"),
    source: str | None = typer.Option(
        None,
        "--source",
        help="Attribution string. Defaults to the executed argv.",
    ),
    producer: str = typer.Option("retornatus", "--producer"),
    subject_state: str | None = typer.Option(None, "--state"),
    action_id: str | None = typer.Option(None, "--action", "-a"),
    claim_id: str | None = typer.Option(
        None,
        "--claim",
        help="Claim id this Evidence SUPPORTS (required for Assurance binding).",
    ),
    git_state: bool = typer.Option(
        False,
        "--git-state",
        help="Record subject_state as commit:<HEAD> when --state is omitted.",
    ),
    timeout: float = typer.Option(
        120.0,
        "--timeout",
        help="Seconds before the command is killed. The process is not run via a shell.",
    ),
    path: Path | None = typer.Option(None, "--path", "-p"),
) -> None:
    """Execute a command and record the result as Evidence.

    Usage: retornatus evidence run [options] -- <command...>

    The command runs with cwd = project root and shell disabled. A non-zero
    exit or a timeout is stored as failing Evidence (provenance=executed).
    """
    from retornatus.application.assurance.evidence import EvidenceService

    argv = list(ctx.args)
    if argv and argv[0] == "--":
        argv = argv[1:]
    if not argv:
        typer.echo("Missing command. Usage: retornatus evidence run [options] -- <command...>")
        raise typer.Exit(code=2)
    try:
        ev = EvidenceService(path or Path.cwd()).run(
            change_id=change_id,
            evidence_type=evidence_type,
            subject=subject,
            command=argv,
            source=source,
            producer=producer,
            timeout_seconds=timeout,
            subject_state=subject_state,
            supports_action_id=action_id,
            supports_claim_id=claim_id,
            capture_git=git_state,
        )
    except ValueError as exc:
        typer.echo(str(exc))
        raise typer.Exit(code=2) from exc
    typer.echo(f"Recorded {ev.id}")
    typer.echo(f"provenance={ev.provenance.value} exit_code={ev.exit_code} timed_out={str(ev.timed_out).lower()}")
    if ev.git_commit:
        typer.echo(f"git_commit={ev.git_commit} dirty={ev.worktree_dirty}")
    else:
        typer.echo("git_commit=none (not a git work tree)")
    if ev.output_artifact:
        typer.echo(f"output_artifact={ev.output_artifact}")
    if ev.output_sha256:
        typer.echo(f"output_sha256={ev.output_sha256}")
    if ev.timed_out or ev.exit_code != 0:
        code = ev.exit_code
        if ev.timed_out or code is None or code < 0 or code > 255:
            code = 1
        raise typer.Exit(code=code)
