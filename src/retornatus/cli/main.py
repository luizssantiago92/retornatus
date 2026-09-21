"""Public CLI entrypoint — intentions, not internal machinery (PRD §62)."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from retornatus import __version__
from retornatus.application.adaptation.service import AdaptationService
from retornatus.application.adaptation.skills import SkillService
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
skill_app = typer.Typer(help="Specialization Skills — create, evolve, export.")
gate_app = typer.Typer(help="Mechanical gates (non-zero exit = STOP).")
evidence_app = typer.Typer(help="Attributable Evidence.")
finding_app = typer.Typer(help="Findings.")
question_app = typer.Typer(help="Questions grounded in Findings.")
loop_app = typer.Typer(help="Next ready unit of work (projection).")
app.add_typer(change_app, name="change")
app.add_typer(skill_app, name="skill")
app.add_typer(gate_app, name="gate")
app.add_typer(evidence_app, name="evidence")
app.add_typer(finding_app, name="finding")
app.add_typer(question_app, name="question")
app.add_typer(loop_app, name="loop")


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
    if entity_id.startswith("S-"):
        meta, body, _ = repo.load_skill(entity_id)
        typer.echo(meta.model_dump_json(indent=2))
        typer.echo("---")
        typer.echo(body)
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


@skill_app.command("create")
def skill_create(
    specialization: str = typer.Option(
        ...,
        "--need",
        "-n",
        help="Specialization the agent must research and encode.",
    ),
    title: Optional[str] = typer.Option(None, "--title", "-t"),
    action_id: Optional[str] = typer.Option(None, "--action", "-a"),
    change_id: Optional[str] = typer.Option(None, "--change", "-c"),
    research_seed: Optional[str] = typer.Option(
        None,
        "--research-seed",
        help="Hints for where/how the agent should research.",
    ),
    activate: bool = typer.Option(False, "--activate", help="Mark ACTIVE immediately."),
    path: Optional[Path] = typer.Option(None, "--path", "-p"),
) -> None:
    """Create one specialization Skill (agent fills RESEARCH via web tools)."""
    root = (path or Path.cwd()).resolve()
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
def skill_list(path: Optional[Path] = typer.Option(None, "--path", "-p")) -> None:
    """List project Skills."""
    root = (path or Path.cwd()).resolve()
    skills = FileRepository(root).list_skills()
    if not skills:
        typer.echo("No skills.")
        return
    for skill in skills:
        typer.echo(
            f"{skill.id}\tv{skill.version}\t{skill.status.value}\t{skill.title}"
        )


@skill_app.command("activate")
def skill_activate(
    skill_id: str = typer.Argument(...),
    path: Optional[Path] = typer.Option(None, "--path", "-p"),
    force: bool = typer.Option(False, "--force", help="Skip research gate."),
) -> None:
    """Mark a Skill ACTIVE for Execution consumption."""
    root = path or Path.cwd()
    if not force:
        from retornatus.application.governance.gates import gate_skill_research

        result = gate_skill_research(root, skill_id)
        if not result.passed:
            for msg in result.messages:
                typer.echo(msg)
            typer.echo("Fill RESEARCH (with URLs) before activate, or pass --force.")
            raise typer.Exit(1)
    skill = SkillService(root).activate(skill_id)
    typer.echo(f"Activated {skill.id}")


@skill_app.command("evolve")
def skill_evolve(
    skill_id: str = typer.Argument(...),
    note: str = typer.Option(..., "--note", "-n"),
    learning_id: Optional[str] = typer.Option(None, "--from-learning", "-l"),
    append: Optional[str] = typer.Option(None, "--append", help="Extra procedure text."),
    path: Optional[Path] = typer.Option(None, "--path", "-p"),
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
    path: Optional[Path] = typer.Option(None, "--path", "-p"),
) -> None:
    """Export Skill to a native environment skill surface (e.g. .cursor/skills/)."""
    dest = SkillService(path or Path.cwd()).export_native(skill_id, target=target)
    typer.echo(f"Exported to {dest}")


@app.command("project-init")
def project_init_cmd(
    path: Optional[Path] = typer.Option(None, "--path", "-p"),
) -> None:
    """Map repository into `.retornatus/project/project.md` continuity notes."""
    from retornatus.bootstrap.project_init import project_init

    dest = project_init(path or Path.cwd())
    typer.echo(f"Wrote {dest}")


@app.command("integrate")
def integrate_cmd(
    path: Optional[Path] = typer.Option(None, "--path", "-p"),
) -> None:
    """Install Retornatus hub skill + Cursor bridge into the project."""
    from retornatus.infrastructure.environment.hub_skill import install_hub_skill
    from retornatus.infrastructure.environment.adapters import CursorAdapter

    root = (path or Path.cwd()).resolve()
    if not is_initialized(root):
        initialize_project(root)
    hub = install_hub_skill(root)
    bridges = CursorAdapter().ensure_bridge_files(root)
    typer.echo(f"Hub skill: {hub}")
    for b in bridges:
        typer.echo(f"Bridge: {b}")


@gate_app.command("contract")
def gate_contract_cmd(
    change_id: str = typer.Argument(...),
    path: Optional[Path] = typer.Option(None, "--path", "-p"),
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
    path: Optional[Path] = typer.Option(None, "--path", "-p"),
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
    path: Optional[Path] = typer.Option(None, "--path", "-p"),
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
    path: Optional[Path] = typer.Option(None, "--path", "-p"),
) -> None:
    """Gate: Assurance SATISFIED (exit 1 = STOP)."""
    from retornatus.application.governance.gates import gate_assurance

    result = gate_assurance(path or Path.cwd(), change_id)
    for msg in result.messages:
        typer.echo(msg)
    raise typer.Exit(result.exit_code)


@evidence_app.command("add")
def evidence_add(
    change_id: str = typer.Option(..., "--change", "-c"),
    evidence_type: str = typer.Option(..., "--type", "-t"),
    subject: str = typer.Option(..., "--subject", "-s"),
    source: str = typer.Option(..., "--source"),
    producer: str = typer.Option("agent", "--producer"),
    subject_state: Optional[str] = typer.Option(None, "--state"),
    action_id: Optional[str] = typer.Option(None, "--action", "-a"),
    path: Optional[Path] = typer.Option(None, "--path", "-p"),
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
    )
    typer.echo(f"Recorded {ev.id}")


@finding_app.command("add")
def finding_add(
    change_id: str = typer.Option(..., "--change", "-c"),
    observation: str = typer.Option(..., "--observation", "-o"),
    source: Optional[str] = typer.Option(None, "--source"),
    number: int = typer.Option(1, "--number"),
    path: Optional[Path] = typer.Option(None, "--path", "-p"),
) -> None:
    """Record a Finding (relevant observation)."""
    from retornatus.application.question.loop import QuestionLoop

    finding = QuestionLoop(path or Path.cwd()).record_finding(
        change_id=change_id,
        observation=observation,
        number=number,
        source=source,
    )
    typer.echo(f"Recorded {finding.id}")


@question_app.command("open")
def question_open(
    change_id: str = typer.Option(..., "--change", "-c"),
    statement: str = typer.Option(..., "--statement", "-s"),
    finding: list[str] = typer.Option(..., "--finding", "-f"),
    number: int = typer.Option(1, "--number"),
    path: Optional[Path] = typer.Option(None, "--path", "-p"),
) -> None:
    """Open a Question grounded in one or more Findings."""
    from retornatus.application.question.loop import QuestionLoop

    q = QuestionLoop(path or Path.cwd()).open_question(
        change_id=change_id,
        statement=statement,
        finding_ids=list(finding),
        number=number,
    )
    typer.echo(f"Opened {q.id}")


@question_app.command("resolve")
def question_resolve(
    question_id: str = typer.Argument(...),
    summary: str = typer.Option(..., "--summary", "-s"),
    evidence: Optional[list[str]] = typer.Option(None, "--evidence", "-e"),
    path: Optional[Path] = typer.Option(None, "--path", "-p"),
) -> None:
    """Resolve a Question with an established summary (+ optional evidence ids)."""
    from retornatus.application.question.loop import QuestionLoop

    q = QuestionLoop(path or Path.cwd()).resolve_question(
        question_id,
        summary=summary,
        evidence_ids=list(evidence or []),
    )
    typer.echo(f"Resolved {q.id}")


@loop_app.command("next")
def loop_next(
    change_id: str = typer.Argument(...),
    path: Optional[Path] = typer.Option(None, "--path", "-p"),
) -> None:
    """Project the next ready Question, Task, or Action (not a Loop Engine)."""
    from retornatus.application.change.loop import next_work

    item = next_work(path or Path.cwd(), change_id)
    if item is None:
        typer.echo("Nothing found.")
        raise typer.Exit(1)
    typer.echo(f"{item.kind}\t{item.id}\t{item.summary}")


def run() -> None:
    """Console-script entrypoint for packaging / ``uv tool install``."""
    app()


if __name__ == "__main__":
    run()
