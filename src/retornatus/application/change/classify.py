"""Complexity lane classification — ceremony matches risk (PRD §71)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from retornatus.domain.enums import ComplexityLane, DemandKind

_COMPLEX_MARKERS = re.compile(
    r"\b(oauth|authn|authz|payment|stripe|migrate|migration|kubernetes|k8s|"
    r"terraform|security|crypto|sso|pii|gdpr|multi-tenant|breaking)\b",
    re.I,
)
_QUICK_MARKERS = re.compile(
    r"\b(typo|rename|wording|docs? only|comment|lint|format)\b",
    re.I,
)
_NON_QUICK_MARKERS = re.compile(
    r"\b(endpoint|api|database|auth|oauth|migrate|payment|test|returns)\b",
    re.I,
)


@dataclass
class LaneClassification:
    lane: ComplexityLane
    rationale: str
    recommendations: list[str] = field(default_factory=list)

    def render(self) -> str:
        lines = [
            f"lane: {self.lane.value}",
            f"rationale: {self.rationale}",
        ]
        if self.recommendations:
            lines.append("recommendations:")
            lines.extend(f"  - {r}" for r in self.recommendations)
        return "\n".join(lines)


def classify_change(
    *,
    demand: str,
    what: str = "",
    done_criteria: list[str] | None = None,
    demand_kind: DemandKind | None = None,
    task_count: int = 0,
    constraint_count: int = 0,
) -> LaneClassification:
    """
    Heuristic ceremony lane — advisory, not durable truth.

    QUICK: typo/docs-scale, few DONE criteria, no specialization markers.
    COMPLEX: security/payment/migration markers, SECURITY kind, many tasks/constraints.
    STANDARD: everything else (full Contract + gates; Skill optional).
    """
    done = done_criteria or []
    hay = " ".join([demand, what, " ".join(done)])

    recommendations: list[str] = []

    if demand_kind is DemandKind.SECURITY or _COMPLEX_MARKERS.search(hay):
        recommendations.extend(
            [
                "Use full Contract + gate contract before build",
                "Consider skill create + gate skill-research for specialized topics",
                "Prefer Claim-bound Evidence + verify; consider assurance review",
                "Run policy check / gate policy for risky effects",
            ]
        )
        return LaneClassification(
            lane=ComplexityLane.COMPLEX,
            rationale=(
                "High-risk or specialized markers (or SECURITY demand) — "
                "earn Skill, Policy, and Assurance rigor"
            ),
            recommendations=recommendations,
        )

    quickish = bool(_QUICK_MARKERS.search(hay)) or (
        len(done) <= 1
        and task_count <= 1
        and len(what) < 60
        and constraint_count == 0
        and len(demand) < 50
        and not _NON_QUICK_MARKERS.search(hay)
    )
    if quickish and demand_kind not in {DemandKind.MIGRATION, DemandKind.SECURITY}:
        recommendations.extend(
            [
                "Short Contract with clear DONE is enough",
                "skill need will usually skip specialization ceremony",
                "Still require gate contract + attributable Evidence before done",
            ]
        )
        return LaneClassification(
            lane=ComplexityLane.QUICK,
            rationale="Looks routine / low-blast-radius — keep ceremony light",
            recommendations=recommendations,
        )

    if task_count >= 4 or len(done) >= 4 or constraint_count >= 3:
        recommendations.extend(
            [
                "Declare explicit Tasks with depends/resources when needed",
                "Use loop next --all-ready for independent READY tasks",
                "skill need if specialized topics appear mid-build",
            ]
        )
        return LaneClassification(
            lane=ComplexityLane.COMPLEX,
            rationale="Many DONE criteria, tasks, or constraints — earn Task graph rigor",
            recommendations=recommendations,
        )

    recommendations.extend(
        [
            "Full Change loop: Contract → gates → Evidence → verify",
            "Tasks only when the work needs a job list",
            "Skill only when skill need says required",
        ]
    )
    return LaneClassification(
        lane=ComplexityLane.STANDARD,
        rationale="Normal feature path — Contract and gates; Skill optional",
        recommendations=recommendations,
    )
