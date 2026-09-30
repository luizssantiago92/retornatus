"""Public CLI entrypoint — intentions, not internal machinery (PRD §62)."""

from __future__ import annotations

# Register commands. Import order of root commands is the definition order
# inside each module; Typer lists direct commands before subcommand groups.
from retornatus.cli import action as _action
from retornatus.cli import assurance as _assurance
from retornatus.cli import change as _change
from retornatus.cli import checks as _checks
from retornatus.cli import ci as _ci
from retornatus.cli import decision as _decision
from retornatus.cli import evidence as _evidence
from retornatus.cli import execution as _execution
from retornatus.cli import finding as _finding
from retornatus.cli import gate as _gate
from retornatus.cli import hook as _hook
from retornatus.cli import hooks as _hooks
from retornatus.cli import intake as _intake
from retornatus.cli import lesson as _lesson
from retornatus.cli import loop as _loop
from retornatus.cli import ops as _ops
from retornatus.cli import policy as _policy
from retornatus.cli import preset as _preset
from retornatus.cli import question as _question
from retornatus.cli import receipt as _receipt
from retornatus.cli import root as _root
from retornatus.cli import rule as _rule
from retornatus.cli import skill as _skill
from retornatus.cli import task as _task
from retornatus.cli.groups import app

# Imported for side effects (command registration).
_REGISTERED = (
    _root,
    _change,
    _skill,
    _gate,
    _checks,
    _ci,
    _hooks,
    _hook,
    _evidence,
    _finding,
    _question,
    _loop,
    _decision,
    _rule,
    _policy,
    _preset,
    _assurance,
    _execution,
    _task,
    _lesson,
    _ops,
    _intake,
    _action,
    _receipt,
)


def entrypoint() -> None:
    """Console-script entrypoint for packaging / ``uv tool install``."""
    app()


if __name__ == "__main__":
    entrypoint()
