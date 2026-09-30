"""CLI command group: CI comment rendering."""

from __future__ import annotations

from pathlib import Path

import typer

from retornatus.cli.groups import ci_app


@ci_app.command("comment")
def ci_comment(
    verify: list[Path] | None = typer.Option(
        None,
        "--verify",
        help="Path to a verify --json document. Repeat for each Change.",
    ),
    gate: list[Path] | None = typer.Option(
        None,
        "--gate",
        help="Path to a gate --json document. Repeat for each gate.",
    ),
    path: Path | None = typer.Option(
        None,
        "--path",
        "-p",
        help="Project root. When set, each Change is included via change overview --format pr.",
    ),
    note: list[str] | None = typer.Option(
        None,
        "--note",
        help="Extra note line. Repeat to add more.",
    ),
    omission: bool = typer.Option(
        False,
        "--omission",
        help="Code changed with no Change in the diff. The verdict is NOT_SATISFIED.",
    ),
    verdict_file: Path | None = typer.Option(
        None,
        "--verdict-file",
        help="Write the folded verdict word (SATISFIED, NOT_SATISFIED, or INCONCLUSIVE).",
    ),
    bundle: Path | None = typer.Option(
        None,
        "--bundle",
        help="Write a JSON bundle of the inputs and the folded verdict.",
    ),
) -> None:
    """Print a sticky pull-request comment from verify and gate JSON.

    Stdout is markdown. The verdict is the JSON ``verdict`` fields folded
    together. This command does not re-run Assurance.
    """
    import json

    from retornatus.application.report.comment import (
        change_ids,
        comment_bundle,
        load_json_documents,
        render_ci_comment,
    )
    from retornatus.cli.common import resolve_root

    verify_docs = load_json_documents(list(verify or []))
    gate_docs = load_json_documents(list(gate or []))
    notes = list(note or [])
    sections: list[str] = []
    if path is not None:
        from retornatus.application.change.overview import render_pull_request

        root = resolve_root(path)
        for change_id in change_ids(verify_docs, gate_docs):
            try:
                sections.append(render_pull_request(root, change_id))
            except FileNotFoundError:
                notes.append(f"Change {change_id} has no overview in this checkout.")
    markdown, verdict = render_ci_comment(
        verify_documents=verify_docs,
        gate_documents=gate_docs,
        overview_markdown=sections,
        notes=notes,
        omission=omission,
    )
    if verdict_file is not None:
        verdict_file.write_text(verdict + "\n", encoding="utf-8")
    if bundle is not None:
        payload = comment_bundle(verify_docs, gate_docs, verdict)
        bundle.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    typer.echo(markdown)
