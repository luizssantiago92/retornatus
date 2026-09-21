"""Focused unit coverage for mid-milestones."""

from __future__ import annotations

from pathlib import Path

from retornatus.application.assurance.evaluate import Claim, AssuranceVerdict, evaluate_assurance
from retornatus.application.governance.policy import PolicyVerdict, evaluate_policy
from retornatus.bootstrap.init import initialize_project
from retornatus.bootstrap.wake import wake_up
from retornatus.domain.enums import AuthorityCategory
from retornatus.domain.models import Authority, Rule
from retornatus.infrastructure.persistence.repository import FileRepository


def test_wake_rebuilds_empty_project(tmp_path: Path) -> None:
    report = wake_up(tmp_path, auto_init=True)
    assert report.initialized
    assert "Initialized" in " ".join(report.diagnostics) or report.index_entities == 0


def test_assurance_inconclusive_without_evidence() -> None:
    result = evaluate_assurance(
        claims=[Claim(id="1", statement="x", required_evidence_types=["test_result"])],
        evidence=[],
    )
    assert result.verdict is AssuranceVerdict.INCONCLUSIVE


def test_policy_deny_must_not_rule(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    repo = FileRepository(tmp_path)
    rule = Rule(
        id="R-0001",
        statement="Do not commit secrets",
        applicability="commit secrets",
        active=True,
        authority=Authority(category=AuthorityCategory.HUMAN),
    )
    repo.save_rule(rule)
    decision = evaluate_policy(
        effect="commit secrets to repo",
        rules=repo.list_rules(),
        authority=Authority(category=AuthorityCategory.DELEGATED),
    )
    assert decision.verdict is PolicyVerdict.DENY
