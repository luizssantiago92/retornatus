"""Public CLI entrypoint — intentions, not internal machinery (PRD §62)."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from retornatus import __version__
from retornatus.application.adaptation.service import AdaptationService
from retornatus.application.adaptation.skills import SkillService
from retornatus.application.change.workflow import ChangeWorkflow, TaskSpec
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
decision_app = typer.Typer(help="Human Decisions (HUMAN authority boundary).")
rule_app = typer.Typer(help="Rule candidates and activation.")
assurance_app = typer.Typer(help="Assurance evaluation and independent review.")
execution_app = typer.Typer(help="Host Execution observations (not an agent runtime).")
app.add_typer(change_app, name="change")
app.add_typer(skill_app, name="skill")
app.add_typer(gate_app, name="gate")
app.add_typer(evidence_app, name="evidence")
app.add_typer(finding_app, name="finding")
app.add_typer(question_app, name="question")
app.add_typer(loop_app, name="loop")
app.add_typer(decision_app, name="decision")
app.add_typer(rule_app, name="rule")
app.add_typer(assurance_app, name="assurance")
app.add_typer(execution_app, name="execution")


def _parse_task_specs(
    tasks: list[str] | None,
    depends: list[str] | None,
    resources: list[str] | None,
) -> list[TaskSpec] | None:
    """
    Build TaskSpecs from CLI flags.

    --task descriptions are independent by default.
    --depends ``1:0`` means task index 1 depends on task index 0.
    --resource ``0:app/main.py`` assigns a resource key to task index 0.
    """
    if not tasks:
        return None
    specs = [TaskSpec(description=t) for t in tasks]
    for item in depends or []:
        if ":" not in item:
            raise typer.BadParameter(f"Invalid --depends {item!r}; expected INDEX:DEP[,DEP]")
        left, right = item.split(":", 1)
        try:
            idx = int(left)
            dep_indices = [int(x) for x in right.split(",") if x.strip() != ""]
        except ValueError as exc:
            raise typer.BadParameter(f"Invalid --depends {item!r}") from exc
        if idx < 0 or idx >= len(specs):
            raise typer.BadParameter(f"--depends index out of range: {idx}")
        specs[idx].depends_on_indices = dep_indices
    for item in resources or []:
        if ":" not in item:
            raise typer.BadParameter(
                f"Invalid --resource {item!r}; expected INDEX:resource/path"
            )
        left, right = item.split(":", 1)
        try:
            idx = int(left)
        except ValueError as exc:
            raise typer.BadParameter(f"Invalid --resource {item!r}") from exc
        if idx < 0 or idx >= len(specs):
            raise typer.BadParameter(f"--resource index out of range: {idx}")
        existing = list(specs[idx].resources or [])
        existing.append(right)
        specs[idx].resources = existing
    return specs


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
    no_git: bool = typer.Option(
        False,
        "--no-git",
        help="Do not derive subject freshness from git HEAD.",
    ),
) -> None:
    """Run Assurance against a Change's contract DONE Claims (bound Evidence)."""
    from retornatus.application.assurance.independent import evaluate_change_assurance

    root = (path or Path.cwd()).resolve()
    result = evaluate_change_assurance(
        root, change_id, use_git_state=not no_git
    )
    typer.echo(result.model_dump_json(indent=2))
    raise typer.Exit(code=0 if result.verdict.value == "SATISFIED" else 1)


@app.command()
def run(
    action_id: str = typer.Argument(..., help="Action id to assemble execution context for."),
    path: Optional[Path] = typer.Option(None, "--path", "-p"),
    assurance: bool = typer.Option(
        False,
        "--assurance",
        help="Assemble a fresh independent Assurance ExecutionContext.",
    ),
) -> None:
    """Assemble a stable ExecutionContext for an Action (does not execute agents)."""
    from retornatus.application.execution.context import (
        assemble_assurance_context,
        assemble_execution_context,
    )

    root = (path or Path.cwd()).resolve()
    if assurance:
        ctx = assemble_assurance_context(root, action_id)
    else:
        ctx = assemble_execution_context(root, action_id)
    typer.echo(ctx.model_dump_json(indent=2))


