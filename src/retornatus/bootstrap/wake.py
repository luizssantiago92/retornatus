"""Wake Up — reconstruct continuity from repository-native state (PRD M4)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from retornatus.bootstrap.init import initialize_project, is_initialized
from retornatus.infrastructure.environment.adapters import (
    CapabilityModel,
    detect_environment,
)
from retornatus.infrastructure.index.sqlite_index import RetornatusIndex
from retornatus.infrastructure.persistence.repository import FileRepository


@dataclass
class WakeReport:
    root: Path
    initialized: bool
    environment: str
    capabilities: CapabilityModel
    change_ids: list[str] = field(default_factory=list)
    rule_count: int = 0
    learning_count: int = 0
    index_entities: int = 0
    bridge_files: list[str] = field(default_factory=list)
    diagnostics: list[str] = field(default_factory=list)
    project_context_summary: str | None = None

    def render(self) -> str:
        lines = [
            f"Retornatus wake @ {self.root}",
            f"initialized: {self.initialized}",
            f"environment: {self.environment}",
            f"capabilities: native_rules={self.capabilities.native_rules} "
            f"native_skills={self.capabilities.native_skills} "
            f"native_sandbox={self.capabilities.native_sandbox}",
            f"changes: {len(self.change_ids)} {self.change_ids}",
            f"rules: {self.rule_count}",
            f"learnings: {self.learning_count}",
            f"index_entities: {self.index_entities}",
        ]
        if self.project_context_summary:
            lines.append("project_context:")
            for line in self.project_context_summary.splitlines()[:16]:
                lines.append(f"  {line}")
        if self.bridge_files:
            lines.append("bridge_files: " + ", ".join(self.bridge_files))
        if self.diagnostics:
            lines.append("diagnostics:")
            lines.extend(f"  - {d}" for d in self.diagnostics)
        return "\n".join(lines)


def wake_up(
    root: Path | None = None,
    *,
    ensure_bridges: bool = False,
    auto_init: bool = True,
) -> WakeReport:
    project_root = (root or Path.cwd()).resolve()
    diagnostics: list[str] = []

    if not is_initialized(project_root):
        if auto_init:
            initialize_project(project_root)
            diagnostics.append("Initialized missing .retornatus/")
        else:
            diagnostics.append("Project not initialized")

    repo = FileRepository(project_root)
    adapter, capabilities = detect_environment(project_root)
    bridge_files: list[str] = []
    if ensure_bridges and adapter.kind.value != "generic":
        bridge_files = [str(p) for p in adapter.ensure_bridge_files(project_root)]

    change_ids = repo.list_change_ids() if is_initialized(project_root) else []
    rules = repo.list_rules() if is_initialized(project_root) else []
    learnings = repo.list_learnings() if is_initialized(project_root) else []

    index = RetornatusIndex(project_root)
    try:
        entities = index.rebuild()
    except Exception as exc:  # noqa: BLE001 — surface as diagnostic
        entities = 0
        diagnostics.append(f"Index rebuild failed: {exc}")

    # Validate config present
    try:
        repo.load_config()
    except FileNotFoundError:
        diagnostics.append("Missing config.toml")

    project_summary = None
    project_md = repo.paths.project_md
    if project_md.is_file():
        text = project_md.read_text(encoding="utf-8", errors="replace")
        # Prefer Identity + Stack sections for Situation orientation
        lines = [ln for ln in text.splitlines() if ln.strip()][:20]
        project_summary = "\n".join(lines)
    else:
        diagnostics.append("No project.md — run project-init for brownfield context")

    return WakeReport(
        root=project_root,
        initialized=is_initialized(project_root),
        environment=adapter.kind.value,
        capabilities=capabilities,
        change_ids=change_ids,
        rule_count=len(rules),
        learning_count=len(learnings),
        index_entities=entities,
        bridge_files=bridge_files,
        diagnostics=diagnostics,
        project_context_summary=project_summary,
    )
