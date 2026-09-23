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

_TRIVIAL_MARKERS = re.compile(
    r"\b(typo|rename|wording|docs? only|comment|lint|format)\b",
    re.I,
)


@dataclass
class SkillNeedAssessment:
    required: bool
    rationale: str
    suggested_need: str | None = None
    source: str = "action"  # action | prompt | change


def _assess_haystack(
    hay: str,
    *,
    source: str,
    short_objective: bool = False,
    task_count: int | None = None,
) -> SkillNeedAssessment:
    if _SPECIALIZATION_MARKERS.search(hay):
        match = _SPECIALIZATION_MARKERS.search(hay)
        topic = match.group(0) if match else "specialization"
        return SkillNeedAssessment(
            required=True,
            rationale=(
                f"Text references specialized topic `{topic}` — "
                "research a current Skill (Action not required to start)"
            ),
            suggested_need=f"Current best practices for {topic} in this stack",
            source=source,
        )

    if _TRIVIAL_MARKERS.search(hay) or (
        short_objective and (task_count is None or task_count <= 2) and len(hay) < 160
    ):
        return SkillNeedAssessment(
            required=False,
            rationale=(
                "Looks routine — Environment-native skills/context suffice; "
                "skip Skill ceremony"
            ),
            source=source,
        )

    return SkillNeedAssessment(
        required=False,
        rationale="No clear specialization gap detected; Skill optional",
        source=source,
    )


def assess_skill_need(
    root: Path,
    action_id: str | None = None,
    *,
    prompt: str | None = None,
    demand: str | None = None,
    what: str | None = None,
) -> SkillNeedAssessment:
    """
    Decide whether on-demand Skill creation is warranted.

    Prefer an Action when one exists. Freeform ``prompt`` / Demand+WHAT work
    before Contract/Action — agents should propose Skills as soon as the need
    is visible, not only mid-execution.
    """
    if bool(action_id) == bool(prompt or demand or what):
        # Exactly one mode: action XOR freeform text
        if action_id and (prompt or demand or what):
            raise ValueError("Provide either action_id or prompt/demand/what, not both")
        if not action_id and not (prompt or demand or what):
            raise ValueError("Provide --action or --prompt/--demand/--what")

    if action_id:
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

        from retornatus.application.adaptation.skills import SkillService

        existing = SkillService(root).resolve_for_action(action_id)
        active = [s for s in existing if s.status.value == "ACTIVE"]
        if active:
            return SkillNeedAssessment(
                required=False,
                rationale=f"Adequate Skill already linked: {active[0].id}",
                suggested_need=None,
                source="action",
            )

        return _assess_haystack(
            hay,
            source="action",
            short_objective=len(action.objective) < 120,
            task_count=len(action.tasks),
        )

    parts = [p for p in (prompt, demand, what) if p]
    hay = " ".join(parts)
    source = "prompt" if prompt and not demand and not what else "change"
    return _assess_haystack(
        hay,
        source=source,
        short_objective=len(hay) < 120,
        task_count=0,
    )