@change_app.command("elicit")
def change_elicit(
    demand: str = typer.Option(..., "--demand", "-d"),
    what: Optional[str] = typer.Option(None, "--what", "-w"),
    done: Optional[list[str]] = typer.Option(None, "--done"),
    situation: Optional[str] = typer.Option(None, "--situation", "-s"),
    constraint: Optional[list[str]] = typer.Option(None, "--constraint"),
    path: Optional[Path] = typer.Option(None, "--path", "-p"),
) -> None:
    """Assess Situation readiness before formalizing a Contract."""
    root = (path or Path.cwd()).resolve()
    if not is_initialized(root):
        initialize_project(root)
    assessment = ChangeWorkflow(root).elicit_situation(
        demand_statement=demand,
        situation=situation,
        what=what,
        done_criteria=list(done or []),
        constraints=list(constraint or []),
    )
    typer.echo(assessment.to_markdown(demand=demand))
    raise typer.Exit(code=0 if assessment.sufficient_for_contract else 1)


@change_app.command("create")
def change_create(
    title: str = typer.Option(..., "--title", "-t"),
    demand: str = typer.Option(..., "--demand", "-d"),
    what: str = typer.Option(..., "--what", "-w"),
    done: list[str] = typer.Option(..., "--done", help="DONE criterion (repeatable)."),
    situation: str = typer.Option("Situation pending detailed analysis.", "--situation", "-s"),
    objective: Optional[str] = typer.Option(None, "--objective", "-o"),
    kind: DemandKind = typer.Option(DemandKind.OTHER, "--kind", "-k"),
    draft_contract: bool = typer.Option(
        False,
        "--draft-contract",
        help="Create Contract without activating (elicitation incomplete).",
    ),
    task: Optional[list[str]] = typer.Option(
        None,
        "--task",
        help="Task description (repeatable). Independent unless --depends is set.",
    ),
    depends: Optional[list[str]] = typer.Option(
        None,
        "--depends",
        help="Task dependency INDEX:DEP[,DEP] (0-based). Example: 1:0",
    ),
    resource: Optional[list[str]] = typer.Option(
        None,
        "--resource",
        help="Task resource INDEX:key (e.g. 0:app/main.py) for conflict detection.",
    ),
    path: Optional[Path] = typer.Option(None, "--path", "-p"),
) -> None:
    """Create a Change with Situation, Contract, and optional Action."""
    root = (path or Path.cwd()).resolve()
    if not is_initialized(root):
        initialize_project(root)
    task_specs = _parse_task_specs(task, depends, resource)
    result = ChangeWorkflow(root).create_change(
        title=title,
        demand_statement=demand,
        demand_kind=kind,
        situation=situation,
        what=what,
        done_criteria=list(done),
        action_objective=objective or what,
        activate_contract=not draft_contract,
        task_specs=task_specs,
        tasks=None if task_specs else None,
    )
    typer.echo(f"Created {result.change.id}")
    if result.situation_assessment:
        ready = result.situation_assessment.sufficient_for_contract
        typer.echo(f"Situation sufficient: {ready}")
        if result.situation_assessment.repo_signals:
            typer.echo(
                f"Repo signals: {len(result.situation_assessment.repo_signals)}"
            )
        if not ready:
            for q in result.situation_assessment.focused_questions:
                typer.echo(f"  Q[{q.topic}]: {q.question}")
    typer.echo(
        f"Contract v{result.contract.version} active={result.contract.active}"
    )
    if result.action:
        typer.echo(f"Action {result.action.id}")
        for t in result.action.tasks:
            deps = ",".join(t.depends_on) if t.depends_on else "-"
            res = ",".join(t.resources) if t.resources else "-"
            typer.echo(f"  Task {t.id} deps={deps} resources={res}")


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
    force: bool = typer.Option(False, "--force", help="Governed bypass of research gate."),
    reason: Optional[str] = typer.Option(
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
    claim_id: Optional[str] = typer.Option(
        None,
        "--claim",
        help="Claim id this Evidence SUPPORTS (required for Assurance binding).",
    ),
    git_state: bool = typer.Option(
        False,
        "--git-state",
        help="Record subject_state as commit:<HEAD> when --state is omitted.",
    ),
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
        supports_claim_id=claim_id,
        capture_git=git_state,
    )
    typer.echo(f"Recorded {ev.id}")
    if ev.subject_state:
        typer.echo(f"subject_state={ev.subject_state}")


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
    """Resolve a Question with established summary + Evidence when required."""
    from retornatus.application.question.loop import (
        QuestionLoop,
        ResolutionIncompleteError,
    )

    try:
        q = QuestionLoop(path or Path.cwd()).resolve_question(
            question_id,
            summary=summary,
            evidence_ids=list(evidence or []),
        )
    except ResolutionIncompleteError as exc:
        typer.echo(str(exc))
        raise typer.Exit(1) from exc
    typer.echo(f"Resolved {q.id}")


