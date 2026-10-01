"""Policy evaluation against Rules, Authority, Boundaries (PRD §35 / M10).

Substring matches on the Action objective still run, and they emit a
deprecation warning. Structured rules (``effect_type``, ``path_globs``,
optional ``command_patterns``) match declared resources and the real diff
instead of the wording of the objective.
"""

from __future__ import annotations

import fnmatch
import shlex
from enum import StrEnum
from pathlib import Path

from pydantic import Field

from retornatus.domain.base import DomainModel
from retornatus.domain.enums import AuthorityCategory
from retornatus.domain.ids import change_id_of
from retornatus.domain.models import Authority, Boundaries, Rule
from retornatus.infrastructure.persistence.repository import FileRepository


class PolicyVerdict(StrEnum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    REQUIRE_HUMAN = "REQUIRE_HUMAN"


class PolicyDecision(DomainModel):
    verdict: PolicyVerdict
    rationale: str = Field(min_length=1)
    matched_rule_ids: list[str] = Field(default_factory=list)
    effect: str | None = None
    warnings: list[str] = Field(default_factory=list)


def rule_is_structured(rule: Rule) -> bool:
    """True when the rule declares effect type, path globs, or command patterns."""
    return bool(rule.effect_type or rule.path_globs or rule.command_patterns)


def command_matches(command: str, pattern: str) -> bool:
    """Fnmatch when the pattern has glob characters, otherwise a case-fold substring."""
    text = command.strip()
    needle = pattern.strip()
    if not text or not needle:
        return False
    if any(char in needle for char in "*?["):
        head = text.split()[0] if text.split() else text
        return fnmatch.fnmatchcase(text, needle) or fnmatch.fnmatchcase(head, needle)
    return needle.casefold() in text.casefold()


def evaluate_policy(
    *,
    effect: str,
    rules: list[Rule],
    authority: Authority,
    boundaries: Boundaries | None = None,
    paths: list[str] | None = None,
    diff_paths: list[str] | None = None,
    commands: list[str] | None = None,
    effect_type: str | None = None,
) -> PolicyDecision:
    """Evaluate a proposed governed effect.

    Structured rules see ``paths`` (declared resources), ``diff_paths`` (git),
    and ``commands``. Substring rules still match ``effect`` text and are
    reported as deprecated.
    """
    boundaries = boundaries or Boundaries()
    effect_l = effect.lower()
    matched: list[str] = []
    warnings = _substring_deprecation(rules)
    combined_paths = _unique([*(paths or []), *(diff_paths or [])])
    command_lines = [item for item in (commands or []) if item.strip()]
    types = _effect_types(effect, effect_type, combined_paths, command_lines)

    def decide(
        verdict: PolicyVerdict,
        rationale: str,
    ) -> PolicyDecision:
        return PolicyDecision(
            verdict=verdict,
            rationale=rationale,
            matched_rule_ids=list(matched),
            effect=effect,
            warnings=warnings,
        )

    for boundary in boundaries.items:
        if boundary.realization.value == "ENFORCED" and boundary.name.lower() in effect_l:
            return decide(
                PolicyVerdict.DENY,
                f"Enforced boundary blocks effect: {boundary.name}",
            )

    for rule in rules:
        if not rule.active or not rule_is_structured(rule):
            continue
        if not _structured_matches(
            rule,
            types=types,
            paths=combined_paths,
            commands=command_lines,
        ):
            continue
        matched.append(rule.id)
        if _is_deny_statement(rule.statement):
            return decide(PolicyVerdict.DENY, f"Denied by structured rule {rule.id}")

    for rule in rules:
        if not rule.active or rule_is_structured(rule):
            continue
        if rule.applicability.lower() in effect_l or effect_l in rule.statement.lower():
            matched.append(rule.id)
            if _is_deny_statement(rule.statement):
                return decide(PolicyVerdict.DENY, f"Denied by rule {rule.id}")

    if authority.category == AuthorityCategory.HUMAN:
        return decide(
            PolicyVerdict.REQUIRE_HUMAN,
            "Authority requires human judgment",
        )

    if matched and authority.category == AuthorityCategory.RULED:
        return decide(PolicyVerdict.ALLOW, "Allowed under applicable rules")

    return decide(
        PolicyVerdict.ALLOW,
        "No denying rule matched; delegated authority",
    )


def _is_deny_statement(statement: str) -> bool:
    stmt = statement.lower()
    return stmt.startswith("must not") or stmt.startswith("do not")


def _substring_deprecation(rules: list[Rule]) -> list[str]:
    legacy = [rule.id for rule in rules if rule.active and not rule_is_structured(rule)]
    if not legacy:
        return []
    joined = ", ".join(legacy)
    return [
        "Substring policy rules are deprecated ("
        + joined
        + "). Declare effect_type, path_globs, and optional command_patterns."
    ]


def _effect_types(
    effect: str,
    effect_type: str | None,
    paths: list[str],
    commands: list[str],
) -> set[str]:
    found: set[str] = set()
    if effect_type and effect_type.strip():
        found.add(effect_type.strip().casefold())
    token = effect.strip().casefold()
    if token and " " not in token:
        found.add(token)
    if paths:
        found.add("write")
    if commands:
        found.add("exec")
    return found


def _structured_matches(
    rule: Rule,
    *,
    types: set[str],
    paths: list[str],
    commands: list[str],
) -> bool:
    if rule.effect_type and rule.effect_type.casefold() not in types:
        return False
    if rule.path_globs and not any(_path_matches(path, rule.path_globs) for path in paths):
        return False
    if not rule.command_patterns:
        return True
    return any(command_matches(command, pattern) for command in commands for pattern in rule.command_patterns)


def _path_matches(path: str, globs: list[str]) -> bool:
    from retornatus.application.governance.globs import glob_match

    return any(glob_match(path, pattern) for pattern in globs)


def _unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered


def evaluate_action_policy(
    root: Path,
    action_id: str,
    *,
    effect_type: str | None = None,
    extra_paths: list[str] | None = None,
    extra_commands: list[str] | None = None,
) -> PolicyDecision:
    """
    Evaluate Policy for an Action using active Rules + Action Authority.

    Structured rules see Task.resources and the work tree diff, not only the
    objective sentence. Includes isolation Boundaries so ENFORCED host
    constraints can DENY.
    """
    from retornatus.application.execution.isolation import (
        enrich_capabilities,
        isolation_boundaries,
    )
    from retornatus.infrastructure.environment.adapters import detect_environment

    repo = FileRepository(root)
    action, _ = repo.load_action(action_id)
    _, caps = detect_environment(root)
    caps = enrich_capabilities(root, caps)
    boundaries = Boundaries(items=list(isolation_boundaries(root, caps)))
    resources: list[str] = []
    for task in action.tasks:
        resources.extend(task.resources)
    diff_paths = _diff_paths(root)
    commands = _executed_commands(root, change_id_of(action_id))
    return evaluate_policy(
        effect=action.objective,
        rules=repo.list_rules(),
        authority=action.authority,
        boundaries=boundaries,
        paths=[*resources, *(extra_paths or [])],
        diff_paths=diff_paths,
        commands=[*commands, *(extra_commands or [])],
        effect_type=effect_type,
    )


def _diff_paths(root: Path) -> list[str]:
    from retornatus.application.governance.diff import changed_paths
    from retornatus.domain.errors import UsageError

    try:
        return changed_paths(root)
    except (UsageError, OSError):
        return []


def _executed_commands(root: Path, change_id: str) -> list[str]:
    from retornatus.application.assurance.evidence import EvidenceService

    try:
        evidence = EvidenceService(root).list_for_change(change_id)
    except (OSError, FileNotFoundError, ValueError):
        return []
    commands: list[str] = []
    for item in evidence:
        if item.command:
            commands.append(shlex.join(item.command))
    return commands
