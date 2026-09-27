"""StrEnum migration must keep persisted enum values.

``str()`` of a ``(str, Enum)`` member on Python 3.11+ is ``Class.MEMBER``.
``StrEnum`` makes ``str()`` and ``format()`` return the value. JSON already
used the value (pydantic and ``json.dumps``), so receipts and evidence stay
the same. Members whose value differs from the name are the ones that would
show a mistake.
"""

from __future__ import annotations

from retornatus.application.governance.gates import GateName
from retornatus.application.governance.policy import PolicyDecision, PolicyVerdict
from retornatus.domain.enums import EvidenceProvenance
from retornatus.domain.models import Evidence
from retornatus.domain.relations import Relation, RelationType
from retornatus.infrastructure.environment.adapters import EnvironmentKind


def test_json_and_string_forms_use_enum_values() -> None:
    evidence = Evidence(
        id="C-0001/E-001",
        type="test_result",
        subject="suite",
        source="pytest",
        producer="retornatus",
        provenance=EvidenceProvenance.SELF_REPORTED,
        relations=[Relation(type=RelationType.SUPPORTS, target_id="C-0001")],
    )
    raw = evidence.model_dump_json()
    assert '"provenance":"self_reported"' in raw
    assert '"type":"SUPPORTS"' in raw
    assert "EvidenceProvenance" not in raw
    assert "SELF_REPORTED" not in raw

    decision = PolicyDecision(verdict=PolicyVerdict.REQUIRE_HUMAN, rationale="review")
    dumped = decision.model_dump_json()
    assert '"verdict":"REQUIRE_HUMAN"' in dumped

    assert str(EvidenceProvenance.SELF_REPORTED) == "self_reported"
    assert format(EvidenceProvenance.EXECUTED) == "executed"
    assert f"{GateName.SKILL_RESEARCH}" == "skill-research"
    assert GateName.CONTRACT == "contract"
    assert str(EnvironmentKind.CLAUDE_CODE) == "claude_code"
    assert EnvironmentKind.GITHUB_COPILOT == "github_copilot"
    assert format(EvidenceProvenance.SELF_REPORTED, "") == "self_reported"
