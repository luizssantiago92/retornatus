"""Public CLI entrypoint — intentions, not internal machinery (PRD §62)."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from retornatus import __version__
from retornatus.application.adaptation.service import AdaptationService
from retornatus.application.change.workflow import ChangeWorkflow
from retornatus.bootstrap.init import initialize_project, is_initialized
from retornatus.bootstrap.wake import wake_up
from retornatus.domain.enums import DemandKind
from retornatus.infrastructure.index.sqlite_index import RetornatusIndex
from retornatus.infrastructure.persistence.repository import FileRepository

app = typer.Typer(
    name="retornatus",
    help=(
        "Repo-native governance harness for AI-assisted software development.\n\n"
        "Govern the work. Bound the agent. Verify the outcome."
    ),
    no_args_is_help=True,
    add_completion=False,
)

change_app = typer.Typer(help="Create and inspect Changes.")
app.add_typer(change_app, name="change")


def version_callback(value: bool) -> None:
    if value:
        typer.echo(f"retornatus {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
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
    path: Optional[Path] = typer.Argument(
        None,
        help="Project root to initialize (default: current directory).",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Recreate canonical files even if already initialized.",
    ),
) -> None:
    """Initialize a minimal `.retornatus/` project in the repository."""
    result = initialize_project(path, force=force)

    if result.already_initialized and not force:
        typer.echo(f"Already initialized: {result.retornatus_dir}")
        typer.echo("Use --force to recreate canonical files.")
        raise typer.Exit(code=0)

    typer.echo(f"Initialized Retornatus at {result.retornatus_dir}")


@app.command()
def wake(
    path: Optional[Path] = typer.Option(
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
    path: Optional[Path] = typer.Option(None, "--path", "-p"),
) -> None:
    """Report derived project status."""
    root = (path or Path.cwd()).resolve()
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
    path: Optional[Path] = typer.Option(None, "--path", "-p"),
) -> None:
    """Run diagnostics on Retornatus state and environment."""
    report = wake_up(path, ensure_bridges=False, auto_init=False)
    typer.echo(report.render())
    raise typer.Exit(code=0 if report.initialized and not report.diagnostics else 1)


@app.command()
def inspect(
    entity_id: str = typer.Argument(..., help="Entity id (e.g. C-0001 or C-0001/A-001)."),
    path: Optional[Path] = typer.Option(None, "--path", "-p"),
) -> None:
    """Inspect a canonical artifact by id."""
    root = (path or Path.cwd()).resolve()
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
    if entity_id.startswith("L-"):
        meta, body, _ = repo.load_learning(entity_id)
        typer.echo(meta.model_dump_json(indent=2))
        typer.echo("---")
        typer.echo(body)
        return
    typer.echo(f"Unrecognized id: {entity_id}")
    raise typer.Exit(code=1)


@app.command()
def search(
    query: str = typer.Argument(..., help="FTS5 query."),
    path: Optional[Path] = typer.Option(None, "--path", "-p"),
) -> None:
    """Search the derived SQLite index."""
    root = (path or Path.cwd()).resolve()
    hits = RetornatusIndex(root).search(query)
    if not hits:
        typer.echo("No hits.")
        return
    for hit in hits:
        typer.echo(f"{hit['id']}\t{hit['kind']}\t{hit['title']}")


@app.command()
def verify(
    change_id: str = typer.Argument(..., help="Change id to verify against contract DONE."),
    path: Optional[Path] = typer.Option(None, "--path", "-p"),
) -> None:
    """Run Assurance against a Change's contract done criteria (evidence types)."""
    from retornatus.application.assurance.evaluate import Claim, evaluate_assurance

    root = (path or Path.cwd()).resolve()
    repo = FileRepository(root)
    contract, _ = repo.load_contract(change_id)
    evidence_dir = repo.paths.change_dir(change_id) / "evidence"
    evidence_pairs: list[tuple[str, str]] = []
    if evidence_dir.is_dir():
        for p in evidence_dir.glob("E-*.json"):
            ev, _ = repo.load_evidence(f"{change_id}/{p.stem}")
            evidence_pairs.append((ev.id, ev.type))
    claims = [
        Claim(id=f"done-{i}", statement=crit, required_evidence_types=["test_result", "human_decision"])
        for i, crit in enumerate(contract.done_criteria, start=1)
    ]
    result = evaluate_assurance(claims=claims, evidence=evidence_pairs)
    typer.echo(result.model_dump_json(indent=2))
    raise typer.Exit(code=0 if result.verdict.value == "SATISFIED" else 1)


@app.command()
def run(
    action_id: str = typer.Argument(..., help="Action id to assemble execution context for."),
    path: Optional[Path] = typer.Option(None, "--path", "-p"),
) -> None:
    """Assemble a stable ExecutionContext for an Action (does not execute agents)."""
    from retornatus.application.execution.context import assemble_execution_context

    root = (path or Path.cwd()).resolve()
    ctx = assemble_execution_context(root, action_id)
    typer.echo(ctx.model_dump_json(indent=2))


@change_app.command("create")
def change_create(
    title: str = typer.Option(..., "--title", "-t"),
    demand: str = typer.Option(..., "--demand", "-d"),
    what: str = typer.Option(..., "--what", "-w"),
    done: list[str] = typer.Option(..., "--done", help="DONE criterion (repeatable)."),
    situation: str = typer.Option("Situation pending detailed analysis.", "--situation", "-s"),
    objective: Optional[str] = typer.Option(None, "--objective", "-o"),
    kind: DemandKind = typer.Option(DemandKind.OTHER, "--kind", "-k"),
    path: Optional[Path] = typer.Option(None, "--path", "-p"),
) -> None:
    """Create a Change with Situation, Contract, and optional Action."""
    root = (path or Path.cwd()).resolve()
    if not is_initialized(root):
        initialize_project(root)
    result = ChangeWorkflow(root).create_change(
        title=title,
        demand_statement=demand,
        demand_kind=kind,
        situation=situation,
        what=what,
        done_criteria=list(done),
        action_objective=objective or what,
    )
    typer.echo(f"Created {result.change.id}")
    if result.action:
        typer.echo(f"Action {result.action.id}")


@change_app.command("learn")
def change_learn(
    title: str = typer.Option(..., "--title", "-t"),
    body: str = typer.Option(..., "--body", "-b"),
    summary: Optional[str] = typer.Option(None, "--summary"),
    path: Optional[Path] = typer.Option(None, "--path", "-p"),
) -> None:
    """Record a Learning from validated experience."""
    root = (path or Path.cwd()).resolve()
    meta = AdaptationService(root).record_learning(title=title, body=body, summary=summary)
    typer.echo(f"Recorded {meta.id}")


if __name__ == "__main__":
    app()