@loop_app.command("next")
def loop_next(
    change_id: str = typer.Argument(...),
    path: Optional[Path] = typer.Option(None, "--path", "-p"),
    all_ready: bool = typer.Option(
        False,
        "--all-ready",
        help="List all READY tasks (parallelizable projection).",
    ),
) -> None:
    """Project the next ready Question, Task, or Action (not a Loop Engine)."""
    from retornatus.application.change.loop import project_next_work

    projection = project_next_work(path or Path.cwd(), change_id)
    if projection.primary is None:
        typer.echo("Nothing found.")
        raise typer.Exit(1)
    if all_ready and len(projection.ready) > 1:
        for item in projection.ready:
            typer.echo(f"{item.kind}\t{item.id}\t{item.summary}")
        if projection.parallelizable_task_ids:
            typer.echo(
                "parallelizable\t"
                + ",".join(projection.parallelizable_task_ids)
            )
        return
    item = projection.primary
    typer.echo(f"{item.kind}\t{item.id}\t{item.summary}")
    if len(projection.ready) > 1:
        typer.echo(f"# also ready: {len(projection.ready) - 1} more (use --all-ready)")


@decision_app.command("record")
def decision_record(
    kind: str = typer.Option(
        ...,
        "--kind",
        "-k",
        help="APPROVE_RULE_ACTIVATION | GOVERNANCE_BYPASS | CONTRACT_APPROVAL | OTHER",
    ),
    subject_id: str = typer.Option(..., "--subject", "-s"),
    summary: str = typer.Option(..., "--summary"),
    confirm: str = typer.Option(
        ...,
        "--confirm",
        help="Must equal --subject for activation/bypass decisions.",
    ),
    path: Optional[Path] = typer.Option(None, "--path", "-p"),
) -> None:
    """Record a HUMAN Decision (local harness authority boundary)."""
    from retornatus.domain.enums import DecisionKind

    root = (path or Path.cwd()).resolve()
    try:
        decision_kind = DecisionKind(kind)
    except ValueError as exc:
        typer.echo(f"Unknown decision kind: {kind}")
        raise typer.Exit(1) from exc
    decision = AdaptationService(root).record_human_decision(
        kind=decision_kind,
        subject_id=subject_id,
        summary=summary,
        confirmation_token=confirm,
    )
    typer.echo(f"Recorded {decision.id}")


@rule_app.command("propose")
def rule_propose(
    statement: str = typer.Option(..., "--statement", "-s"),
    applicability: str = typer.Option(..., "--applicability", "-a"),
    learning_id: Optional[str] = typer.Option(None, "--from-learning", "-l"),
    path: Optional[Path] = typer.Option(None, "--path", "-p"),
) -> None:
    """Propose a Rule Candidate (never auto-activates)."""
    root = (path or Path.cwd()).resolve()
    candidate = AdaptationService(root).propose_rule_candidate(
        statement=statement,
        applicability=applicability,
        from_learning_id=learning_id,
    )
    typer.echo(f"Proposed candidate {candidate.id} (active={candidate.active})")


