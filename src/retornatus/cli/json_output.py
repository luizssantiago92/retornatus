"""Stdout JSON for verdict commands. Diagnostics stay on stderr."""

from __future__ import annotations

import json
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any, NoReturn

import typer

from retornatus.application.governance.gates import GateResult
from retornatus.application.report.envelope import gate_document

JSON_OUTPUT_HELP = (
    "Print the versioned verdict envelope as the only stdout. Diagnostics go to stderr. Exit codes match text mode."
)


def write_json(document: Mapping[str, Any]) -> None:
    """Write one JSON document and a trailing newline. No Rich formatting."""
    sys.stdout.write(json.dumps(document, indent=2, ensure_ascii=False))
    sys.stdout.write("\n")


def finish_gate(
    result: GateResult,
    *,
    root: Path,
    as_json: bool,
    change_id: str | None = None,
    action_id: str | None = None,
    skill_id: str | None = None,
) -> NoReturn:
    """Print a gate result and exit with its existing code."""
    if as_json:
        for message in result.messages:
            typer.echo(message, err=True)
        write_json(
            gate_document(
                root,
                result,
                change_id=change_id,
                action_id=action_id,
                skill_id=skill_id,
            )
        )
    else:
        for message in result.messages:
            typer.echo(message)
    raise typer.Exit(code=result.exit_code)
