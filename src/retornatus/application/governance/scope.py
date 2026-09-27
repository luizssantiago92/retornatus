"""Compare a Change's declared resources with the real git diff."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from retornatus.application.assurance.evaluate import (
    evidence_is_fresh,
    execution_proof_kind,
)
from retornatus.application.assurance.evidence import EvidenceService
from retornatus.application.assurance.independent import evaluate_change_assurance
from retornatus.application.assurance.settings import (
    allow_self_reported_enabled,
    load_project_config,
)
from retornatus.application.assurance.subject_state import derive_current_subject_states
from retornatus.application.governance.diff import changed_paths, git_available
from retornatus.application.governance.globs import glob_match, normalize_repo_path
from retornatus.domain.errors import UsageError
from retornatus.domain.models import Evidence
from retornatus.domain.relations import RelationType
from retornatus.infrastructure.persistence.repository import FileRepository

DEFAULT_DENIED_GLOBS: tuple[str, ...] = (
    "**/.env",
    "**/.env.*",
    "**/secrets/**",
    "**/*.pem",
    "**/*.key",
)

DEFAULT_SENSITIVE_GLOBS: tuple[str, ...] = (
    "**/infra/**",
    "**/*.tf",
    "**/terraform/**",
    "**/k8s/**",
    "**/kubernetes/**",
    "**/helm/**",
    "**/auth/**",
    "**/authentication/**",
    "**/authorization/**",
    "**/migrations/**",
    "**/alembic/**",
    "**/.github/workflows/**",
    "**/.gitlab-ci.yml",
    "**/Jenkinsfile",
)

_SENSITIVE_EVIDENCE = frozenset({"review_result", "security_test"})


@dataclass(frozen=True)
class ScopeSettings:
    denied_globs: tuple[str, ...]
    sensitive_globs: tuple[str, ...]


@dataclass
class ScopeReport:
    changed: list[str]
    denied: list[str]
    out_of_scope: list[str]
    sensitive: list[str]
    sensitive_satisfied: bool
    messages: list[str]
    force_fail: bool = False

    @property
    def passed(self) -> bool:
        if self.force_fail or self.denied or self.out_of_scope:
            return False
        if self.sensitive and not self.sensitive_satisfied:
            return False
        return True


def load_scope_settings(root: Path) -> ScopeSettings:
    governance = load_project_config(root).get("governance")
    if not isinstance(governance, dict):
        return ScopeSettings(DEFAULT_DENIED_GLOBS, DEFAULT_SENSITIVE_GLOBS)
    table = governance.get("scope")
    if table is None:
        return ScopeSettings(DEFAULT_DENIED_GLOBS, DEFAULT_SENSITIVE_GLOBS)
    if not isinstance(table, dict):
        raise UsageError("Invalid [governance.scope]: expected a table")
    return ScopeSettings(
        denied_globs=_globs(table, "denied_globs", DEFAULT_DENIED_GLOBS),
        sensitive_globs=_globs(table, "sensitive_globs", DEFAULT_SENSITIVE_GLOBS),
    )


def change_resources(root: Path, change_id: str) -> list[str]:
    """Union of Task.resources on every Action of the Change."""
    repo = FileRepository(root)
    actions_dir = repo.paths.change_dir(change_id) / "actions"
    resources: list[str] = []
    if not actions_dir.is_dir():
        return resources
    for path in sorted(actions_dir.glob("A-*.json")):
        action, _ = repo.load_action(f"{change_id}/{path.stem}")
        for task in action.tasks:
            resources.extend(task.resources)
    return resources


def path_in_scope(path: str, resources: list[str]) -> bool:
    """True for ``.retornatus/**`` and declared Task resources (exact or glob)."""
    norm = normalize_repo_path(path)
    if norm == ".retornatus" or norm.startswith(".retornatus/"):
        return True
    for resource in resources:
        if _resource_matches(norm, resource):
            return True
    return False


def evaluate_scope(
    root: Path,
    change_id: str,
    *,
    base: str | None = None,
    staged: bool = False,
) -> ScopeReport:
    """Fail on out-of-scope paths, denied globs, and unreviewed sensitive paths."""
    if not git_available(root):
        return ScopeReport(
            changed=[],
            denied=[],
            out_of_scope=[],
            sensitive=[],
            sensitive_satisfied=False,
            messages=["Not a git work tree; scope gate needs a diff"],
            force_fail=True,
        )
    repo = FileRepository(root)
    try:
        repo.load_change(change_id)
    except FileNotFoundError:
        return ScopeReport(
            changed=[],
            denied=[],
            out_of_scope=[],
            sensitive=[],
            sensitive_satisfied=False,
            messages=[f"Change not found: {change_id}"],
            force_fail=True,
        )
    settings = load_scope_settings(root)
    names = changed_paths(root, base=base, staged=staged)
    resources = change_resources(root, change_id)
    denied: list[str] = []
    out_of_scope: list[str] = []
    sensitive: list[str] = []
    for name in names:
        if any(glob_match(name, pattern) for pattern in settings.denied_globs):
            denied.append(name)
            continue
        if not path_in_scope(name, resources):
            out_of_scope.append(name)
            continue
        if any(glob_match(name, pattern) for pattern in settings.sensitive_globs):
            sensitive.append(name)
    sensitive_ok = True
    if sensitive:
        sensitive_ok = sensitive_claim_satisfied(root, change_id)
    messages: list[str] = []
    for name in denied:
        messages.append(f"denied path: {name}")
    for name in out_of_scope:
        messages.append(
            f"out of scope: {name} (not in Task.resources or .retornatus/**)"
        )
    if sensitive and not sensitive_ok:
        joined = ", ".join(sensitive)
        messages.append(
            "sensitive paths require a satisfied review_result or security_test "
            f"claim: {joined}"
        )
    if not names and not messages:
        messages_ok = ["No changed paths"]
        return ScopeReport(
            changed=[],
            denied=[],
            out_of_scope=[],
            sensitive=[],
            sensitive_satisfied=True,
            messages=messages_ok,
        )
    if not messages:
        messages = [f"Scope OK ({len(names)} path(s))"]
    return ScopeReport(
        changed=names,
        denied=denied,
        out_of_scope=out_of_scope,
        sensitive=sensitive,
        sensitive_satisfied=sensitive_ok,
        messages=messages,
    )


def sensitive_claim_satisfied(root: Path, change_id: str) -> bool:
    """True when a review_result or security_test claim is actually satisfied."""
    try:
        result = evaluate_change_assurance(root, change_id)
    except FileNotFoundError:
        return False
    repo = FileRepository(root)
    try:
        contract, _ = repo.load_contract(change_id)
    except FileNotFoundError:
        return False
    from retornatus.application.assurance.evaluate import build_claims_from_contract

    claims = build_claims_from_contract(contract)
    evidence = EvidenceService(root).list_for_change(change_id)
    states = derive_current_subject_states(root, evidence)
    allowed = allow_self_reported_enabled(root)
    for claim in claims:
        if result.claim_results.get(claim.id) != "SATISFIED":
            continue
        needed = _SENSITIVE_EVIDENCE & set(claim.required_evidence_types)
        if not needed:
            continue
        for item in evidence:
            if item.type not in needed:
                continue
            if not _supports(item, claim.id):
                continue
            if not evidence_is_fresh(item, current_subject_states=states or None):
                continue
            if execution_proof_kind(item, allow_self_reported=allowed) != "satisfying":
                continue
            return True
    return False


def _supports(evidence: Evidence, claim_id: str) -> bool:
    return any(
        relation.type is RelationType.SUPPORTS and relation.target_id == claim_id
        for relation in evidence.relations
    )


def _resource_matches(path: str, resource: str) -> bool:
    resource_norm = normalize_repo_path(resource)
    if not resource_norm:
        return False
    if any(char in resource_norm for char in "*?["):
        return glob_match(path, resource_norm)
    if path == resource_norm:
        return True
    if resource_norm.endswith("/") and path.startswith(resource_norm):
        return True
    return False


def _globs(table: dict[str, Any], key: str, default: tuple[str, ...]) -> tuple[str, ...]:
    if key not in table:
        return default
    value = table[key]
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise UsageError(f"Invalid [governance.scope] {key}: expected a list of strings")
    return tuple(value)
