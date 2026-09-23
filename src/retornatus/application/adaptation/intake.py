"""Prompt intake analysis — stages before Skill proposal (human-controlled).

Freeform prompt → inspect existing .retornatus state → specialization signal →
focused questions to the human → only then authorize Skill creation.

Two worlds:
- Manual: human asks for a Skill explicitly (`skill create`).
- Analyzed: agent runs ``intake analyze``; Skill is proposed, not auto-created.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from retornatus.application.adaptation.skill_need import assess_skill_need
from retornatus.application.adaptation.skills import SkillService
from retornatus.application.change.situation import load_project_context_snippet
from retornatus.domain.enums import SkillStatus
from retornatus.domain.models import Skill
from retornatus.infrastructure.persistence.repository import FileRepository

MAX_INTAKE_QUESTIONS = 4


class IntakeVerdict(str, Enum):
    """Outcome of prompt intake (Skill path)."""

    ROUTINE = "ROUTINE"
    REUSE_SKILL = "REUSE_SKILL"
    PROPOSE_SKILL = "PROPOSE_SKILL"
    CREATE_SKILL = "CREATE_SKILL"


@dataclass
class IntakeQuestion:
    topic: str
    question: str
    why_material: str
    options: list[str] = field(default_factory=list)


@dataclass
class IntakeAnalysis:
    prompt: str
    stages: list[str] = field(default_factory=list)
    known_facts: list[str] = field(default_factory=list)
    existing_skill_ids: list[str] = field(default_factory=list)
    skill_need_required: bool = False
    suggested_need: str | None = None
    verdict: IntakeVerdict = IntakeVerdict.ROUTINE
    focused_questions: list[IntakeQuestion] = field(default_factory=list)
    rationale: str = ""
    create_authorized: bool = False

    def to_markdown(self) -> str:
        lines = [
            "# Prompt intake",
            "",
            "## Prompt",
            "",
            self.prompt.strip(),
            "",
            "## Stages checked",
            "",
        ]
        lines.extend(f"- {s}" for s in self.stages)
        lines.extend(["", "## Known facts", ""])
        if self.known_facts:
            lines.extend(f"- {f}" for f in self.known_facts)
        else:
            lines.append("- (none)")
        lines.extend(
            [
                "",
                "## Skill signal",
                "",
                f"- required={self.skill_need_required}",
            ]
        )
        if self.suggested_need:
            lines.append(f"- suggested_need={self.suggested_need}")
        if self.existing_skill_ids:
            lines.append(
                "- existing_skills: " + ", ".join(self.existing_skill_ids)
            )
        lines.extend(
            [
                "",
                f"## Verdict: `{self.verdict.value}`",
                "",
                self.rationale,
                "",
            ]
        )
        if self.focused_questions:
            lines.append("## Focused questions (human)")
            lines.append("")
            lines.append(
                "_Answer these before creating a Skill "
                f"(at most {MAX_INTAKE_QUESTIONS})._"
            )
            lines.append("")
            for i, q in enumerate(self.focused_questions, start=1):
                lines.append(f"{i}. **[{q.topic}]** {q.question}")
                lines.append(f"   - Why material: {q.why_material}")
                if q.options:
                    lines.append("   - Options:")
                    for opt in q.options:
                        lines.append(f"     - {opt}")
                lines.append("")
            lines.append(
                "Record answers: `retornatus intake analyze --prompt \"…\" "
                "--answer \"TOPIC=…\"` (repeat `--answer`)."
            )
            lines.append("")
        if self.create_authorized:
            lines.extend(
                [
                    "## Next",
                    "",
                    "Human confirmed Skill creation. Run with `--create-skill` "
                    "or `skill create --need \"…\"`.",
                    "",
                ]
            )
        elif self.verdict is IntakeVerdict.REUSE_SKILL:
            lines.extend(
                [
                    "## Next",
                    "",
                    "Reuse an existing Skill — do not create a duplicate.",
                    "",
                ]
            )
        elif self.verdict is IntakeVerdict.ROUTINE:
            lines.extend(
                [
                    "## Next",
                    "",
                    "No Skill ceremony — proceed with Situation/Contract as needed.",
                    "",
                ]
            )
        return "\n".join(lines)


def _token_overlap(a: str, b: str) -> bool:
    ta = {t for t in re.findall(r"[a-z0-9_]{3,}", a.lower())}
    tb = {t for t in re.findall(r"[a-z0-9_]{3,}", b.lower())}
    return bool(ta & tb)


def _matching_skills(root: Path, prompt: str) -> list[str]:
    svc = SkillService(root)
    matched: list[str] = []
    for skill in FileRepository(root).list_skills():
        if skill.status is SkillStatus.SUPERSEDED:
            continue
        hay = " ".join(
            [
                skill.title,
                skill.description or "",
                skill.specialization or "",
                skill.name,
            ]
        )
        if _token_overlap(prompt, hay):
            matched.append(f"{skill.id}({skill.status.value})")
    # Also relevance helper
    for skill in svc.resolve_relevant(prompt, limit=5):
        label = f"{skill.id}({skill.status.value})"
        if label not in matched:
            matched.append(label)
    return matched[:8]


def analyze_prompt_intake(
    root: Path,
    prompt: str,
    *,
    answers: dict[str, str] | None = None,
) -> IntakeAnalysis:
    """
    Run intake stages over a freeform prompt.

    Does **not** create Skills. Human answers (and optional ``--create-skill``)
    authorize creation.
    """
    text = (prompt or "").strip()
    if not text:
        raise ValueError("prompt must not be empty")

    stages: list[str] = []
    facts: list[str] = []

    stages.append("1. Capture freeform prompt")
    facts.append(f"Prompt length={len(text)} chars")

    stages.append("2. Inspect project continuity notes")
    excerpt = load_project_context_snippet(root, max_chars=400)
    if excerpt:
        facts.append("project.md present — Situation/context available")
    else:
        facts.append("No project.md yet — consider project-init for brownfield")

    stages.append("3. Scan existing Skills under .retornatus/adaptation/skills/")
    existing = _matching_skills(root, text)
    if existing:
        facts.append("Possible Skill overlap: " + ", ".join(existing))
    else:
        facts.append("No overlapping Skills found")

    stages.append("4. Complexity-sensitive specialization signal (skill need)")
    need = assess_skill_need(root, prompt=text)
    facts.append(need.rationale)

    stages.append("5. Decide Skill path (propose vs reuse vs routine)")

    analysis = IntakeAnalysis(
        prompt=text,
        stages=stages,
        known_facts=facts,
        existing_skill_ids=existing,
        skill_need_required=need.required,
        suggested_need=need.suggested_need,
    )

    active_overlap = [s for s in existing if "(ACTIVE)" in s]
    if active_overlap and need.required:
        analysis.verdict = IntakeVerdict.REUSE_SKILL
        analysis.rationale = (
            "Specialization markers present, but an ACTIVE Skill already overlaps — "
            "reuse before creating another"
        )
        analysis.focused_questions = [
            IntakeQuestion(
                topic="REUSE",
                question=(
                    "Confirm reuse of existing Skill "
                    f"{active_overlap[0].split('(')[0]} instead of creating a new one?"
                ),
                why_material="Duplicate Skills rot; prefer one researched specialization",
                options=[
                    "yes — reuse existing",
                    "no — still create a new Skill (justify)",
                ],
            )
        ]
    elif need.required:
        analysis.verdict = IntakeVerdict.PROPOSE_SKILL
        analysis.rationale = (
            "Prompt appears to require specialization the agent should research. "
            "Ask the human before creating a Skill."
        )
        analysis.focused_questions = [
            IntakeQuestion(
                topic="SPECIALIZATION",
                question=(
                    "Does this work need a researched specialization Skill "
                    f"(suggested: {need.suggested_need or 'current best practices'})?"
                ),
                why_material=(
                    "Skill ceremony has cost — only earn it when Environment-native "
                    "context is not enough"
                ),
                options=[
                    "yes — create a Skill",
                    "no — Environment context is enough",
                    "unsure — ask one clarifying question first",
                ],
            ),
            IntakeQuestion(
                topic="NEED",
                question="What specialization should the Skill encode (one sentence)?",
                why_material="Skill title/need must be concrete for RESEARCH",
                options=[],
            ),
            IntakeQuestion(
                topic="CREATE",
                question="Authorize creating a DRAFT Skill now?",
                why_material="Human control — agents must not invent Skills silently",
                options=[
                    "yes — create DRAFT now",
                    "not yet — only Situation/Contract for now",
                ],
            ),
        ][:MAX_INTAKE_QUESTIONS]
    else:
        analysis.verdict = IntakeVerdict.ROUTINE
        analysis.rationale = (
            "No clear specialization gap — skip Skill ceremony; "
            "use Situation/Contract if requirements are still open"
        )

    if answers:
        analysis = apply_intake_answers(analysis, answers)

    return analysis


def apply_intake_answers(
    analysis: IntakeAnalysis,
    answers: dict[str, str],
) -> IntakeAnalysis:
    """Fold human answers into the intake verdict (does not persist)."""
    updated = IntakeAnalysis(
        prompt=analysis.prompt,
        stages=list(analysis.stages) + ["6. Apply human answers"],
        known_facts=list(analysis.known_facts),
        existing_skill_ids=list(analysis.existing_skill_ids),
        skill_need_required=analysis.skill_need_required,
        suggested_need=analysis.suggested_need,
        verdict=analysis.verdict,
        focused_questions=list(analysis.focused_questions),
        rationale=analysis.rationale,
        create_authorized=False,
    )

    normalized = {k.upper(): v.strip() for k, v in answers.items()}

    for topic, answer in normalized.items():
        updated.known_facts.append(f"Answer[{topic}]={answer}")

    create = normalized.get("CREATE", "")
    spec = normalized.get("SPECIALIZATION", "")
    need_ans = normalized.get("NEED", "")
    reuse = normalized.get("REUSE", "")

    if need_ans:
        updated.suggested_need = need_ans

    create_yes = bool(re.search(r"\byes\b", create, re.I))
    create_no = bool(re.search(r"\bnot yet\b|\bno\b", create, re.I))
    spec_yes = bool(re.search(r"\byes\b", spec, re.I))
    spec_no = bool(re.search(r"\bno\b", spec, re.I))
    reuse_yes = bool(re.search(r"\byes\b", reuse, re.I))
    reuse_no = bool(re.search(r"\bno\b", reuse, re.I))

    if reuse_yes and not reuse_no:
        updated.verdict = IntakeVerdict.REUSE_SKILL
        updated.create_authorized = False
        updated.focused_questions = []
        updated.rationale = "Human confirmed reuse of an existing Skill"
        return updated

    if reuse_no and create_yes:
        # Force new skill path after rejecting reuse
        updated.verdict = IntakeVerdict.CREATE_SKILL
        updated.create_authorized = True
        updated.focused_questions = []
        updated.rationale = "Human rejected reuse and authorized a new DRAFT Skill"
        return updated

    if spec_no and not create_yes:
        updated.verdict = IntakeVerdict.ROUTINE
        updated.create_authorized = False
        updated.focused_questions = []
        updated.rationale = "Human declined Skill ceremony — proceed without Skill"
        return updated

    if create_yes and (spec_yes or not spec or need_ans):
        updated.verdict = IntakeVerdict.CREATE_SKILL
        updated.create_authorized = True
        updated.focused_questions = []
        updated.rationale = (
            "Human authorized DRAFT Skill creation after intake questions"
        )
        return updated

    if create_no:
        updated.verdict = IntakeVerdict.PROPOSE_SKILL
        updated.create_authorized = False
        updated.rationale = "Skill still proposed, but creation deferred by human"
        updated.focused_questions = [
            q for q in analysis.focused_questions if q.topic.upper() not in normalized
        ]
        return updated

    # Partial answers — keep unanswered questions
    answered = {t.upper() for t in normalized}
    updated.focused_questions = [
        q for q in analysis.focused_questions if q.topic.upper() not in answered
    ]
    if not updated.focused_questions and updated.skill_need_required:
        if create_yes:
            updated.verdict = IntakeVerdict.CREATE_SKILL
            updated.create_authorized = True
            updated.rationale = "All intake questions answered — create authorized"
        else:
            updated.verdict = IntakeVerdict.PROPOSE_SKILL
            updated.rationale = "Questions answered; CREATE not authorized yet"
    else:
        updated.verdict = IntakeVerdict.PROPOSE_SKILL
        updated.rationale = "Awaiting remaining human answers before Skill creation"

    return updated


def create_skill_from_intake(
    root: Path,
    analysis: IntakeAnalysis,
    *,
    change_id: str | None = None,
    action_id: str | None = None,
) -> Skill:
    """Create a DRAFT Skill only when intake authorized creation."""
    if not analysis.create_authorized:
        raise ValueError(
            "Skill creation not authorized — complete intake answers "
            "(CREATE=yes) first"
        )
    need = analysis.suggested_need or (
        f"Specialization for: {analysis.prompt[:120]}"
    )
    skill, _ = SkillService(root).create_for_specialization(
        specialization=need,
        title=need if len(need) < 80 else need[:77] + "…",
        change_id=change_id,
        action_id=action_id,
    )
    return skill
