"""Governed bypass: reason, authority, and paired Decision."""

from __future__ import annotations

from pathlib import Path

import pytest

from retornatus.application.governance.bypass import BypassError, BypassService
from retornatus.bootstrap.init import initialize_project
from retornatus.domain.enums import AuthorityCategory, DecisionKind
from retornatus.domain.models import Authority, Decision
from retornatus.domain.relations import RelationType
from retornatus.infrastructure.persistence.repository import FileRepository


def test_bypass_requires_a_real_reason(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    service = BypassService(tmp_path)
    with pytest.raises(BypassError):
        service.record_bypass(gate="skill-research", entity_id="S-0001", reason="")
    with pytest.raises(BypassError):
        service.record_bypass(gate="skill-research", entity_id="S-0001", reason="   ")


def test_human_bypass_records_a_paired_decision(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    service = BypassService(tmp_path)
    record = service.record_bypass(
        gate="skill-research",
        entity_id="S-0001",
        reason="Research deferred for a hotfix",
    )
    assert record.id == "B-0001"
    assert record.decision_id == "D-0001"
    assert record.authority.category is AuthorityCategory.HUMAN
    assert record.relations[0].type is RelationType.APPLIES_TO
    assert record.relations[0].target_id == "S-0001"

    decision, _ = FileRepository(tmp_path).load_decision("D-0001")
    assert decision.kind is DecisionKind.GOVERNANCE_BYPASS
    assert decision.subject_id == "S-0001"
    assert decision.confirmation_token == "S-0001"

    second = service.record_bypass(
        gate="skill-research",
        entity_id="S-0002",
        reason="Second bypass",
    )
    assert second.id == "B-0002"
    assert second.decision_id == "D-0002"


def test_delegated_bypass_needs_rationale_and_skips_auto_decision(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    service = BypassService(tmp_path)
    with pytest.raises(BypassError):
        service.record_bypass(
            gate="policy",
            entity_id="C-0001/A-001",
            reason="owner asked",
            authority=Authority(category=AuthorityCategory.DELEGATED, rationale="  "),
        )
    record = service.record_bypass(
        gate="policy",
        entity_id="C-0001/A-001",
        reason="owner asked",
        authority=Authority(
            category=AuthorityCategory.DELEGATED,
            rationale="Standing delegation for local experiments",
        ),
    )
    assert record.decision_id is None
    assert record.authority.category is AuthorityCategory.DELEGATED
    assert FileRepository(tmp_path).list_decisions() == []


def test_ruled_authority_cannot_bypass(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    with pytest.raises(BypassError):
        BypassService(tmp_path).record_bypass(
            gate="assurance",
            entity_id="C-0001",
            reason="rules say so",
            authority=Authority(category=AuthorityCategory.RULED, rationale="no"),
        )


def test_existing_decision_must_match_gate_subject(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    repo = FileRepository(tmp_path)
    repo.save_decision(
        Decision(
            id="D-0007",
            kind=DecisionKind.OTHER,
            subject_id="S-0001",
            summary="Not a bypass",
            authority=Authority(category=AuthorityCategory.HUMAN),
            confirmation_token="not-checked-for-other",
        )
    )
    service = BypassService(tmp_path)
    with pytest.raises(BypassError):
        service.record_bypass(
            gate="skill-research",
            entity_id="S-0001",
            reason="use the other decision",
            decision_id="D-0007",
        )

    repo.save_decision(
        Decision(
            id="D-0008",
            kind=DecisionKind.GOVERNANCE_BYPASS,
            subject_id="S-0009",
            summary="Wrong subject",
            authority=Authority(category=AuthorityCategory.HUMAN),
            confirmation_token="S-0009",
        )
    )
    with pytest.raises(BypassError):
        service.record_bypass(
            gate="skill-research",
            entity_id="S-0001",
            reason="subject mismatch",
            decision_id="D-0008",
        )

    repo.save_decision(
        Decision(
            id="D-0009",
            kind=DecisionKind.GOVERNANCE_BYPASS,
            subject_id="S-0001",
            summary="Approved bypass",
            authority=Authority(category=AuthorityCategory.HUMAN),
            confirmation_token="S-0001",
        )
    )
    record = service.record_bypass(
        gate="skill-research",
        entity_id="S-0001",
        reason="use the recorded decision",
        decision_id="D-0009",
    )
    assert record.decision_id == "D-0009"
    assert len(repo.list_decisions()) == 3


def test_next_id_ignores_malformed_bypass_ids(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    initialize_project(tmp_path)
    service = BypassService(tmp_path)

    class _Legacy:
        def __init__(self, bypass_id: str) -> None:
            self.id = bypass_id

    monkeypatch.setattr(
        service.repo,
        "list_bypasses",
        lambda: [_Legacy("B-nope"), _Legacy("plain"), _Legacy("B-0004")],
    )
    assert service.next_bypass_id() == "B-0005"


def test_missing_decision_id_is_not_found(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    with pytest.raises(FileNotFoundError):
        BypassService(tmp_path).record_bypass(
            gate="skill-research",
            entity_id="S-0001",
            reason="missing decision",
            decision_id="D-4040",
        )
