"""Complexity-sensitive Skill need — specialize only when earned."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from retornatus.infrastructure.persistence.repository import FileRepository


_SPECIALIZATION_MARKERS = re.compile(
    r"\b(oauth|stripe|kubernetes|k8s|terraform|graphql|wasm|protobuf|"
    r"kafka|redis|postgres|migrate|security|crypto|sso|webhook|"
    r"framework|sdk|protocol)\b",
    re.I,
)


@dataclass
class SkillNeedAssessment:
    required: bool
    rationale: str
    suggested_need: str | None = None


def assess_skill_need(
    root: Path,
    action_id: str,
) -> SkillNeedAssessment:
    """
    Decide whether on-demand Skill creation is warranted.

    Trivial Actions skip ceremony. Specialization keywords or missing local
    procedural knowledge justify a Skill.
    """
    repo = FileRepository(root)
    action, _ = repo.load_action(action_id)
    hay = " ".join(
        [
            action.objective,
            action.scope or "",
            " ".join(action.success_conditions),
            " ".join(action.constraints),
        ]
    )

    # Existing adequate Skill already linked?
    from retornatus.application.adaptation.skills import SkillService

    existing = SkillService(root).resolve_for_action(action_id)
    active = [s for s in existing if s.status.value == "ACTIVE"]
    if active:
        return SkillNeedAssessment(
            required=False,
            rationale=f"Adequate Skill already linked: {active[0].id}",
            suggested_need=None,
        )

    if _SPECIALIZATION_MARKERS.search(hay):
        match = _SPECIALIZATION_MARKERS.search(hay)
        topic = match.group(0) if match else "specialization"
        return SkillNeedAssessment(
            required=True,
            rationale=f"Action references specialized topic `{topic}` — research a current Skill",
            suggested_need=f"Current best practices for {topic} in this stack",
        )

    # Few tasks / short objective → trivial
    if len(action.tasks) <= 2 and len(action.objective) < 120:
        return SkillNeedAssessment(
            required=False,
            rationale=(
                "Action looks routine — Environment-native skills/context suffice; "
                "skip Skill ceremony"
            ),
        )

    return SkillNeedAssessment(
        required=False,
        rationale="No clear specialization gap detected; Skill optional",
    )
