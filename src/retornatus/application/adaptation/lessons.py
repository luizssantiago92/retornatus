"""Lessons from gate failures — Learning (+ optional Rule Candidate)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from retornatus.application.adaptation.service import AdaptationService
from retornatus.application.governance.gates import (
    gate_assurance,
    gate_contract,
    gate_evidence,
    gate_policy,
    gate_skill_research,
)
from retornatus.domain.models import LearningMetadata, Rule


@dataclass
class LessonResult:
    learning: LearningMetadata
    rule_candidate: Rule | None = None
    gate_passed: bool | None = None
    gate_messages: list[str] | None = None


def record_lesson_from_gate(
    root: Path,
    *,
    gate: str,
    title: str,
    note: str,
    change_id: str | None = None,
    skill_id: str | None = None,
    action_id: str | None = None,
    propose_rule: bool = False,
    recheck: bool = True,
) -> LessonResult:
    """
    Record a Learning after a failed (or inspected) gate.

    Optionally re-runs the named gate to attach current messages, and may
    propose a Rule Candidate (never auto-activates).
    """
    gate_key = gate.strip().lower().replace("_", "-")
    messages: list[str] = []
    passed: bool | None = None

    if recheck:
        if gate_key == "contract":
            if not change_id:
                raise ValueError("change_id required for gate contract")
            result = gate_contract(root, change_id)
            passed, messages = result.passed, list(result.messages)
        elif gate_key == "evidence":
            if not change_id:
                raise ValueError("change_id required for gate evidence")
            result = gate_evidence(root, change_id)
            passed, messages = result.passed, list(result.messages)
        elif gate_key in {"assurance", "verify"}:
            if not change_id:
                raise ValueError("change_id required for gate assurance")
            result = gate_assurance(root, change_id)
            passed, messages = result.passed, list(result.messages)
        elif gate_key in {"skill-research", "skill_research", "skill"}:
            if not skill_id:
                raise ValueError("skill_id required for gate skill-research")
            result = gate_skill_research(root, skill_id)
            passed, messages = result.passed, list(result.messages)
        elif gate_key == "policy":
            if not action_id:
                raise ValueError("action_id required for gate policy")
            result = gate_policy(root, action_id)
            passed, messages = result.passed, list(result.messages)
        else:
            raise ValueError(
                f"Unknown gate `{gate}`. "
                "Use: contract, evidence, assurance, skill-research, policy"
            )

    related = [x for x in (change_id, skill_id, action_id) if x]
    body_parts = [
        f"# Lesson: {title}",
        "",
        f"**Gate:** `{gate_key}`",
        f"**Passed on recheck:** {passed}",
        "",
        "## Note",
        "",
        note.strip(),
        "",
    ]
    if messages:
        body_parts.extend(["## Gate messages", ""])
        body_parts.extend(f"- {m}" for m in messages)
        body_parts.append("")
    body_parts.extend(
        [
            "## Next",
            "",
            "- Fix the artifact and re-run the gate",
            "- Or promote a Rule Candidate via Human Decision if this must constrain future work",
            "",
        ]
    )

    adaptation = AdaptationService(root)
    learning = adaptation.record_learning(
        title=title,
        body="\n".join(body_parts),
        summary=note.strip()[:200],
        tags=["gate-failure", f"gate:{gate_key}", "lesson"],
        related_ids=related,
    )

    rule: Rule | None = None
    if propose_rule:
        rule = adaptation.propose_rule_candidate(
            statement=(
                f"When `{gate_key}` fails with this pattern, stop and remediate "
                f"before claiming progress. Context: {note.strip()[:160]}"
            ),
            applicability=f"After gate `{gate_key}` failures related to {related or 'this project'}",
            from_learning_id=learning.id,
        )

    return LessonResult(
        learning=learning,
        rule_candidate=rule,
        gate_passed=passed,
        gate_messages=messages or None,
    )
