"""Path-level Evidence freshness, isolation Boundaries, Host Execution records."""

from __future__ import annotations

from pathlib import Path

from retornatus.application.assurance.evaluate import (
    AssuranceVerdict,
    Claim,
    evaluate_assurance,
    evidence_is_fresh,
)
from retornatus.application.assurance.evidence import EvidenceService
from retornatus.application.assurance.subject_state import (
    derive_current_subject_states,
    format_commit_state,
    git_commit_for_path,
    resolve_subject_commit,
)
from retornatus.application.change.workflow import ChangeWorkflow
from retornatus.application.execution.brownfield_fixture import (
    git_commit_all,
    seed_brownfield_service,
)
from retornatus.application.execution.context import assemble_execution_context
from retornatus.application.execution.host_record import HostExecutionService
from retornatus.bootstrap.init import initialize_project
from retornatus.bootstrap.wake import wake_up
from retornatus.domain.enums import DemandKind


def test_path_level_freshness_isolated_from_unrelated_commits(tmp_path: Path) -> None:
    seed_brownfield_service(tmp_path, init_git=True)
    initialize_project(tmp_path)
    created = ChangeWorkflow(tmp_path).create_change(
        title="Docs",
        demand_statement="Document overview",
        demand_kind=DemandKind.CAPABILITY,
        situation="Docs already exist",
        what="Keep docs/overview.md accurate",
        done_criteria=["docs/overview.md reviewed in repository"],
        action_objective="Observe docs",
    )
    cid = created.change.id
    claim_id = f"{cid}/claim-done-1"

    EvidenceService(tmp_path).add(
        change_id=cid,
        evidence_type="repository_observation",
        subject="docs/overview.md",
        source="filesystem",
        producer="test",
        supports_claim_id=claim_id,
        capture_git=True,
    )
    docs_sha = git_commit_for_path(tmp_path, tmp_path / "docs" / "overview.md")
    assert docs_sha

    # Unrelated change to app/main.py should NOT stale docs Evidence
    (tmp_path / "app" / "main.py").write_text(
        '"""Acme service entrypoints."""\n\n'
        "def version() -> dict:\n"
        '    return {"service": "acme", "version": "0.2.0"}\n',
        encoding="utf-8",
    )
    git_commit_all(tmp_path, "Unrelated app bump")

    evidence = EvidenceService(tmp_path).list_for_change(cid)
    states = derive_current_subject_states(tmp_path, evidence)
    assert states["docs/overview.md"] == format_commit_state(docs_sha)
    assert evidence_is_fresh(evidence[0], current_subject_states=states)

    result = evaluate_assurance(
        claims=[
            Claim(
                id=claim_id,
                statement="docs/overview.md reviewed in repository",
                required_evidence_types=["repository_observation"],
                subject="docs/overview.md",
            )
        ],
        evidence=evidence,
        current_subject_states=states,
    )
    assert result.verdict is AssuranceVerdict.SATISFIED

    # Changing the documented file itself must stale prior Evidence
    (tmp_path / "docs" / "overview.md").write_text(
        "# Overview\n\nUpdated.\n", encoding="utf-8"
    )
    git_commit_all(tmp_path, "Update docs")
    evidence2 = EvidenceService(tmp_path).list_for_change(cid)
    states2 = derive_current_subject_states(tmp_path, evidence2)
    assert not evidence_is_fresh(evidence2[0], current_subject_states=states2)


def test_isolation_boundaries_project_native_capabilities(tmp_path: Path) -> None:
    seed_brownfield_service(tmp_path, init_git=True)
    initialize_project(tmp_path)
    created = ChangeWorkflow(tmp_path).create_change(
        title="Iso",
        demand_statement="Exercise isolation boundaries",
        situation="Need native worktree guidance",
        what="Context includes prefer-native-worktree",
        done_criteria=["ExecutionContext exposes isolation Boundaries"],
        action_objective="Assemble context",
    )
    assert created.action is not None
    ctx = assemble_execution_context(tmp_path, created.action.id)
    names = {b.name for b in ctx.boundaries.items}
    assert "prefer-native-worktree" in names
    assert "native_worktrees" in ctx.environment_capabilities

    wake = wake_up(tmp_path, auto_init=False)
    assert wake.capabilities.details.get("native_worktrees") == "true"


def test_host_execution_record(tmp_path: Path) -> None:
    seed_brownfield_service(tmp_path, init_git=True)
    initialize_project(tmp_path)
    created = ChangeWorkflow(tmp_path).create_change(
        title="Host",
        demand_statement="Record host execution",
        situation="Host implements work",
        what="HostExecutionRecord persisted under runtime/executions",
        done_criteria=["Host execution record exists for Action"],
        action_objective="Implement via host",
    )
    assert created.action is not None
    svc = HostExecutionService(tmp_path)
    record = svc.record(
        action_id=created.action.id,
        summary="Host applied health endpoint changes",
        ok=True,
        artifact_paths=["app/main.py", "tests/test_health.py"],
        capture_git=True,
    )
    assert record.id.startswith("X-")
    assert record.subject_state and record.subject_state.startswith("commit:")
    listed = svc.list_for_action(created.action.id)
    assert len(listed) == 1
    assert (
        tmp_path / ".retornatus" / "runtime" / "executions" / f"{record.id}.json"
    ).is_file()


def test_resolve_subject_commit_prefers_path(tmp_path: Path) -> None:
    seed_brownfield_service(tmp_path, init_git=True)
    sha = resolve_subject_commit(tmp_path, "docs/overview.md")
    assert sha == git_commit_for_path(tmp_path, tmp_path / "docs" / "overview.md")
