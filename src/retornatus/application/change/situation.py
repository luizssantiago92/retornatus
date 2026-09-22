"""Situation elicitation — Demand → inspect context → ambiguities → Contract readiness.

Not a RequirementsEngine: a ChangeWorkflow-adjacent process (PRD §11).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from retornatus.bootstrap.project_init import (
    architecture_clues,
    detect_ci,
    detect_tests,
)
from retornatus.infrastructure.persistence.paths import RetornatusPaths


@dataclass
class FocusedQuestion:
    """A material uncertainty that can change the Contract."""

    topic: str
    question: str
    why_material: str


@dataclass
class SituationAssessment:
    """Structured Situation understanding before Contract formalization."""

    known_facts: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    ambiguities: list[str] = field(default_factory=list)
    missing_decisions: list[str] = field(default_factory=list)
    focused_questions: list[FocusedQuestion] = field(default_factory=list)
    sufficient_for_contract: bool = False
    rationale: str = ""
    repo_signals: list[str] = field(default_factory=list)

    def to_markdown(self, *, demand: str, project_notes: str | None = None) -> str:
        lines = [
            "# Situation",
            "",
            "## Demand",
            "",
            demand.strip(),
            "",
        ]
        if project_notes:
            lines.extend(["## Project context", "", project_notes.strip(), ""])
        if self.repo_signals:
            lines.extend(
                [
                    "## Repo signals (inferred)",
                    "",
                    *[f"- {s}" for s in self.repo_signals],
                    "",
                ]
            )
        sections = [
            ("Known facts", self.known_facts),
            ("Constraints", self.constraints),
            ("Assumptions", self.assumptions),
            ("Ambiguities", self.ambiguities),
            ("Missing decisions", self.missing_decisions),
        ]
        for title, items in sections:
            lines.append(f"## {title}")
            lines.append("")
            if items:
                lines.extend(f"- {item}" for item in items)
            else:
                lines.append("- (none)")
            lines.append("")
        if self.focused_questions:
            lines.append("## Focused questions")
            lines.append("")
            for q in self.focused_questions:
                lines.append(
                    f"- **{q.topic}**: {q.question} _(material: {q.why_material})_"
                )
            lines.append("")
        lines.extend(
            [
                "## Contract readiness",
                "",
                f"- Sufficient: **{'yes' if self.sufficient_for_contract else 'no'}**",
                f"- Rationale: {self.rationale}",
                "",
            ]
        )
        return "\n".join(lines)


def load_project_context_snippet(root: Path, *, max_chars: int = 2000) -> str:
    """Load brownfield project.md when present — light, not a semantic index."""
    path = RetornatusPaths(root).project_md
    if not path.is_file():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace").strip()
    if len(text) > max_chars:
        return text[: max_chars - 20].rstrip() + "\n\n…(truncated)"
    return text


def collect_repo_signals(root: Path) -> list[str]:
    """
    Lightweight brownfield signals for Situation — prefer inference over questions.

    Does not build a semantic code index.
    """
    root = root.resolve()
    signals: list[str] = []
    manifests = [
        name
        for name in (
            "pyproject.toml",
            "package.json",
            "Cargo.toml",
            "go.mod",
            "pom.xml",
            "requirements.txt",
        )
        if (root / name).exists()
    ]
    if manifests:
        signals.append("stack manifests: " + ", ".join(f"`{m}`" for m in manifests))
    tests = detect_tests(root)
    if tests:
        signals.append("tests: " + ", ".join(tests))
    ci = detect_ci(root)
    if ci:
        signals.append("ci: " + ", ".join(f"`{c}`" for c in ci))
    arch = architecture_clues(root)
    if arch:
        signals.append("architecture: " + "; ".join(arch))
    for path in ("app/main.py", "src", "lib"):
        if (root / path).exists():
            signals.append(f"code path present: `{path}`")
            break
    # Endpoint hints without full AST
    main = root / "app" / "main.py"
    if main.is_file():
        text = main.read_text(encoding="utf-8", errors="replace")
        if "def health" in text or "/health" in text:
            signals.append("health endpoint symbols already present in app/main.py")
        else:
            signals.append("no health endpoint symbols detected in app/main.py")
    if (root / ".retornatus" / "config.toml").is_file():
        signals.append("Retornatus already initialized")
    return signals


def _has_substance(text: str | None) -> bool:
    if not text:
        return False
    cleaned = text.strip().lower()
    placeholders = {
        "",
        "situation pending detailed analysis.",
        "tbd",
        "todo",
        "n/a",
    }
    return cleaned not in placeholders and len(cleaned) >= 8


def _looks_like_placeholder_done(criteria: list[str]) -> bool:
    if not criteria:
        return True
    weak = 0
    for c in criteria:
        cl = c.strip().lower()
        if len(cl) < 8 or cl in {"done", "ok", "works", "finished"}:
            weak += 1
    return weak == len(criteria)


_AMBIGUOUS_MARKERS = re.compile(
    r"\b(somehow|maybe|tbd|todo|unclear|decide later|or something)\b",
    re.I,
)


def assess_situation(
    *,
    demand: str,
    situation: str | None = None,
    what: str | None = None,
    done_criteria: list[str] | None = None,
    constraints: list[str] | None = None,
    project_context: str | None = None,
    repo_signals: list[str] | None = None,
) -> SituationAssessment:
    """
    Assess whether information is sufficient to activate a Contract.

    Asks only when the answer could materially alter WHAT / constraints / DONE.
    Repo signals are treated as known facts — do not re-ask what the repo shows.
    """
    assessment = SituationAssessment()
    done_criteria = done_criteria or []
    constraints = constraints or []
    signals = list(repo_signals or [])
    assessment.repo_signals = signals

    if _has_substance(demand):
        assessment.known_facts.append(f"Demand stated: {demand.strip()}")

    for signal in signals:
        assessment.known_facts.append(f"Repo: {signal}")
        # Infer soft constraints from stack — do not ask "what language?"
        if "pyproject.toml" in signal or "pytest" in signal.lower():
            if "Prefer pytest for automated verification" not in assessment.constraints:
                assessment.constraints.append(
                    "Prefer pytest for automated verification (inferred from repo)"
                )

    if project_context and project_context.strip():
        for line in project_context.splitlines():
            stripped = line.strip()
            if stripped.startswith("- ") and len(assessment.known_facts) < 16:
                fact = stripped[2:].strip()
                if fact and fact not in assessment.known_facts:
                    assessment.known_facts.append(fact)

    if constraints:
        for c in constraints:
            if c.strip() and c.strip() not in assessment.constraints:
                assessment.constraints.append(c.strip())

    if _has_substance(situation):
        assessment.known_facts.append("Situation narrative provided by agent/human")
    elif situation and not _has_substance(situation):
        assessment.assumptions.append(
            "Situation placeholder used — treat as unanalyzed unless Demand is trivial"
        )

    if not _has_substance(what):
        assessment.missing_decisions.append("WHAT obligation is not yet clear")
        assessment.focused_questions.append(
            FocusedQuestion(
                topic="WHAT",
                question="What concrete obligation must this Change deliver?",
                why_material="Contract WHAT cannot be empty or placeholder",
            )
        )
    else:
        assessment.known_facts.append(f"Proposed WHAT: {(what or '').strip()}")
        if _AMBIGUOUS_MARKERS.search(what or ""):
            assessment.ambiguities.append("WHAT contains unresolved hedging language")

    if _looks_like_placeholder_done(done_criteria):
        assessment.missing_decisions.append("DONE criteria are missing or too weak")
        # If repo has tests, suggest automated proof rather than open-ended ask
        if any("tests:" in s or "pytest" in s.lower() for s in signals):
            assessment.focused_questions.append(
                FocusedQuestion(
                    topic="DONE",
                    question="Confirm DONE includes an automated pytest covering the change",
                    why_material="Repo already has a test harness — Contract should use it",
                )
            )
        else:
            assessment.focused_questions.append(
                FocusedQuestion(
                    topic="DONE",
                    question="How will satisfaction be evidenced (tests, docs, review)?",
                    why_material="Active Contract requires at least one meaningful DONE criterion",
                )
            )
    else:
        for crit in done_criteria:
            assessment.known_facts.append(f"DONE criterion: {crit.strip()}")

    demand_l = demand.lower()
    security_hit = any(
        w in demand_l
        for w in ("unauthorized", "authn", "authz", "security hole", "secret leak", "pii")
    ) or ("auth" in demand_l and "oauth" not in demand_l)
    if security_hit and not constraints:
        assessment.ambiguities.append(
            "Security-sensitive Demand without explicit constraints"
        )
        assessment.focused_questions.append(
            FocusedQuestion(
                topic="constraints",
                question="What security or compliance constraints apply?",
                why_material="Constraints materially change Contract and Assurance",
            )
        )

    # Do not ask about stack/language when manifests already answered it
    simple = (
        _has_substance(demand)
        and _has_substance(what)
        and not _looks_like_placeholder_done(done_criteria)
        and not assessment.focused_questions
        and not assessment.missing_decisions
    )
    if simple:
        assessment.sufficient_for_contract = True
        assessment.rationale = (
            "Demand, WHAT, and DONE are sufficiently clear; repo signals incorporated; "
            "no material ambiguity detected"
        )
    else:
        assessment.sufficient_for_contract = False
        assessment.rationale = (
            "Material uncertainty remains — answer focused questions before activating Contract"
            if assessment.focused_questions
            else "Insufficient structured understanding for Contract activation"
        )

    return assessment


def apply_decision_to_situation(
    assessment: SituationAssessment,
    *,
    topic: str,
    answer: str,
) -> SituationAssessment:
    """Incorporate an answer/decision and re-evaluate sufficiency."""
    updated = SituationAssessment(
        known_facts=list(assessment.known_facts) + [f"Decision ({topic}): {answer}"],
        constraints=list(assessment.constraints),
        assumptions=[a for a in assessment.assumptions if topic.lower() not in a.lower()],
        ambiguities=[a for a in assessment.ambiguities if topic.lower() not in a.lower()],
        missing_decisions=[
            m for m in assessment.missing_decisions if topic.lower() not in m.lower()
        ],
        focused_questions=[
            q for q in assessment.focused_questions if q.topic.lower() != topic.lower()
        ],
        repo_signals=list(assessment.repo_signals),
    )
    if topic.lower() == "constraints" and answer.strip():
        updated.constraints.append(answer.strip())
    updated.sufficient_for_contract = (
        not updated.focused_questions and not updated.missing_decisions
    )
    updated.rationale = (
        "Focused questions resolved; Contract may be formalized"
        if updated.sufficient_for_contract
        else "Additional material questions remain"
    )
    return updated
