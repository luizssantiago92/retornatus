"""CLI command group: change."""

from __future__ import annotations

from pathlib import Path

import typer

from retornatus.application.adaptation.service import AdaptationService
from retornatus.application.change.workflow import ChangeWorkflow
from retornatus.bootstrap.init import initialize_project, is_initialized
from retornatus.cli.common import parse_task_specs, resolve_root
from retornatus.cli.groups import change_app
from retornatus.cli.json_output import JSON_OUTPUT_HELP
from retornatus.domain.enums import ComplexityLane, DemandKind


@change_app.command("elicit")
def change_elicit(
    demand: str = typer.Option(..., "--demand", "-d"),
    what: str | None = typer.Option(None, "--what", "-w"),
    done: list[str] | None = typer.Option(None, "--done"),
    situation: str | None = typer.Option(None, "--situation", "-s"),
    constraint: list[str] | None = typer.Option(None, "--constraint"),
    answer: list[str] | None = typer.Option(
        None,
        "--answer",
        "-a",
        help="Record a requirements answer TOPIC=text (repeatable). "
        "WHAT/DONE/constraints fold into the assessment; other topics close focused questions.",
    ),
    write: Path | None = typer.Option(
        None,
        "--write",
        help="Write Situation markdown to this path (before a Change exists).",
    ),
    path: Path | None = typer.Option(None, "--path", "-p"),
) -> None:
    """Requirements analysis — assess Situation readiness before a Contract."""
    from retornatus.application.change.situation import (
        apply_answers,
        merge_answers_into_inputs,
        parse_answer_option,
    )

    root = resolve_root(path)
    if not is_initialized(root):
        initialize_project(root)

    parsed: dict[str, str] = {}
    for raw in answer or []:
        try:
            topic, text = parse_answer_option(raw)
        except ValueError as exc:
            typer.echo(str(exc), err=True)
            raise typer.Exit(2) from exc
        parsed[topic] = text

    what_m, done_m, constraints_m, remaining = merge_answers_into_inputs(
        what=what,
        done_criteria=list(done or []),
        constraints=list(constraint or []),
        answers=parsed,
    )
    answered_topics = {t.lower() for t in remaining} | {
        t.lower() for t in parsed if t.lower() in {"what", "done", "constraint", "constraints"}
    }

    assessment = ChangeWorkflow(root).elicit_situation(
        demand_statement=demand,
        situation=situation,
        what=what_m,
        done_criteria=done_m,
        constraints=constraints_m,
        answered_topics=answered_topics,
    )
    if remaining:
        assessment = apply_answers(assessment, remaining)

    md = assessment.to_markdown(demand=demand)
    typer.echo(md)
    if write is not None:
        write_path = write if write.is_absolute() else (root / write)
        write_path.parent.mkdir(parents=True, exist_ok=True)
        write_path.write_text(md, encoding="utf-8")
        typer.echo(f"Wrote Situation to {write_path}")
    raise typer.Exit(code=0 if assessment.sufficient_for_contract else 1)


@change_app.command("create")
def change_create(
    title: str = typer.Option(..., "--title", "-t"),
    demand: str = typer.Option(..., "--demand", "-d"),
    what: str = typer.Option(..., "--what", "-w"),
    done: list[str] = typer.Option(..., "--done", help="DONE criterion (repeatable)."),
    situation: str = typer.Option("Situation pending detailed analysis.", "--situation", "-s"),
    objective: str | None = typer.Option(None, "--objective", "-o"),
    kind: DemandKind = typer.Option(DemandKind.OTHER, "--kind", "-k"),
    draft_contract: bool = typer.Option(
        False,
        "--draft-contract",
        help="Create Contract without activating (elicitation incomplete).",
    ),
    task: list[str] | None = typer.Option(
        None,
        "--task",
        help="Task description (repeatable). Independent unless --depends is set.",
    ),
    depends: list[str] | None = typer.Option(
        None,
        "--depends",
        help="Task dependency INDEX:DEP[,DEP] (0-based). Example: 1:0",
    ),
    resource: list[str] | None = typer.Option(
        None,
        "--resource",
        help="Task resource INDEX:key (e.g. 0:app/main.py) for conflict detection.",
    ),
    lane: ComplexityLane | None = typer.Option(
        None,
        "--lane",
        help="Ceremony lane QUICK|STANDARD|COMPLEX (auto-classified when omitted).",
    ),
    path: Path | None = typer.Option(None, "--path", "-p"),
) -> None:
    """Create a Change with Situation, Contract, and optional Action."""
    root = resolve_root(path)
    if not is_initialized(root):
        initialize_project(root)
    task_specs = parse_task_specs(task, depends, resource)
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
        lane=lane.value if lane else None,
    )
    typer.echo(f"Created {result.change.id}")
    if result.change.lane:
        typer.echo(f"Lane: {result.change.lane}")
    if result.situation_assessment:
        ready = result.situation_assessment.sufficient_for_contract
        typer.echo(f"Situation sufficient: {ready}")
        if result.situation_assessment.repo_signals:
            typer.echo(f"Repo signals: {len(result.situation_assessment.repo_signals)}")
        if not ready:
            for q in result.situation_assessment.focused_questions:
                typer.echo(f"  Q[{q.topic}]: {q.question}")
    typer.echo(f"Contract v{result.contract.version} active={result.contract.active}")
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
    summary: str | None = typer.Option(None, "--summary"),
    path: Path | None = typer.Option(None, "--path", "-p"),
) -> None:
    """Record a Learning from validated experience."""
    root = resolve_root(path)
    meta = AdaptationService(root).record_learning(title=title, body=body, summary=summary)
    typer.echo(f"Recorded {meta.id}")


