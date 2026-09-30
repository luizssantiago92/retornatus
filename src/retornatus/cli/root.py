"""CLI command group: root."""

from __future__ import annotations

from pathlib import Path

import typer

from retornatus import __version__
from retornatus.application.change.workflow import ChangeWorkflow
from retornatus.bootstrap.gitignore import tracked_private_key_warnings
from retornatus.bootstrap.init import initialize_project, is_initialized
from retornatus.bootstrap.presets import list_presets
from retornatus.bootstrap.wake import wake_up
from retornatus.cli.common import resolve_root
from retornatus.cli.groups import app
from retornatus.cli.json_output import JSON_OUTPUT_HELP
from retornatus.infrastructure.index.sqlite_index import RetornatusIndex
from retornatus.infrastructure.persistence.repository import FileRepository


def version_callback(value: bool) -> None:
    if value:
        typer.echo(f"retornatus {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool | None = typer.Option(
        None,
        "--version",
        "-V",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """Retornatus CLI."""


@app.command()
def init(
    path: Path | None = typer.Argument(
        None,
        help="Project root to initialize (default: current directory).",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Recreate canonical files even if already initialized.",
    ),
    preset: str | None = typer.Option(
        None,
        "--preset",
        help="Write a packaged config preset into .retornatus/config.toml.",
    ),
    list_presets_flag: bool = typer.Option(
        False,
        "--list-presets",
        help="List packaged presets and exit without writing files.",
    ),
    force_config: bool = typer.Option(
        False,
        "--force-config",
        help="Overwrite an existing config.toml when --preset is set.",
    ),
) -> None:
    """Initialize a minimal `.retornatus/` project and append ignore rules."""
    if list_presets_flag:
        for name, summary in list_presets():
            typer.echo(f"{name}: {summary}")
        raise typer.Exit()

    result = initialize_project(
        path,
        force=force,
        preset=preset,
        force_config=force_config,
    )
    for line in tracked_private_key_warnings(result.tracked_private_keys):
        typer.echo(line, err=True)
    if result.gitignore_updated:
        typer.echo(
            "Gitignore: appended Retornatus ignore rules to "
            f"{result.root / '.gitignore'}"
        )

    if result.config_preserved:
        typer.echo(
            ".retornatus/config.toml already exists. "
            f"Pass --force-config to overwrite it with preset {result.preset!r}.",
            err=True,
        )
        raise typer.Exit(code=1)

    if result.config_written and result.preset:
        typer.echo(
            f"Wrote preset {result.preset!r} to {result.retornatus_dir / 'config.toml'}"
        )

    if result.created:
        typer.echo(f"Initialized Retornatus at {result.retornatus_dir}")
        return

    if not result.config_written:
        typer.echo(f"Already initialized: {result.retornatus_dir}")
        typer.echo("Use --force to recreate canonical files.")
        raise typer.Exit(code=0)


@app.command()
def wake(
    path: Path | None = typer.Option(
        None,
        "--path",
        "-p",
        help="Project root (default: current directory).",
    ),
    bridges: bool = typer.Option(
        False,
        "--bridges",
        help="Write environment bridge files when a native adapter is detected.",
    ),
) -> None:
    """Reconstruct project continuity from repository-native state."""
    report = wake_up(path, ensure_bridges=bridges, auto_init=True)
    typer.echo(report.render())


@app.command()
def status(
    path: Path | None = typer.Option(None, "--path", "-p"),
) -> None:
    """Report derived project status."""
    root = resolve_root(path)
    if not is_initialized(root):
        typer.echo("Not initialized. Run: retornatus init")
        raise typer.Exit(code=1)
    wf = ChangeWorkflow(root)
    ids = FileRepository(root).list_change_ids()
    if not ids:
        typer.echo("No changes.")
        raise typer.Exit(code=0)
    for cid in ids:
        typer.echo(wf.derived_status(cid))


@app.command()
def doctor(
    path: Path | None = typer.Option(None, "--path", "-p"),
) -> None:
    """Run diagnostics on Retornatus state and environment."""
    from retornatus.bootstrap.doctor import run_doctor

    report = run_doctor(path)
    typer.echo(report.render())
    raise typer.Exit(code=0 if report.ok else 1)


@app.command()
def inspect(
    entity_id: str = typer.Argument(..., help="Entity id (e.g. C-0001 or C-0001/A-001)."),
    path: Path | None = typer.Option(None, "--path", "-p"),
) -> None:
    """Inspect a canonical artifact by id."""
    root = resolve_root(path)
    repo = FileRepository(root)
    if entity_id.startswith("C-") and "/" not in entity_id:
        change, _ = repo.load_change(entity_id)
        typer.echo(change.model_dump_json(indent=2))
        return
    if "/A-" in entity_id:
        action, _ = repo.load_action(entity_id)
        typer.echo(action.model_dump_json(indent=2))
        return
    if "/F-" in entity_id:
        finding, _ = repo.load_finding(entity_id)
        typer.echo(finding.model_dump_json(indent=2))
        return
    if "/Q-" in entity_id:
        question, _ = repo.load_question(entity_id)
        typer.echo(question.model_dump_json(indent=2))
        return
    if "/E-" in entity_id:
        evidence, _ = repo.load_evidence(entity_id)
        typer.echo(evidence.model_dump_json(indent=2))
        return
    if entity_id.startswith("R-"):
        rule, _ = repo.load_rule(entity_id)
        typer.echo(rule.model_dump_json(indent=2))
        return
    if entity_id.startswith("S-"):
        skill_meta, skill_body, _ = repo.load_skill(entity_id)
        typer.echo(skill_meta.model_dump_json(indent=2))
        typer.echo("---")
        typer.echo(skill_body)
        return
    if entity_id.startswith("L-"):
        learning_meta, learning_body, _ = repo.load_learning(entity_id)
        typer.echo(learning_meta.model_dump_json(indent=2))
        typer.echo("---")
        typer.echo(learning_body)
        return
    typer.echo(f"Unrecognized id: {entity_id}")
    raise typer.Exit(code=1)


@app.command()
def search(
    query: str = typer.Argument(..., help="FTS5 query."),
    path: Path | None = typer.Option(None, "--path", "-p"),
) -> None:
    """Search the derived SQLite index."""
    root = resolve_root(path)
    hits = RetornatusIndex(root).search(query)
    if not hits:
        typer.echo("No hits.")
        return
    for hit in hits:
        typer.echo(f"{hit['id']}\t{hit['kind']}\t{hit['title']}")


@app.command()
def verify(
    change_id: str = typer.Argument(..., help="Change id to verify against contract DONE."),
    path: Path | None = typer.Option(None, "--path", "-p"),
    no_git: bool = typer.Option(
        False,
        "--no-git",
        help="Do not derive subject freshness from git HEAD.",
    ),
    receipt: bool = typer.Option(
        False,
        "--receipt",
        help="Write an Ed25519 receipt under .retornatus/assurance/receipts/.",
    ),
    allow_self_reported: bool = typer.Option(
        False,
        "--allow-self-reported",
        help=(
            "Count self-reported test/build/lint evidence as satisfying. "
            "Migration opt-out; also enabled by [assurance] allow_self_reported "
            "in config.toml. Does not bypass [assurance] required_checks."
        ),
    ),
    run_checks: bool = typer.Option(
        False,
        "--run-checks",
        help=(
            "Execute [assurance] required_checks and record Evidence before "
            "evaluating. Same capture path as evidence run."
        ),
    ),
    check_timeout: float = typer.Option(
        120.0,
        "--check-timeout",
        help="Seconds before each required check is killed when --run-checks is set.",
    ),
    as_json: bool = typer.Option(False, "--json", help=JSON_OUTPUT_HELP),
) -> None:
    """Run Assurance against a Change's contract DONE Claims (bound Evidence)."""
    from retornatus.application.assurance.independent import evaluate_change_assurance
    from retornatus.application.assurance.receipt import (
        load_signing_key,
        write_verify_receipt,
    )
    from retornatus.application.assurance.settings import allow_self_reported_enabled
    from retornatus.application.report.envelope import verify_document
    from retornatus.cli.json_output import write_json

    root = resolve_root(path)
    if receipt:
        # Fail before evaluation so a bad key is a usage error, not a traceback.
        # The key is not written to disk here.
        load_signing_key(root)
    if run_checks:
        from retornatus.application.assurance.checks import run_required_checks

        outcome = run_required_checks(
            root, change_id, timeout_seconds=check_timeout
        )
        for note in outcome.notes:
            typer.echo(f"WARN {note}", err=as_json)
        for evidence in outcome.evidence:
            typer.echo(
                f"Recorded {evidence.id} argv={' '.join(evidence.command or [])} "
                f"exit_code={evidence.exit_code}",
                err=as_json,
            )
    allowed = allow_self_reported or allow_self_reported_enabled(root)
    result = evaluate_change_assurance(
        root,
        change_id,
        use_git_state=not no_git,
        allow_self_reported=allowed,
    )
    receipt_path: str | None = None
    if receipt:
        receipt_path = str(write_verify_receipt(root, change_id, result))
    if as_json:
        for label in result.evidence_labels:
            typer.echo(label, err=True)
        for surface in result.surfaces:
            typer.echo(
                f"surface {surface.get('name')}: {surface.get('status')}",
                err=True,
            )
        for warning in result.warnings:
            typer.echo(f"WARN {warning}", err=True)
        if receipt_path:
            typer.echo(f"receipt: {receipt_path}", err=True)
        write_json(verify_document(root, change_id, result, receipt_path=receipt_path))
    else:
        for label in result.evidence_labels:
            typer.echo(label)
        for surface in result.surfaces:
            typer.echo(f"surface {surface.get('name')}: {surface.get('status')}")
        for warning in result.warnings:
            typer.echo(f"WARN {warning}")
        typer.echo(result.model_dump_json(indent=2))
        if receipt_path:
            typer.echo(f"receipt: {receipt_path}")
    raise typer.Exit(code=0 if result.verdict.value == "SATISFIED" else 1)


@app.command()
def run(
    action_id: str = typer.Argument(..., help="Action id to assemble execution context for."),
    path: Path | None = typer.Option(None, "--path", "-p"),
    assurance: bool = typer.Option(
        False,
        "--assurance",
        help="Assemble a fresh independent Assurance ExecutionContext.",
    ),
    strict_policy: bool = typer.Option(
        False,
        "--strict-policy",
        help="Exit non-zero when Policy is DENY or REQUIRE_HUMAN.",
    ),
) -> None:
    """Assemble a stable ExecutionContext for an Action (does not execute agents)."""
    from retornatus.application.execution.context import (
        assemble_assurance_context,
        assemble_execution_context,
    )
    from retornatus.application.governance.policy import PolicyVerdict

    root = resolve_root(path)
    ctx = (
        assemble_assurance_context(root, action_id)
        if assurance
        else assemble_execution_context(root, action_id)
    )
    typer.echo(ctx.model_dump_json(indent=2))
    if strict_policy and ctx.policy_verdict in {
        PolicyVerdict.DENY.value,
        PolicyVerdict.REQUIRE_HUMAN.value,
    }:
        raise typer.Exit(1)


@app.command("project-init")
def project_init_cmd(
    path: Path | None = typer.Option(None, "--path", "-p"),
) -> None:
    """Map repository into `.retornatus/project/project.md` continuity notes."""
    from retornatus.bootstrap.project_init import project_init

    dest = project_init(path or Path.cwd())
    typer.echo(f"Wrote {dest}")


@app.command("integrate")
def integrate_cmd(
    path: Path | None = typer.Option(None, "--path", "-p"),
) -> None:
    """Install Retornatus hub skill + Environment bridge for the detected host."""
    from retornatus.infrastructure.environment.adapters import detect_environment
    from retornatus.infrastructure.environment.hub_skill import install_hub_skill

    root = resolve_root(path)
    if not is_initialized(root):
        initialize_project(root)
    adapter, caps = detect_environment(root)
    bridges = adapter.ensure_bridge_files(root)
    hub = install_hub_skill(root)
    typer.echo(f"environment: {adapter.kind.value}")
    typer.echo(
        f"capabilities: native_rules={caps.native_rules} "
        f"native_skills={caps.native_skills} native_sandbox={caps.native_sandbox}"
    )
    seen: set[str] = set()
    for b in [*bridges, hub]:
        key = str(b)
        if key in seen:
            continue
        seen.add(key)
        label = "Hub skill" if b == hub or "skills/retornatus" in key else "Bridge"
        typer.echo(f"{label}: {b}")
