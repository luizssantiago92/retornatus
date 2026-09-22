"""Situation elicitation — requirements analysis before Contract formalization.

Demand → inspect context / kickoff → focused questions (≤5, with options) →
Contract readiness. Not a separate RequirementsEngine (PRD §11).
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

MAX_FOCUSED_QUESTIONS = 5

_KICKOFF_CANDIDATES = (
    "prd.md",
    "prd/PRD.md",
    "docs/brief.md",
    "kickoff.md",
    "docs/kickoff.md",
)

_VAGUE_VERBS = re.compile(
    r"\b(add|improve|fix|support|update|enhance|handle|implement|create|make)\b",
    re.I,
)
_SCOPE_HINTS = re.compile(
    r"\b(user|users|admin|customer|api|endpoint|ui|cli|oauth|password|"
    r"email|session|scope|out of scope|must|shall|acceptance)\b",
    re.I,
)
_AMBIGUOUS_MARKERS = re.compile(
    r"\b(somehow|maybe|tbd|todo|unclear|decide later|or something)\b",
    re.I,
)


@dataclass
class FocusedQuestion:
    """A material uncertainty that can change the Contract."""

    topic: str
    question: str
    why_material: str
    options: list[str] = field(default_factory=list)
    round_priority: int = 50


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
    kickoff_sources: list[str] = field(default_factory=list)

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
        if self.kickoff_sources:
            lines.extend(
                [
                    "## Kickoff sources",
                    "",
                    *[f"- `{s}`" for s in self.kickoff_sources],
                    "",
                ]
            )
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
            lines.append(
                "_Requirements analysis — answer these before activating a Contract "
                f"(at most {MAX_FOCUSED_QUESTIONS} per round)._"
            )
            lines.append("")
            for q in self.focused_questions:
                lines.append(
                    f"- **{q.topic}**: {q.question} _(material: {q.why_material})_"
                )
                if q.options:
                    for i, opt in enumerate(q.options, start=1):
                        lines.append(f"  - {i}. {opt}")
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


def discover_kickoff(
    root: Path, *, max_chars_per_file: int = 1500
) -> tuple[list[str], list[str]]:
    """
    Find local kickoff / brief files and extract light facts.

    Returns (source relative paths, fact lines). Does not build a semantic index.
    """
    root = root.resolve()
    sources: list[str] = []
    facts: list[str] = []
    for rel in _KICKOFF_CANDIDATES:
        path = root / rel
        if not path.is_file():
            continue
        sources.append(rel.replace("\\", "/"))
        text = path.read_text(encoding="utf-8", errors="replace").strip()
        if len(text) > max_chars_per_file:
            text = text[: max_chars_per_file - 20].rstrip() + "\n\n…(truncated)"
        facts.append(f"Kickoff `{rel}` present ({len(text)} chars loaded)")
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if stripped.startswith(("- ", "* ", "> ")):
                item = stripped.lstrip("-*> ").strip()
                if len(item) >= 12 and len(facts) < 24:
                    facts.append(f"From `{rel}`: {item}")
            elif re.match(r"^\d+\.", stripped) and len(facts) < 24:
                facts.append(f"From `{rel}`: {stripped}")
    return sources, facts


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


def _demand_looks_vague(demand: str, *, what: str | None) -> bool:
    """Short / generic software asks without actor, scope, or criterion."""
    d = demand.strip()
    if not d:
        return True
    if _has_substance(what) and len(d) >= 40 and _SCOPE_HINTS.search(d):
        return False
    words = re.findall(r"[a-zA-Z0-9]+", d)
    if len(words) <= 6 and _VAGUE_VERBS.search(d):
        return True
    if _VAGUE_VERBS.search(d) and not _SCOPE_HINTS.search(d) and len(words) < 14:
        return True
    if len(words) <= 4:
        return True
    return False


def _topic_covered_in_facts(topic: str, facts: list[str]) -> bool:
    """Skip re-asking when kickoff / facts already speak to the topic."""
    blob = " ".join(facts).lower()
    markers = {
        "scope": ("scope", "in scope", "must ", "shall "),
        "actors": ("user", "users", "actor", "admin", "customer", "persona"),
        "out_of_scope": ("out of scope", "not in scope", "exclude", "non-goal"),
        "success": ("acceptance", "done when", "success", "criteria", "verify"),
        "WHAT": ("what:", "obligation", "deliver"),
        "DONE": ("done", "pytest", "test", "evidence"),
        "constraints": ("constraint", "security", "compliance", "must not"),
    }
    for marker in markers.get(topic, (topic.lower(),)):
        if marker in blob:
            return True
    return False


def _cap_questions(questions: list[FocusedQuestion]) -> list[FocusedQuestion]:
    ordered = sorted(questions, key=lambda q: (q.round_priority, q.topic))
    return ordered[:MAX_FOCUSED_QUESTIONS]


def parse_answer_option(raw: str) -> tuple[str, str]:
    """Parse ``TOPIC=text`` or ``TOPIC:text`` into (topic, answer)."""
    for sep in ("=", ":"):
        if sep in raw:
            topic, _, answer = raw.partition(sep)
            topic = topic.strip()
            answer = answer.strip()
            if topic and answer:
                return topic, answer
    raise ValueError(
        f"Invalid --answer '{raw}'; expected TOPIC=text (e.g. scope=Email+password only)"
    )


def merge_answers_into_inputs(
    *,
    what: str | None,
    done_criteria: list[str],
    constraints: list[str],
    answers: dict[str, str],
) -> tuple[str | None, list[str], list[str], dict[str, str]]:
    """
    Fold WHAT / DONE / constraints answers into assess inputs.

    Remaining answers (scope, actors, …) stay for apply_decision_to_situation.
    """
    remaining = dict(answers)
    what_out = what
    done_out = list(done_criteria)
    constraints_out = list(constraints)

    for key in list(remaining):
        kl = key.lower()
        if kl == "what" and not _has_substance(what_out):
            what_out = remaining.pop(key)
        elif kl == "done":
            done_out.append(remaining.pop(key))
        elif kl in {"constraint", "constraints"}:
            constraints_out.append(remaining.pop(key))

    return what_out, done_out, constraints_out, remaining


def assess_situation(
    *,
    demand: str,
    situation: str | None = None,
    what: str | None = None,
    done_criteria: list[str] | None = None,
    constraints: list[str] | None = None,
    project_context: str | None = None,
    repo_signals: list[str] | None = None,
    kickoff_sources: list[str] | None = None,
    kickoff_facts: list[str] | None = None,
    answered_topics: set[str] | None = None,
) -> SituationAssessment:
    """
    Assess whether information is sufficient to activate a Contract.

    Requirements-analysis behavior: ask only when the answer could materially
    alter WHAT / constraints / DONE / scope. Cap at MAX_FOCUSED_QUESTIONS.
    Repo signals and kickoff facts are known — do not re-ask what they show.
    """
    assessment = SituationAssessment()
    done_criteria = list(done_criteria or [])
    constraints = list(constraints or [])
    signals = list(repo_signals or [])
    answered = {t.lower() for t in (answered_topics or set())}
    assessment.repo_signals = signals
    assessment.kickoff_sources = list(kickoff_sources or [])

    if _has_substance(demand):
        assessment.known_facts.append(f"Demand stated: {demand.strip()}")

    for signal in signals:
        assessment.known_facts.append(f"Repo: {signal}")
        if "pyproject.toml" in signal or "pytest" in signal.lower():
            if "Prefer pytest for automated verification" not in assessment.constraints:
                assessment.constraints.append(
                    "Prefer pytest for automated verification (inferred from repo)"
                )

    for fact in kickoff_facts or []:
        if fact and fact not in assessment.known_facts:
            assessment.known_facts.append(fact)

    if project_context and project_context.strip():
        for line in project_context.splitlines():
            stripped = line.strip()
            if stripped.startswith("- ") and len(assessment.known_facts) < 28:
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

    questions: list[FocusedQuestion] = []

    if not _has_substance(what) and "what" not in answered:
        questions.append(
            FocusedQuestion(
                topic="WHAT",
                question="What concrete obligation must this Change deliver?",
                why_material="Contract WHAT cannot be empty or placeholder",
                options=[
                    "One user-visible behavior with a clear success path",
                    "An API/CLI contract with status codes and payload shape",
                    "A bug fix restoring a previously working behavior",
                ],
                round_priority=10,
            )
        )
    else:
        if _has_substance(what):
            assessment.known_facts.append(f"Proposed WHAT: {(what or '').strip()}")
        if _AMBIGUOUS_MARKERS.search(what or ""):
            assessment.ambiguities.append("WHAT contains unresolved hedging language")

    if _looks_like_placeholder_done(done_criteria) and "done" not in answered:
        if any("tests:" in s or "pytest" in s.lower() for s in signals):
            questions.append(
                FocusedQuestion(
                    topic="DONE",
                    question="Confirm DONE includes an automated pytest covering the change",
                    why_material="Repo already has a test harness — Contract should use it",
                    options=[
                        "Yes — pytest covering the new/changed behavior",
                        "Pytest plus a short doc note",
                        "Defer automated test only if QUICK lane and explicitly justified",
                    ],
                    round_priority=15,
                )
            )
        else:
            questions.append(
                FocusedQuestion(
                    topic="DONE",
                    question="How will satisfaction be evidenced (tests, docs, review)?",
                    why_material="Active Contract requires at least one meaningful DONE criterion",
                    options=[
                        "Automated tests when a harness exists or can be added",
                        "Documented manual check steps with expected results",
                        "Independent review evidence for high-risk Changes",
                    ],
                    round_priority=15,
                )
            )
    else:
        for crit in done_criteria:
            if crit.strip():
                assessment.known_facts.append(f"DONE criterion: {crit.strip()}")

    demand_l = demand.lower()
    security_hit = any(
        w in demand_l
        for w in ("unauthorized", "authn", "authz", "security hole", "secret leak", "pii")
    ) or ("auth" in demand_l and "oauth" not in demand_l)
    if (
        security_hit
        and not constraints
        and "constraints" not in answered
        and "constraint" not in answered
    ):
        assessment.ambiguities.append(
            "Security-sensitive Demand without explicit constraints"
        )
        questions.append(
            FocusedQuestion(
                topic="constraints",
                question="What security or compliance constraints apply?",
                why_material="Constraints materially change Contract and Assurance",
                options=[
                    "No secrets in logs; fail closed on auth errors",
                    "Follow existing project auth patterns only",
                    "Explicit threat notes required before activate",
                ],
                round_priority=20,
            )
        )

    vague = _demand_looks_vague(demand, what=what)
    obligations_clear = _has_substance(what) and not _looks_like_placeholder_done(
        done_criteria
    )
    if vague and not obligations_clear:
        assessment.ambiguities.append(
            "Demand looks underspecified for software delivery (requirements analysis needed)"
        )
        vague_questions = [
            FocusedQuestion(
                topic="actors",
                question="Who is the primary actor for this Change?",
                why_material="Actor choice changes WHAT and acceptance paths",
                options=[
                    "End user of the product",
                    "Operator / admin",
                    "Another service / API client",
                ],
                round_priority=25,
            ),
            FocusedQuestion(
                topic="scope",
                question="What is the minimum in-scope behavior for the first Contract?",
                why_material="Vague Demand hardens into the wrong product without a scope cut",
                options=[
                    "Happy path only for one primary flow",
                    "Happy path plus the top failure mode",
                    "Parity with an existing documented behavior",
                ],
                round_priority=26,
            ),
            FocusedQuestion(
                topic="out_of_scope",
                question="What must stay explicitly out of scope for this Change?",
                why_material="Out-of-scope prevents mid-build scope creep",
                options=[
                    "No new auth providers / identity systems",
                    "No UI redesign beyond the touched flow",
                    "No infra / deploy changes",
                ],
                round_priority=27,
            ),
            FocusedQuestion(
                topic="success",
                question="How will we know the software Change succeeded?",
                why_material="Success criteria become Contract DONE",
                options=[
                    "Automated test proves the behavior",
                    "Documented manual scenario passes",
                    "Both test and a short review note",
                ],
                round_priority=28,
            ),
        ]
        for vq in vague_questions:
            if vq.topic.lower() in answered:
                continue
            if _topic_covered_in_facts(vq.topic, assessment.known_facts):
                assessment.known_facts.append(
                    f"Topic `{vq.topic}` already addressed in kickoff/facts — not re-asked"
                )
                continue
            questions.append(vq)

    # Never invent language/stack questions — repo signals already cover that
    questions = [
        q
        for q in questions
        if q.topic.lower() not in {"language", "stack", "runtime"}
        and q.topic.lower() not in answered
    ]
    assessment.focused_questions = _cap_questions(questions)
    # Missing decisions track only this round's remaining questions
    assessment.missing_decisions = [
        f"Requirements topic `{q.topic}` not yet decided"
        for q in assessment.focused_questions
    ]

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
            "Demand, WHAT, and DONE are sufficiently clear; repo/kickoff signals "
            "incorporated; no material requirements ambiguity detected"
        )
    else:
        assessment.sufficient_for_contract = False
        assessment.rationale = (
            "Material uncertainty remains — answer focused questions "
            "(requirements analysis) before activating Contract"
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
    """Incorporate an answer/decision and re-evaluate sufficiency for this round."""
    topic_l = topic.lower()
    updated = SituationAssessment(
        known_facts=list(assessment.known_facts) + [f"Decision ({topic}): {answer}"],
        constraints=list(assessment.constraints),
        assumptions=[a for a in assessment.assumptions if topic_l not in a.lower()],
        ambiguities=[a for a in assessment.ambiguities if topic_l not in a.lower()],
        missing_decisions=[
            m
            for m in assessment.missing_decisions
            if topic_l not in m.lower() and f"`{topic_l}`" not in m.lower()
        ],
        focused_questions=[
            q for q in assessment.focused_questions if q.topic.lower() != topic_l
        ],
        repo_signals=list(assessment.repo_signals),
        kickoff_sources=list(assessment.kickoff_sources),
    )
    if topic_l in {"constraints", "constraint"} and answer.strip():
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


def apply_answers(
    assessment: SituationAssessment,
    answers: dict[str, str],
) -> SituationAssessment:
    """Apply multiple topic answers in order."""
    current = assessment
    for topic, answer in answers.items():
        current = apply_decision_to_situation(current, topic=topic, answer=answer)
    return current
