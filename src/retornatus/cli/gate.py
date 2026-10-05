"""CLI command group: gate."""

from __future__ import annotations

from pathlib import Path

import typer

from retornatus.cli.common import resolve_root
from retornatus.cli.groups import gate_app
from retornatus.cli.json_output import JSON_OUTPUT_HELP, finish_gate


@gate_app.command("policy")
def gate_policy_cmd(
    action_id: str = typer.Argument(..., help="Action id to evaluate Policy against."),
    path: Path | None = typer.Option(None, "--path", "-p"),
    as_json: bool = typer.Option(False, "--json", help=JSON_OUTPUT_HELP),
) -> None:
    """Gate: Policy ALLOW for Action objective (exit 1 = STOP)."""
    from retornatus.application.governance.gates import gate_policy

    root = path or Path.cwd()
    result = gate_policy(root, action_id)
    finish_gate(result, root=root, as_json=as_json, action_id=action_id)


@gate_app.command("contract")
def gate_contract_cmd(
    change_id: str = typer.Argument(...),
    path: Path | None = typer.Option(None, "--path", "-p"),
    as_json: bool = typer.Option(False, "--json", help=JSON_OUTPUT_HELP),
) -> None:
    """Gate: active Contract with WHAT + DONE (exit 1 = STOP)."""
    from retornatus.application.governance.gates import gate_contract

    root = path or Path.cwd()
    result = gate_contract(root, change_id)
    finish_gate(result, root=root, as_json=as_json, change_id=change_id)


@gate_app.command("evidence")
def gate_evidence_cmd(
    change_id: str = typer.Argument(...),
    path: Path | None = typer.Option(None, "--path", "-p"),
    as_json: bool = typer.Option(False, "--json", help=JSON_OUTPUT_HELP),
) -> None:
    """Gate: Evidence artifacts exist (exit 1 = STOP)."""
    from retornatus.application.governance.gates import gate_evidence

    root = path or Path.cwd()
    result = gate_evidence(root, change_id)
    finish_gate(result, root=root, as_json=as_json, change_id=change_id)


@gate_app.command("skill-research")
def gate_skill_research_cmd(
    skill_id: str = typer.Argument(...),
    path: Path | None = typer.Option(None, "--path", "-p"),
    as_json: bool = typer.Option(False, "--json", help=JSON_OUTPUT_HELP),
) -> None:
    """Gate: Skill RESEARCH filled with sources (exit 1 = STOP)."""
    from retornatus.application.governance.gates import gate_skill_research

    root = path or Path.cwd()
    result = gate_skill_research(root, skill_id)
    finish_gate(result, root=root, as_json=as_json, skill_id=skill_id)


@gate_app.command("assurance")
def gate_assurance_cmd(
    change_id: str = typer.Argument(...),
    path: Path | None = typer.Option(None, "--path", "-p"),
    as_json: bool = typer.Option(False, "--json", help=JSON_OUTPUT_HELP),
) -> None:
    """Gate: Assurance SATISFIED (exit 1 = STOP)."""
    from retornatus.application.governance.gates import gate_assurance

    root = path or Path.cwd()
    result = gate_assurance(root, change_id)
    finish_gate(result, root=root, as_json=as_json, change_id=change_id)


@gate_app.command("budget")
def gate_budget_cmd(
    action_id: str = typer.Argument(...),
    path: Path | None = typer.Option(None, "--path", "-p"),
    as_json: bool = typer.Option(False, "--json", help=JSON_OUTPUT_HELP),
) -> None:
    """Gate: Action attempt budget not exhausted (exit 1 = STOP)."""
    from retornatus.application.governance.gates import gate_budget

    root = path or Path.cwd()
    result = gate_budget(root, action_id)
    finish_gate(result, root=root, as_json=as_json, action_id=action_id)


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
    as_json: bool = typer.Option(False, "--json", help=JSON_OUTPUT_HELP),
) -> None:
    """Gate: added diff lines must not introduce suppression markers (exit 1 = STOP)."""
    from retornatus.application.governance.gates import gate_suppressions

    root = resolve_root(path)
    result = gate_suppressions(root, base=base, staged=staged)
    finish_gate(result, root=root, as_json=as_json)


@gate_app.command("omission")
def gate_omission_cmd(
    path: Path | None = typer.Option(None, "--path", "-p"),
    base: str | None = typer.Option(
        None,
        "--base",
        help="Compare git diff --name-only base...HEAD.",
    ),
    staged: bool = typer.Option(
        False,
        "--staged",
        help="Compare the index only. Without --base or --staged, staged and unstaged changes are used.",
    ),
    pr_author: str = typer.Option(
        "",
        "--pr-author",
        help=(
            "Pull request author login. The GitHub Action passes "
            "pull_request.user.login. A title, body, or commit message is not a login."
        ),
    ),
    change: str | None = typer.Option(
        None,
        "--change",
        help="Change id already selected for this run. Omission is skipped.",
    ),
    as_json: bool = typer.Option(False, "--json", help=JSON_OUTPUT_HELP),
) -> None:
    """Gate: code with no Change fails, unless a listed bot only touched manifests."""
    from retornatus.application.governance.gates import gate_omission

    root = resolve_root(path)
    result = gate_omission(
        root,
        base=base,
        staged=staged,
        author=pr_author,
        declared_change=change,
    )
    finish_gate(result, root=root, as_json=as_json)


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
    as_json: bool = typer.Option(False, "--json", help=JSON_OUTPUT_HELP),
) -> None:
    """Gate: diff stays inside Task.resources and .retornatus (exit 1 = STOP)."""
    from retornatus.application.governance.gates import gate_scope

    root = resolve_root(path)
    result = gate_scope(root, change_id, base=base, staged=staged)
    finish_gate(result, root=root, as_json=as_json, change_id=change_id)
