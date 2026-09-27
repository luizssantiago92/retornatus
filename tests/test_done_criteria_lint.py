"""DONE-criteria lint on gate contract."""

from __future__ import annotations

from pathlib import Path

from retornatus.application.change.workflow import ChangeWorkflow
from retornatus.application.governance.gates import GateResult, gate_contract, lint_done_criteria
from retornatus.bootstrap.init import initialize_project
from retornatus.infrastructure.persistence.repository import FileRepository


def _gate(tmp_path: Path, criteria: list[str]) -> GateResult:
    initialize_project(tmp_path)
    created = ChangeWorkflow(tmp_path).create_change(
        title="Health",
        demand_statement="Add a health endpoint for ops liveness",
        situation="Ops needs GET /health. Authentication is out of scope.",
        what="GET /health returns 200",
        done_criteria=["pytest covers GET /health returns 200"],
        action_objective="Implement health",
    )
    repo = FileRepository(tmp_path)
    contract, rev = repo.load_contract(created.change.id)
    repo.save_contract(contract.model_copy(update={"done_criteria": criteria}), expected=rev)
    return gate_contract(tmp_path, created.change.id)


def test_placeholders_duplicates_and_vague_terms_fail(tmp_path: Path) -> None:
    result = _gate(
        tmp_path,
        [
            "TODO finish the endpoint",
            "Behavior is TBD",
            "Copy [NEEDS CLARIFICATION] into the contract",
            "Response matches <expected>",
            "The page is user-friendly",
            "It responds properly",
            "Make it fast",
            "Handle errors as needed",
            "Cover login, logout, etc",
            "pytest covers GET /health",
            "pytest covers GET /health",
        ],
    )
    assert result.passed is False
    text = "\n".join(result.messages)
    assert "placeholder" in text
    assert "duplicated" in text
    assert "vague" in text
    assert "TODO" in text
    assert "TBD" in text
    assert "[NEEDS CLARIFICATION]" in text
    assert "<expected>" in text


def test_missing_observable_outcome_warns_without_failing(tmp_path: Path) -> None:
    result = _gate(tmp_path, ["Policy enforceable for this change"])
    assert result.passed is True
    assert any("no observable outcome" in message for message in result.messages)
    assert any(message.startswith("WARN:") for message in result.messages)


def test_observable_criterion_stays_clean(tmp_path: Path) -> None:
    result = _gate(tmp_path, ["pytest covers GET /health returns 200"])
    assert result.passed is True
    assert result.messages == ["Contract OK"]


def test_lint_helper_flags_short_criteria() -> None:
    errors, warnings = lint_done_criteria(["ok", "works"])
    assert errors
    assert not warnings
