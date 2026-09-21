"""Environment detection, capabilities, and adapters (PRD M4 / M11)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class EnvironmentKind(str, Enum):
    CURSOR = "cursor"
    CLAUDE_CODE = "claude_code"
    CODEX = "codex"
    GENERIC = "generic"


@dataclass(frozen=True)
class CapabilityModel:
    """Discovered capabilities of the current execution environment."""

    environment: EnvironmentKind
    native_rules: bool = False
    native_skills: bool = False
    native_sandbox: bool = False
    bridge_files: tuple[str, ...] = ()
    details: dict[str, str] = field(default_factory=dict)


class EnvironmentAdapter:
    """Base adapter — prefer native capabilities (PRD §64)."""

    kind: EnvironmentKind = EnvironmentKind.GENERIC

    def detect(self, root: Path) -> bool:
        return True

    def capabilities(self, root: Path) -> CapabilityModel:
        return CapabilityModel(environment=self.kind)

    def ensure_bridge_files(self, root: Path) -> list[Path]:
        """Generate only necessary bridge projections. Canonical truth stays in .retornatus."""
        return []


class GenericAdapter(EnvironmentAdapter):
    kind = EnvironmentKind.GENERIC


class CursorAdapter(EnvironmentAdapter):
    kind = EnvironmentKind.CURSOR

    def detect(self, root: Path) -> bool:
        return (root / ".cursor").is_dir() or os.environ.get("CURSOR_TRACE_ID") is not None

    def capabilities(self, root: Path) -> CapabilityModel:
        return CapabilityModel(
            environment=self.kind,
            native_rules=True,
            native_skills=True,
            bridge_files=(".cursor/rules/retornatus.mdc",),
            details={"hint": "Cursor rules/skills are native"},
        )

    def ensure_bridge_files(self, root: Path) -> list[Path]:
        path = root / ".cursor" / "rules" / "retornatus.mdc"
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text(
                "---\ndescription: Retornatus governance bridge\nglobs:\nalwaysApply: true\n---\n\n"
                "Follow Retornatus Contracts, Rules, and Evidence requirements in `.retornatus/`.\n"
                "Govern the work. Bound the agent. Verify the outcome.\n"
                "Use the Retornatus hub skill under `.cursor/skills/retornatus/`.\n",
                encoding="utf-8",
            )
        from retornatus.infrastructure.environment.hub_skill import install_hub_skill

        hub = install_hub_skill(root)
        return [path, hub]


class ClaudeCodeAdapter(EnvironmentAdapter):
    kind = EnvironmentKind.CLAUDE_CODE

    def detect(self, root: Path) -> bool:
        return (root / "CLAUDE.md").is_file() or (root / ".claude").is_dir()

    def capabilities(self, root: Path) -> CapabilityModel:
        return CapabilityModel(
            environment=self.kind,
            native_rules=True,
            bridge_files=("CLAUDE.md",),
            details={"hint": "CLAUDE.md is the native instruction surface"},
        )

    def ensure_bridge_files(self, root: Path) -> list[Path]:
        path = root / "CLAUDE.md"
        marker = "<!-- retornatus-bridge -->"
        snippet = (
            f"\n{marker}\n"
            "## Retornatus\n"
            "Respect Contracts, Rules, Authority, and Evidence under `.retornatus/`.\n"
            f"{marker}\n"
        )
        if path.exists():
            text = path.read_text(encoding="utf-8")
            if marker not in text:
                path.write_text(text.rstrip() + snippet, encoding="utf-8")
        else:
            path.write_text("# Project\n" + snippet, encoding="utf-8")
        return [path]


class CodexAdapter(EnvironmentAdapter):
    kind = EnvironmentKind.CODEX

    def detect(self, root: Path) -> bool:
        return (root / "AGENTS.md").is_file() or (root / ".codex").is_dir()

    def capabilities(self, root: Path) -> CapabilityModel:
        return CapabilityModel(
            environment=self.kind,
            native_rules=True,
            bridge_files=("AGENTS.md",),
        )

    def ensure_bridge_files(self, root: Path) -> list[Path]:
        path = root / "AGENTS.md"
        marker = "<!-- retornatus-bridge -->"
        snippet = (
            f"\n{marker}\n"
            "## Retornatus\n"
            "Use `.retornatus/` as canonical governance state.\n"
            f"{marker}\n"
        )
        if path.exists():
            text = path.read_text(encoding="utf-8")
            if marker not in text:
                path.write_text(text.rstrip() + snippet, encoding="utf-8")
        else:
            path.write_text("# Agents\n" + snippet, encoding="utf-8")
        return [path]


ADAPTERS: list[EnvironmentAdapter] = [
    CursorAdapter(),
    ClaudeCodeAdapter(),
    CodexAdapter(),
    GenericAdapter(),
]


def detect_environment(root: Path) -> tuple[EnvironmentAdapter, CapabilityModel]:
    for adapter in ADAPTERS:
        if adapter.kind is EnvironmentKind.GENERIC:
            continue
        if adapter.detect(root):
            return adapter, adapter.capabilities(root)
    generic = GenericAdapter()
    return generic, generic.capabilities(root)
