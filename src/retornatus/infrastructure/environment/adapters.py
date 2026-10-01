"""Environment detection, capabilities, and adapters (PRD M4 / M11)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path


class EnvironmentKind(StrEnum):
    CURSOR = "cursor"
    CLAUDE_CODE = "claude_code"
    CODEX = "codex"
    GITHUB_COPILOT = "github_copilot"
    GENERIC = "generic"


# Distinct begin/end so a later ensure_bridge_files replaces the block.
BRIDGE_BEGIN = "<!-- retornatus-bridge:begin -->"
BRIDGE_END = "<!-- retornatus-bridge:end -->"
# Older adapters used one marker twice and never rewrote the body.
_LEGACY_BRIDGE_MARKER = "<!-- retornatus-bridge -->"


def upsert_managed_block(text: str, body: str) -> str:
    """Insert or replace the Retornatus bridge block. Host text outside it stays."""
    block = f"{BRIDGE_BEGIN}\n{body.rstrip()}\n{BRIDGE_END}"
    if BRIDGE_BEGIN in text and BRIDGE_END in text:
        start = text.index(BRIDGE_BEGIN)
        end = text.index(BRIDGE_END, start) + len(BRIDGE_END)
        return text[:start] + block + text[end:]
    if text.count(_LEGACY_BRIDGE_MARKER) >= 2:
        start = text.index(_LEGACY_BRIDGE_MARKER)
        second = text.index(_LEGACY_BRIDGE_MARKER, start + len(_LEGACY_BRIDGE_MARKER))
        end = second + len(_LEGACY_BRIDGE_MARKER)
        return text[:start] + block + text[end:]
    base = text.rstrip()
    if base:
        return base + "\n\n" + block + "\n"
    return block + "\n"


def _write_bridge(path: Path, root: Path, *, title: str, body: str) -> Path:
    """Upsert the managed block, then refresh the active-Rules section."""
    from retornatus.infrastructure.environment.rule_projection import (
        project_active_rules_into,
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8") if path.is_file() else f"# {title}\n"
    path.write_text(upsert_managed_block(existing, body), encoding="utf-8")
    project_active_rules_into(path, root)
    return path


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
        from retornatus.infrastructure.environment.hub_skill import install_hub_skill
        from retornatus.infrastructure.environment.rule_projection import (
            project_active_rules_into,
        )

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
        project_active_rules_into(path, root)
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
        path = _write_bridge(
            root / "CLAUDE.md",
            root,
            title="Project",
            body=("## Retornatus\nRespect Contracts, Rules, Authority, and Evidence under `.retornatus/`.\n"),
        )
        return [path]


class CodexAdapter(EnvironmentAdapter):
    kind = EnvironmentKind.CODEX

    def detect(self, root: Path) -> bool:
        return (root / "AGENTS.md").is_file() or (root / ".codex").is_dir()

    def capabilities(self, root: Path) -> CapabilityModel:
        return CapabilityModel(
            environment=self.kind,
            native_rules=True,
            native_sandbox=True,
            bridge_files=("AGENTS.md",),
            details={"hint": "Prefer Codex native isolation when available"},
        )

    def ensure_bridge_files(self, root: Path) -> list[Path]:
        path = _write_bridge(
            root / "AGENTS.md",
            root,
            title="Agents",
            body=("## Retornatus\nUse `.retornatus/` as canonical governance state.\n"),
        )
        return [path]


class GitHubCopilotAdapter(EnvironmentAdapter):
    """GitHub Copilot custom instructions (``.github/copilot-instructions.md``)."""

    kind = EnvironmentKind.GITHUB_COPILOT

    def detect(self, root: Path) -> bool:
        instructions = root / ".github" / "copilot-instructions.md"
        return instructions.is_file() or (root / ".github").is_dir()

    def capabilities(self, root: Path) -> CapabilityModel:
        return CapabilityModel(
            environment=self.kind,
            native_rules=True,
            bridge_files=(".github/copilot-instructions.md",),
            details={"hint": "Copilot reads .github/copilot-instructions.md"},
        )

    def ensure_bridge_files(self, root: Path) -> list[Path]:
        path = _write_bridge(
            root / ".github" / "copilot-instructions.md",
            root,
            title="GitHub Copilot instructions",
            body=(
                "## Retornatus\n"
                "Use `.retornatus/` as canonical governance state. "
                "Govern the work. Bound the agent. Verify the outcome.\n"
            ),
        )
        return [path]


ADAPTERS: list[EnvironmentAdapter] = [
    CursorAdapter(),
    ClaudeCodeAdapter(),
    CodexAdapter(),
    GitHubCopilotAdapter(),
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
