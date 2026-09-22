"""Deeper doctor diagnostics — Process vs Brakes readiness + governance hygiene."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from retornatus.application.governance.gates import gate_contract, gate_skill_research
from retornatus.bootstrap.wake import WakeReport, wake_up
from retornatus.domain.enums import SkillStatus
from retornatus.infrastructure.persistence.repository import FileRepository


@dataclass
class ReadinessScore:
    name: str
    earned: int
    total: int
    details: list[str] = field(default_factory=list)

    @property
    def ratio(self) -> str:
        return f"{self.earned}/{self.total}"

    @property
    def complete(self) -> bool:
        return self.earned >= self.total and self.total > 0


@dataclass
class DoctorReport:
    wake: WakeReport
    diagnostics: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    process: ReadinessScore | None = None
    brakes: ReadinessScore | None = None

    @property
    def ok(self) -> bool:
        return self.wake.initialized and not self.diagnostics

    @property
    def mode(self) -> str:
        if self.process and self.brakes:
            if self.process.complete and self.brakes.complete:
                return "Brakes-ready"
            if self.process.complete:
                return "Process-only"
            return "Not ready"
        return "unknown"

    def render(self) -> str:
        lines = [self.wake.render()]
        if self.process and self.brakes:
            lines.append("")
            lines.append(f"process: {self.process.ratio} — {self.process.name}")
            lines.extend(f"  - {d}" for d in self.process.details)
            lines.append(f"brakes: {self.brakes.ratio} — {self.brakes.name}")
            lines.extend(f"  - {d}" for d in self.brakes.details)
            lines.append(f"mode: {self.mode}")
            lines.append(
                "  Process = hub/workflow can run; "
                "Brakes = gates + verify paths are usable"
            )
        if self.warnings:
            lines.append("warnings:")
            lines.extend(f"  - {w}" for w in self.warnings)
        if self.diagnostics:
            extra = [d for d in self.diagnostics if d not in self.wake.diagnostics]
            if extra:
                if "diagnostics:" not in "\n".join(lines):
                    lines.append("diagnostics:")
                lines.extend(f"  - {d}" for d in extra)
        return "\n".join(lines)


def _score_process(root: Path, wake: WakeReport) -> ReadinessScore:
    details: list[str] = []
    earned = 0
    checks = [
        ("initialized", wake.initialized, ".retornatus/ present"),
        ("config", (root / ".retornatus" / "config.toml").is_file(), "config.toml"),
        (
            "hub",
            (root / ".cursor" / "skills" / "retornatus" / "SKILL.md").is_file()
            or (root / "CLAUDE.md").is_file()
            or (root / "AGENTS.md").is_file(),
            "hub skill or host bridge",
        ),
        (
            "project_context",
            (root / ".retornatus" / "project" / "project.md").is_file()
            or not wake.initialized,
            "project.md (optional for greenfield)",
        ),
    ]
    # project_context is soft — count as earned if missing (optional)
    for key, ok, label in checks:
        if key == "project_context":
            if ok:
                earned += 1
                details.append(f"ok: {label}")
            else:
                earned += 1  # optional — still counts toward process
                details.append(f"optional missing: {label} (run project-init)")
            continue
        if ok:
            earned += 1
            details.append(f"ok: {label}")
        else:
            details.append(f"missing: {label}")
    return ReadinessScore(
        name="workflow continuity",
        earned=earned,
        total=len(checks),
        details=details,
    )


def _score_brakes(root: Path, wake: WakeReport) -> ReadinessScore:
    details: list[str] = []
    earned = 0
    total = 4

    # Gate module importable / callable
    try:
        from retornatus.application.governance import gates as _gates  # noqa: F401

        earned += 1
        details.append("ok: gate module importable")
    except Exception as exc:  # noqa: BLE001
        details.append(f"missing: gate module ({exc})")

    # verify path
    try:
        from retornatus.application.assurance.independent import (  # noqa: F401
            evaluate_change_assurance,
        )

        earned += 1
        details.append("ok: assurance/verify path importable")
    except Exception as exc:  # noqa: BLE001
        details.append(f"missing: assurance path ({exc})")

    # At least one active contract passes gate OR no changes yet (vacuously ready)
    if not wake.change_ids:
        earned += 1
        details.append("ok: no Changes yet (gates ready when created)")
    else:
        repo = FileRepository(root)
        active_ok = False
        any_active = False
        for cid in repo.list_change_ids():
            try:
                contract, _ = repo.load_contract(cid)
            except FileNotFoundError:
                continue
            if not contract.active:
                continue
            any_active = True
            if gate_contract(root, cid).passed:
                active_ok = True
                break
        if not any_active or active_ok:
            earned += 1
            details.append(
                "ok: active contract gate pass"
                if any_active
                else "ok: only draft contracts (activate then gate)"
            )
        else:
            details.append("fail: active contract(s) fail gate contract")

    # Index rebuildable
    if wake.initialized:
        earned += 1
        details.append("ok: wake/index path available")
    else:
        details.append("missing: initialize before brakes")

    return ReadinessScore(
        name="mechanical gates",
        earned=earned,
        total=total,
        details=details,
    )


def run_doctor(root: Path | None = None) -> DoctorReport:
    """Wake continuity plus Process/Brakes scores and governance hygiene."""
    project_root = (root or Path.cwd()).resolve()
    wake = wake_up(project_root, ensure_bridges=False, auto_init=False)
    diagnostics = list(wake.diagnostics)
    warnings: list[str] = []

    process = _score_process(project_root, wake)
    brakes = _score_brakes(project_root, wake)

    if not wake.initialized:
        return DoctorReport(
            wake=wake,
            diagnostics=diagnostics,
            warnings=warnings,
            process=process,
            brakes=brakes,
        )

    repo = FileRepository(project_root)

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

    for rule in repo.list_rules():
        if not rule.active:
            warnings.append(
                f"{rule.id}: Rule Candidate inactive — needs HUMAN Decision to activate"
            )

    if wake.change_ids and wake.index_entities == 0:
        warnings.append("Index empty despite Changes — wake rebuild may have failed")

    if process.complete and not brakes.complete:
        warnings.append(
            "Process ready but Brakes incomplete — gates may not stop incomplete work"
        )

    return DoctorReport(
        wake=wake,
        diagnostics=diagnostics,
        warnings=warnings,
        process=process,
        brakes=brakes,
    )
