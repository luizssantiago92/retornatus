"""Operational loops — recurring repo hygiene (not Change construction)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from retornatus.bootstrap.doctor import run_doctor
from retornatus.bootstrap.wake import wake_up
from retornatus.infrastructure.persistence.repository import FileRepository


@dataclass
class OpsLoop:
    id: str
    title: str
    description: str
    steps: list[str] = field(default_factory=list)


@dataclass
class OpsLoopResult:
    loop_id: str
    ok: bool
    output: str


Runner = Callable[[Path], OpsLoopResult]


def _run_doctor(root: Path) -> OpsLoopResult:
    report = run_doctor(root)
    return OpsLoopResult(
        loop_id="doctor-hygiene",
        ok=report.ok,
        output=report.render(),
    )


def _run_wake_index(root: Path) -> OpsLoopResult:
    report = wake_up(root, ensure_bridges=False, auto_init=False)
    return OpsLoopResult(
        loop_id="wake-index",
        ok=report.initialized and not report.diagnostics,
        output=report.render(),
    )


def _run_list_drafts(root: Path) -> OpsLoopResult:
    repo = FileRepository(root)
    lines = ["# Draft contracts and inactive rules", ""]
    drafts = 0
    for cid in repo.list_change_ids():
        try:
            contract, _ = repo.load_contract(cid)
        except FileNotFoundError:
            lines.append(f"- {cid}: missing contract.json")
            drafts += 1
            continue
        if not contract.active:
            lines.append(f"- {cid}: draft contract v{contract.version}")
            drafts += 1
    for rule in repo.list_rules():
        if not rule.active:
            lines.append(f"- {rule.id}: inactive Rule Candidate")
            drafts += 1
    if drafts == 0:
        lines.append("(none)")
    return OpsLoopResult(loop_id="list-drafts", ok=True, output="\n".join(lines))


def _run_gate_scan(root: Path) -> OpsLoopResult:
    from retornatus.application.governance.gates import gate_contract

    repo = FileRepository(root)
    lines = ["# Active contract gate scan", ""]
    ok = True
    scanned = 0
    for cid in repo.list_change_ids():
        try:
            contract, _ = repo.load_contract(cid)
        except FileNotFoundError:
            continue
        if not contract.active:
            continue
        scanned += 1
        result = gate_contract(root, cid)
        status = "PASS" if result.passed else "FAIL"
        if not result.passed:
            ok = False
        msg = "; ".join(result.messages) if result.messages else "-"
        lines.append(f"{cid}: {status} - {msg}")
    if scanned == 0:
        lines.append("(no active contracts)")
    return OpsLoopResult(loop_id="gate-scan", ok=ok, output="\n".join(lines))


_CATALOG: dict[str, OpsLoop] = {
    "doctor-hygiene": OpsLoop(
        id="doctor-hygiene",
        title="Doctor hygiene",
        description="Continuity + Process/Brakes readiness + governance warnings",
        steps=["retornatus doctor"],
    ),
    "wake-index": OpsLoop(
        id="wake-index",
        title="Wake / rebuild index",
        description="Reconstruct continuity and rebuild derived FTS index",
        steps=["retornatus wake"],
    ),
    "list-drafts": OpsLoop(
        id="list-drafts",
        title="List drafts",
        description="Draft Contracts and inactive Rule Candidates needing attention",
        steps=["scan .retornatus/changes/*/contract.json", "scan governance/rules"],
    ),
    "gate-scan": OpsLoop(
        id="gate-scan",
        title="Gate scan",
        description="Run gate contract on every active Contract",
        steps=["retornatus gate contract <C-id> for each active contract"],
    ),
}

_RUNNERS: dict[str, Runner] = {
    "doctor-hygiene": _run_doctor,
    "wake-index": _run_wake_index,
    "list-drafts": _run_list_drafts,
    "gate-scan": _run_gate_scan,
}


def list_ops_loops() -> list[OpsLoop]:
    return list(_CATALOG.values())


def show_ops_loop(loop_id: str) -> OpsLoop:
    if loop_id not in _CATALOG:
        known = ", ".join(sorted(_CATALOG))
        raise ValueError(f"Unknown ops loop `{loop_id}`. Known: {known}")
    return _CATALOG[loop_id]


def run_ops_loop(root: Path, loop_id: str) -> OpsLoopResult:
    if loop_id not in _RUNNERS:
        known = ", ".join(sorted(_RUNNERS))
        raise ValueError(f"Unknown ops loop `{loop_id}`. Known: {known}")
    return _RUNNERS[loop_id](root.resolve())
