"""Project Environment isolation capabilities into advisory Boundaries.

Govern, don't duplicate: Retornatus does not implement worktrees/sandboxes —
it tells the Agent to prefer native Environment isolation when available.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from retornatus.domain.enums import BoundaryRealization
from retornatus.domain.models import Boundary
from retornatus.infrastructure.environment.adapters import (
    CapabilityModel,
    EnvironmentKind,
    detect_environment,
)


def enrich_capabilities(root: Path, capabilities: CapabilityModel) -> CapabilityModel:
    """
    Derive isolation-related capability flags without inventing a WorkspacePool.

    Detection is heuristic and Environment-native:
    - git worktree command available
    - Cursor / known agent env markers
    """
    details = dict(capabilities.details)
    native_sandbox = capabilities.native_sandbox
    native_worktrees = False
    native_subagents = False

    if shutil.which("git"):
        native_worktrees = True
        details["isolation"] = "git-worktree-available"

    if capabilities.environment is EnvironmentKind.CURSOR:
        native_subagents = True
        if os.environ.get("CURSOR_TRACE_ID") or (root / ".cursor").is_dir():
            native_sandbox = True
            details["sandbox"] = "prefer-cursor-native"
            details["subagents"] = "prefer-cursor-native-subagents"

    if capabilities.environment is EnvironmentKind.CLAUDE_CODE:
        native_subagents = True
        details["subagents"] = "prefer-claude-code-native"

    if capabilities.environment is EnvironmentKind.CODEX:
        details.setdefault("isolation", "prefer-codex-native")

    details["native_worktrees"] = "true" if native_worktrees else "false"
    details["native_subagents"] = "true" if native_subagents else "false"

    return CapabilityModel(
        environment=capabilities.environment,
        native_rules=capabilities.native_rules,
        native_skills=capabilities.native_skills,
        native_sandbox=native_sandbox,
        bridge_files=capabilities.bridge_files,
        details=details,
    )


def isolation_boundaries(
    root: Path,
    capabilities: CapabilityModel | None = None,
) -> list[Boundary]:
    """Advisory Boundaries projecting native isolation — never fake enforcement."""
    if capabilities is None:
        _, capabilities = detect_environment(root)
    caps = enrich_capabilities(root, capabilities)
    items: list[Boundary] = []

    if caps.details.get("native_worktrees") == "true":
        items.append(
            Boundary(
                name="prefer-native-worktree",
                kind="workspace isolation",
                realization=BoundaryRealization.ADVISORY,
                description=(
                    "Use Environment/git worktrees for conflicting writers; "
                    "Retornatus does not run a WorkspacePool"
                ),
            )
        )
    if caps.native_sandbox:
        items.append(
            Boundary(
                name="prefer-native-sandbox",
                kind="execution isolation",
                realization=BoundaryRealization.ADVISORY,
                description="Prefer host sandbox when available; do not rebuild isolation",
            )
        )
    if caps.details.get("native_subagents") == "true":
        items.append(
            Boundary(
                name="prefer-native-subagents",
                kind="execution scope",
                realization=BoundaryRealization.ADVISORY,
                description=(
                    "Specialize via Assignment+Context+Skills on native subagents; "
                    "no permanent ReviewerAgent identities"
                ),
            )
        )
    return items


def capability_flag_list(capabilities: CapabilityModel) -> list[str]:
    flags = [
        name
        for name, enabled in {
            "native_rules": capabilities.native_rules,
            "native_skills": capabilities.native_skills,
            "native_sandbox": capabilities.native_sandbox,
        }.items()
        if enabled
    ]
    details = capabilities.details
    if details.get("native_worktrees") == "true":
        flags.append("native_worktrees")
    if details.get("native_subagents") == "true":
        flags.append("native_subagents")
    return flags