@change_app.command("overview")
def change_overview_cmd(
    change_id: str = typer.Argument(..., help="Change id (e.g. C-0001)."),
    path: Path | None = typer.Option(None, "--path", "-p"),
    output_format: str = typer.Option(
        "text",
        "--format",
        help="text (dashboard), pr (markdown pull-request body), or json (verdict envelope).",
    ),
    as_json: bool = typer.Option(False, "--json", help=JSON_OUTPUT_HELP),
) -> None:
    """Dashboard: Claims ↔ Evidence, Tasks, Questions, next work."""
    from retornatus.application.change.overview import (
        build_change_overview,
        render_pull_request,
    )
    from retornatus.application.report.envelope import (
        overview_document,
        overview_missing_document,
    )
    from retornatus.cli.json_output import write_json
    from retornatus.domain.errors import UsageError

    if output_format not in {"text", "pr", "json"}:
        raise UsageError("--format must be text, pr, or json")
    if as_json and output_format == "pr":
        raise UsageError("--json cannot be combined with --format pr")
    use_json = as_json or output_format == "json"
    root = resolve_root(path)
    try:
        if use_json:
            write_json(overview_document(root, change_id))
            return
        if output_format == "pr":
            typer.echo(render_pull_request(root, change_id))
            return
        overview = build_change_overview(root, change_id)
    except FileNotFoundError:
        message = f"Change not found: {change_id}"
        if use_json:
            typer.echo(message, err=True)
            write_json(overview_missing_document(root, change_id))
        else:
            typer.echo(message)
        raise typer.Exit(code=1) from None
    typer.echo(overview.render())


@change_app.command("classify")
def change_classify_cmd(
    demand: str = typer.Option("", "--demand", "-d"),
    what: str = typer.Option("", "--what", "-w"),
    done: list[str] | None = typer.Option(None, "--done"),
    kind: DemandKind = typer.Option(DemandKind.OTHER, "--kind", "-k"),
    tasks: int = typer.Option(0, "--tasks", help="Expected task count."),
    constraints: int = typer.Option(0, "--constraints", help="Expected constraint count."),
    from_diff: str | None = typer.Option(
        None,
        "--from-diff",
        help="Git base ref. Combine changed-file count, lines, and sensitive globs with text heuristics.",
    ),
    path: Path | None = typer.Option(None, "--path", "-p"),
) -> None:
    """Classify ceremony lane (QUICK | STANDARD | COMPLEX) — advisory."""
    from retornatus.application.change.classify import classify_change, collect_diff_signals
    from retornatus.domain.errors import UsageError

    if not demand.strip() and not from_diff:
        raise UsageError("Pass --demand and/or --from-diff")
    diff = None
    if from_diff:
        diff = collect_diff_signals(resolve_root(path), from_diff)
    result = classify_change(
        demand=demand,
        what=what,
        done_criteria=list(done or []),
        demand_kind=kind,
        task_count=tasks,
        constraint_count=constraints,
        diff=diff,
    )
    typer.echo(result.render())


@change_app.command("activate")
def change_activate(
    change_id: str = typer.Argument(...),
    path: Path | None = typer.Option(None, "--path", "-p"),
) -> None:
    """Activate a draft Contract when Situation is sufficient."""
    root = resolve_root(path)
    try:
        contract = ChangeWorkflow(root).activate_contract(change_id)
    except ValueError as exc:
        typer.echo(str(exc))
        raise typer.Exit(1) from exc
    typer.echo(f"Activated {change_id} → contract v{contract.version} active={contract.active}")


@change_app.command("reopen")
def change_reopen(
    change_id: str = typer.Argument(...),
    what: str = typer.Option(..., "--what", "-w"),
    done: list[str] = typer.Option(..., "--done"),
    constraint: list[str] | None = typer.Option(None, "--constraint"),
    note: str | None = typer.Option(None, "--note", help="Situation reopen note."),
    draft: bool = typer.Option(False, "--draft", help="Leave new Contract inactive."),
    path: Path | None = typer.Option(None, "--path", "-p"),
) -> None:
    """Material Contract change: archive active version and create a new one."""
    root = resolve_root(path)
    contract = ChangeWorkflow(root).reopen_contract(
        change_id,
        what=what,
        done_criteria=list(done),
        constraints=list(constraint) if constraint is not None else None,
        situation_note=note,
        activate=not draft,
    )
    typer.echo(f"Reopened {change_id} → contract v{contract.version} active={contract.active}")
    archive = Path(root) / ".retornatus" / "changes" / change_id / "contracts" / f"v{contract.version - 1}.json"
    if archive.is_file():
        typer.echo(f"Archived prior version at {archive}")
