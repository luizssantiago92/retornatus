"""Deeper doctor diagnostics — continuity and governance hygiene."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from retornatus.application.governance.gates import gate_contract, gate_skill_research
from retornatus.bootstrap.wake import WakeReport, wake_up
from retornatus.domain.enums import SkillStatus
from retornatus.infrastructure.persistence.repository import FileRepository


@dataclass
class DoctorReport:
    wake: WakeReport
    diagnostics: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.wake.initialized and not self.diagnostics

    def render(self) -> str:
        lines = [self.wake.render()]
        if self.warnings:
            lines.append("warnings:")
            lines.extend(f"  - {w}" for w in self.warnings)
        if self.diagnostics:
            # wake already prints its diagnostics; add doctor-specific under same header if new
            extra = [d for d in self.diagnostics if d not in self.wake.diagnostics]
            if extra:
                if "diagnostics:" not in self.wake.render():
                    lines.append("diagnostics:")
                lines.extend(f"  - {d}" for d in extra)
        return "\n".join(lines)


def run_doctor(root: Path | None = None) -> DoctorReport:
    """Wake continuity plus governance hygiene checks."""
    project_root = (root or Path.cwd()).resolve()
    wake = wake_up(project_root, ensure_bridges=False, auto_init=False)
    diagnostics = list(wake.diagnostics)
    warnings: list[str] = []

    if not wake.initialized:
        return DoctorReport(wake=wake, diagnostics=diagnostics, warnings=warnings)

    repo = FileRepository(project_root)

    # Draft contracts awaiting activation
    for cid in repo.list_change_ids():
        try:
            contract, _ = repo.load_contract(cid)
        except FileNotFoundError:
            warnings.append(f"{cid}: Change without contract.json")
            continue
        if not contract.active:
            warnings.append(
                f"{cid}: contract v{contract.version} is draft — "
                "run `change activate` when Situation is sufficient"
            )
        else:
            gate = gate_contract(project_root, cid)
            if not gate.passed:
                diagnostics.append(
                    f"{cid}: active contract fails gate contract: "
                    + "; ".join(gate.messages)
                )

    # Skill drafts / research gaps
    for skill in repo.list_skills():
        if skill.status is SkillStatus.DRAFT:
            warnings.append(f"{skill.id}: DRAFT skill — research then activate")
        if skill.status is SkillStatus.ACTIVE:
            gate = gate_skill_research(project_root, skill.id)
            if not gate.passed:
                diagnostics.append(
                    f"{skill.id}: ACTIVE without research gate: "
                    + "; ".join(gate.messages)
                )

    # Rule candidates
    for rule in repo.list_rules():
        if not rule.active:
            warnings.append(
                f"{rule.id}: Rule Candidate inactive — needs HUMAN Decision to activate"
            )

    # Index disposable reminder when empty but changes exist
    if wake.change_ids and wake.index_entities == 0:
        warnings.append("Index empty despite Changes — wake rebuild may have failed")

    return DoctorReport(wake=wake, diagnostics=diagnostics, warnings=warnings)