@rule_app.command("activate")
def rule_activate(
    rule_id: str = typer.Argument(...),
    decision_id: str = typer.Option(
        ...,
        "--decision",
        "-d",
        help="Human Decision id approving activation.",
    ),
    path: Optional[Path] = typer.Option(None, "--path", "-p"),
) -> None:
    """Activate a Rule Candidate via HUMAN Decision boundary."""
    from retornatus.application.adaptation.service import HumanAuthorityError

    root = (path or Path.cwd()).resolve()
    try:
        rule = AdaptationService(root).activate_rule(
            rule_id, human_decision_id=decision_id
        )
    except HumanAuthorityError as exc:
        typer.echo(str(exc))
        raise typer.Exit(1) from exc
    typer.echo(f"Activated {rule.id}")


@assurance_app.command("plan")
def assurance_plan(
    change_id: str = typer.Argument(...),
    action_id: Optional[str] = typer.Option(None, "--action", "-a"),
    path: Optional[Path] = typer.Option(None, "--path", "-p"),
) -> None:
    """Project whether independent Assurance Execution is required."""
    from retornatus.application.assurance.independent import plan_independent_assurance

    root = (path or Path.cwd()).resolve()
    plan = plan_independent_assurance(root, change_id, action_id=action_id)
    typer.echo(f"required={plan.required}")
    typer.echo(plan.rationale)
    if plan.claims_needing_review:
        typer.echo("claims: " + ", ".join(plan.claims_needing_review))
    if plan.action_id:
        typer.echo(f"action={plan.action_id}")
    if plan.execution_context is not None:
        typer.echo(
            f"fresh_context independent={plan.execution_context.independent_assurance}"
        )
    raise typer.Exit(code=0 if not plan.required else 2)


@assurance_app.command("review")
def assurance_review(
    change_id: str = typer.Argument(...),
    claim_id: str = typer.Option(..., "--claim"),
    subject: str = typer.Option(..., "--subject", "-s"),
    summary: str = typer.Option(..., "--summary"),
    verdict: str = typer.Option("approved", "--verdict"),
    path: Optional[Path] = typer.Option(None, "--path", "-p"),
) -> None:
    """Record review_result Evidence from an independent Assurance Execution."""
    from retornatus.application.assurance.independent import (
        record_independent_review_evidence,
    )

    root = (path or Path.cwd()).resolve()
    eid = record_independent_review_evidence(
        root,
        change_id=change_id,
        claim_id=claim_id,
        subject=subject,
        summary=summary,
        verdict=verdict,
    )
    typer.echo(f"Recorded {eid}")


@execution_app.command("record")
def execution_record(
    action_id: str = typer.Option(..., "--action", "-a"),
    summary: str = typer.Option(..., "--summary", "-s"),
    ok: bool = typer.Option(True, "--ok/--failed"),
    artifact: Optional[list[str]] = typer.Option(
        None,
        "--artifact",
        help="Artifact path produced by Host execution (repeatable).",
    ),
    producer: str = typer.Option("host", "--producer"),
    path: Optional[Path] = typer.Option(None, "--path", "-p"),
) -> None:
    """Record that Environment-native Host work completed for an Action."""
    from retornatus.application.execution.host_record import HostExecutionService

    root = (path or Path.cwd()).resolve()
    record = HostExecutionService(root).record(
        action_id=action_id,
        summary=summary,
        ok=ok,
        artifact_paths=list(artifact or []),
        producer=producer,
        capture_git=True,
    )
    typer.echo(f"Recorded {record.id} for {record.action_id} ok={record.ok}")
    if record.subject_state:
        typer.echo(f"subject_state={record.subject_state}")


@execution_app.command("list")
def execution_list(
    action_id: str = typer.Argument(...),
    path: Optional[Path] = typer.Option(None, "--path", "-p"),
) -> None:
    """List Host Execution records for an Action."""
    from retornatus.application.execution.host_record import HostExecutionService

    root = (path or Path.cwd()).resolve()
    records = HostExecutionService(root).list_for_action(action_id)
    if not records:
        typer.echo("No host executions.")
        return
    for record in records:
        typer.echo(f"{record.id}\tok={record.ok}\t{record.summary}")


def run() -> None:
    """Console-script entrypoint for packaging / ``uv tool install``."""
    app()


if __name__ == "__main__":
    run()
