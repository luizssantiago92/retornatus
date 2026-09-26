"""Coverage for verify receipts and Action attempt budgets."""

from __future__ import annotations

from pathlib import Path

from retornatus.application.assurance.evaluate import (
    AssuranceResult,
    AssuranceVerdict,
)
from retornatus.application.assurance.receipt import (
    load_and_verify_receipt,
    verify_receipt_dict,
    write_verify_receipt,
)
from retornatus.application.change.tasks import TaskService
from retornatus.application.change.workflow import ChangeWorkflow
from retornatus.application.governance.gates import gate_budget
from retornatus.bootstrap.init import initialize_project


def _project(tmp: Path) -> Path:
    initialize_project(tmp)
    return tmp


def test_receipt_roundtrip(tmp_path: Path) -> None:
    root = _project(tmp_path)
    result = AssuranceResult(
        verdict=AssuranceVerdict.SATISFIED,
        rationale="all claims supported",
        claim_results={"done:1": "SATISFIED"},
        evidence_ids=["C-0001/E-001"],
    )
    path = write_verify_receipt(root, "C-0001", result)
    assert path.is_file()
    ok, msg, data = load_and_verify_receipt(root, path)
    assert ok, msg
    assert data["change_id"] == "C-0001"
    assert data["verdict"] == "SATISFIED"

    tampered = dict(data)
    tampered["verdict"] = "NOT_SATISFIED"
    bad, _ = verify_receipt_dict(root, tampered)
    assert bad is False


def test_action_budget_gate(tmp_path: Path) -> None:
    root = _project(tmp_path)
    created = ChangeWorkflow(root).create_change(
        title="Budget demo",
        demand_statement="Add health",
        situation="GET /health should return 200 with tests",
        what="GET /health returns 200",
        done_criteria=["pytest covers GET /health"],
        action_objective="Implement health",
        tasks=["implement"],
    )
    assert created.action is not None
    action_id = created.action.id
    tasks = TaskService(root)
    tasks.set_max_attempts(action_id, 2)
    assert gate_budget(root, action_id).passed

    task_id = created.action.tasks[0].id
    tasks.start(task_id)
    tasks.fail(task_id)
    assert gate_budget(root, action_id).passed

    tasks.reopen(task_id)
    tasks.start(task_id)
    tasks.fail(task_id)
    assert not gate_budget(root, action_id).passed


def test_docs_html_check_script_runs() -> None:
    import subprocess
    import sys

    repo = Path(__file__).resolve().parents[1]
    proc = subprocess.run(
        [sys.executable, str(repo / "scripts" / "build_docs_html.py"), "--check"],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
