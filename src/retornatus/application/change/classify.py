"""Complexity lane classification — ceremony matches risk (PRD §71)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from retornatus.domain.enums import ComplexityLane, DemandKind

# Diff size bands. Sensitive paths use the same globs as ``gate scope``.
SMALL_FILE_MAX = 3
SMALL_LINE_MAX = 80
LARGE_FILE_MIN = 15
LARGE_LINE_MIN = 400

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


@dataclass(frozen=True)
class DiffSignals:
    """Size and sensitivity of ``git diff base...HEAD``."""

    file_count: int
    lines_changed: int
    sensitive_paths: list[str] = field(default_factory=list)

    def render(self) -> str:
        sensitive = ", ".join(self.sensitive_paths) if self.sensitive_paths else "none"
        return f"{self.file_count} files, {self.lines_changed} lines changed, sensitive: {sensitive}"


def _diff_is_small(diff: DiffSignals) -> bool:
    return diff.file_count <= SMALL_FILE_MAX and diff.lines_changed <= SMALL_LINE_MAX


def _diff_is_large(diff: DiffSignals) -> bool:
    return diff.file_count >= LARGE_FILE_MIN or diff.lines_changed >= LARGE_LINE_MIN


def collect_diff_signals(root: Path, base: str) -> DiffSignals:
    """Count files and changed lines, and flag scope-gate sensitive paths."""
    from retornatus.application.governance.diff import changed_paths, require_ref, run_git
    from retornatus.application.governance.globs import glob_match
    from retornatus.application.governance.scope import load_scope_settings

    require_ref(root, base)
    paths = changed_paths(root, base=base)
    completed = run_git(root, ["diff", "--numstat", f"{base}...HEAD"])
    lines_changed = 0
    if completed.returncode == 0:
        for line in completed.stdout.splitlines():
            parts = line.split("\t")
            if len(parts) < 3:
                continue
            added, deleted = parts[0], parts[1]
            if added.isdigit():
                lines_changed += int(added)
            if deleted.isdigit():
                lines_changed += int(deleted)
    settings = load_scope_settings(root)
    sensitive = [path for path in paths if any(glob_match(path, pattern) for pattern in settings.sensitive_globs)]
    return DiffSignals(
        file_count=len(paths),
        lines_changed=lines_changed,
        sensitive_paths=sensitive,
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
    diff: DiffSignals | None = None,
) -> LaneClassification:
    """
    Heuristic ceremony lane — advisory, not durable truth.

    QUICK: typo/docs-scale, few DONE criteria, no specialization markers,
    and (when a diff is supplied) a small non-sensitive diff.
    COMPLEX: security/payment/migration markers, SECURITY kind, sensitive
    paths from the scope-gate globs, a large diff, or many tasks/constraints.
    STANDARD: everything else (full Contract + gates; Skill optional).

    Text heuristics and diff signals combine: a typo that touches a sensitive
    path or a large diff is not QUICK.
    """
    done = done_criteria or []
    hay = " ".join([demand, what, " ".join(done)])
    diff_note = f" ({diff.render()})" if diff is not None else ""

    recommendations: list[str] = []

    if demand_kind is DemandKind.SECURITY or _COMPLEX_MARKERS.search(hay):
        recommendations.extend(
            [
                "Use full Contract + gate contract before build",
                "Propose skill need --prompt early (Action optional) + gate skill-research",
                "Prefer Claim-bound Evidence + verify; consider assurance review",
                "Run policy check / gate policy for risky effects",
            ]
        )
        return LaneClassification(
            lane=ComplexityLane.COMPLEX,
            rationale=(
                "High-risk or specialized markers (or SECURITY demand) — "
                "earn Skill, Policy, and Assurance rigor" + diff_note
            ),
            recommendations=recommendations,
        )

    if diff is not None and diff.sensitive_paths:
        recommendations.extend(
            [
                "Use full Contract + gate contract before build",
                "Run gate scope against the same base; sensitive paths need review evidence",
                "Prefer Claim-bound Evidence + verify",
            ]
        )
        return LaneClassification(
            lane=ComplexityLane.COMPLEX,
            rationale="Diff touches scope-gate sensitive paths" + diff_note,
            recommendations=recommendations,
        )

    if diff is not None and _diff_is_large(diff):
        recommendations.extend(
            [
                "Declare explicit Tasks with depends/resources when needed",
                "Run gate scope so the diff stays inside declared resources",
                "Prefer Claim-bound Evidence + verify",
            ]
        )
        return LaneClassification(
            lane=ComplexityLane.COMPLEX,
            rationale="Diff is large enough to earn full ceremony" + diff_note,
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
    diff_allows_quick = diff is None or _diff_is_small(diff)
    if quickish and diff_allows_quick and demand_kind not in {DemandKind.MIGRATION, DemandKind.SECURITY}:
        recommendations.extend(
            [
                "Short Contract with clear DONE is enough",
                "skill need will usually skip specialization ceremony",
                "Still require gate contract + attributable Evidence before done",
            ]
        )
        return LaneClassification(
            lane=ComplexityLane.QUICK,
            rationale="Looks routine / low-blast-radius — keep ceremony light" + diff_note,
            recommendations=recommendations,
        )

    if task_count >= 4 or len(done) >= 4 or constraint_count >= 3:
        recommendations.extend(
            [
                "Declare explicit Tasks with depends/resources when needed",
                "Use loop next --all-ready for independent READY tasks",
                "skill need --prompt as soon as specialized topics appear (not only mid-Action)",
            ]
        )
        return LaneClassification(
            lane=ComplexityLane.COMPLEX,
            rationale="Many DONE criteria, tasks, or constraints — earn Task graph rigor" + diff_note,
            recommendations=recommendations,
        )

    recommendations.extend(
        [
            "Full Change loop: Contract → gates → Evidence → verify",
            "Tasks only when the work needs a job list",
            "Skill only when skill need says required (prompt or Action)",
        ]
    )
    standard_why = "Normal feature path — Contract and gates; Skill optional"
    if diff is not None and quickish and not diff_allows_quick:
        standard_why = "Text looks small, but the diff is wider than a quick fix"
    return LaneClassification(
        lane=ComplexityLane.STANDARD,
        rationale=standard_why + diff_note,
        recommendations=recommendations,
    )
