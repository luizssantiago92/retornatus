"""File-backed repository — single persistence boundary (PRD §55)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from retornatus.domain.models import (
    Action,
    BypassRecord,
    Change,
    Contract,
    Decision,
    Evidence,
    Finding,
    LearningMetadata,
    Question,
    Rule,
    Skill,
)
from retornatus.infrastructure.persistence.atomic import atomic_write_bytes, atomic_write_text
from retornatus.infrastructure.persistence.concurrency import (
    ArtifactRevision,
    ConcurrencyConflict,
    assert_unchanged,
    read_revision,
)
from retornatus.infrastructure.persistence.migrations import (
    DEFAULT_REGISTRY,
    IncompatibleSchemaError,
    MigrationRegistry,
)
from retornatus.infrastructure.persistence.paths import RetornatusPaths
from retornatus.infrastructure.persistence.serializers import (
    dump_json_model,
    dump_markdown,
    dump_toml_dict,
    load_json_model,
    load_markdown,
    load_toml_dict,
)

T = TypeVar("T", bound=BaseModel)


class FileRepository:
    """Canonical file repository with atomic writes and optimistic concurrency."""

    def __init__(
        self,
        root: Path,
        *,
        migrations: MigrationRegistry | None = None,
    ) -> None:
        self.paths = RetornatusPaths(root)
        self.migrations = migrations or DEFAULT_REGISTRY

    # --- generic JSON helpers -------------------------------------------------

    def _load_json(self, path: Path, model_type: type[T]) -> tuple[T, ArtifactRevision]:
        raw, revision = read_revision(path)
        if raw is None:
            raise FileNotFoundError(path)
        payload = json.loads(raw.decode("utf-8"))
        try:
            migrated = self.migrations.migrate(payload)
        except IncompatibleSchemaError:
            raise
        model = model_type.model_validate(migrated)
        return model, revision

    def _save_json(
        self,
        path: Path,
        model: BaseModel,
        *,
        expected: ArtifactRevision | None = None,
    ) -> ArtifactRevision:
        if expected is not None:
            assert_unchanged(expected)
        elif path.exists():
            raise ConcurrencyConflict(
                f"Refusing to overwrite existing artifact without expected revision: {path}"
            )
        data = dump_json_model(model)
        atomic_write_bytes(path, data)
        _, revision = read_revision(path)
        return revision

    # --- config / markdown ----------------------------------------------------

    def load_config(self) -> tuple[dict, ArtifactRevision]:
        raw, revision = read_revision(self.paths.config)
        if raw is None:
            raise FileNotFoundError(self.paths.config)
        return load_toml_dict(raw), revision

    def save_config(
        self,
        data: dict,
        *,
        expected: ArtifactRevision | None = None,
    ) -> ArtifactRevision:
        if expected is not None:
            assert_unchanged(expected)
        atomic_write_bytes(self.paths.config, dump_toml_dict(data))
        _, revision = read_revision(self.paths.config)
        return revision

    def save_markdown(
        self,
        path: Path,
        body: str,
        *,
        front_matter: dict | None = None,
        expected: ArtifactRevision | None = None,
    ) -> ArtifactRevision:
        if expected is not None:
            assert_unchanged(expected)
        elif path.exists() and expected is None:
            # Allow create-or-replace only when caller passes expected=None AND
            # we treat missing expected as create-only for new files; if exists, require expected.
            raise ConcurrencyConflict(
                f"Refusing to overwrite existing markdown without expected revision: {path}"
            )
        text = dump_markdown(body, front_matter=front_matter)
        atomic_write_text(path, text)
        _, revision = read_revision(path)
        return revision

    def load_markdown(self, path: Path) -> tuple[dict | None, str, ArtifactRevision]:
        raw, revision = read_revision(path)
        if raw is None:
            raise FileNotFoundError(path)
        meta, body = load_markdown(raw.decode("utf-8"))
        return meta, body, revision

    # --- Change aggregate -----------------------------------------------------

    def save_change(
        self,
        change: Change,
        *,
        expected: ArtifactRevision | None = None,
    ) -> ArtifactRevision:
        path = self.paths.change_json(change.id)
        path.parent.mkdir(parents=True, exist_ok=True)
        for sub in ("actions", "findings", "questions", "evidence"):
            (path.parent / sub).mkdir(exist_ok=True)
        return self._save_json(path, change, expected=expected)

    def load_change(self, change_id: str) -> tuple[Change, ArtifactRevision]:
        return self._load_json(self.paths.change_json(change_id), Change)

    def list_change_ids(self) -> list[str]:
        if not self.paths.changes.is_dir():
            return []
        return sorted(
            p.name
            for p in self.paths.changes.iterdir()
            if p.is_dir() and (p / "change.json").is_file()
        )

    def save_situation(
        self,
        change_id: str,
        body: str,
        *,
        expected: ArtifactRevision | None = None,
    ) -> ArtifactRevision:
        return self.save_markdown(
            self.paths.situation_md(change_id),
            body,
            front_matter={"schema_version": 1, "change_id": change_id},
            expected=expected,
        )

    def load_situation(self, change_id: str) -> tuple[dict | None, str, ArtifactRevision]:
        return self.load_markdown(self.paths.situation_md(change_id))

    def save_contract(
        self,
        contract: Contract,
        *,
        expected: ArtifactRevision | None = None,
    ) -> ArtifactRevision:
        return self._save_json(
            self.paths.contract_json(contract.change_id),
            contract,
            expected=expected,
        )

    def load_contract(self, change_id: str) -> tuple[Contract, ArtifactRevision]:
        return self._load_json(self.paths.contract_json(change_id), Contract)

    def save_action(
        self, action: Action, *, expected: ArtifactRevision | None = None
    ) -> ArtifactRevision:
        return self._save_json(self.paths.action_json(action.id), action, expected=expected)

    def load_action(self, action_id: str) -> tuple[Action, ArtifactRevision]:
        return self._load_json(self.paths.action_json(action_id), Action)

    def save_finding(
        self, finding: Finding, *, expected: ArtifactRevision | None = None
    ) -> ArtifactRevision:
        return self._save_json(
            self.paths.finding_json(finding.id), finding, expected=expected
        )

    def load_finding(self, finding_id: str) -> tuple[Finding, ArtifactRevision]:
        return self._load_json(self.paths.finding_json(finding_id), Finding)

    def save_question(
        self, question: Question, *, expected: ArtifactRevision | None = None
    ) -> ArtifactRevision:
        return self._save_json(
            self.paths.question_json(question.id), question, expected=expected
        )

    def load_question(self, question_id: str) -> tuple[Question, ArtifactRevision]:
        return self._load_json(self.paths.question_json(question_id), Question)

    def save_evidence(
        self, evidence: Evidence, *, expected: ArtifactRevision | None = None
    ) -> ArtifactRevision:
        return self._save_json(
            self.paths.evidence_json(evidence.id), evidence, expected=expected
        )

    def load_evidence(self, evidence_id: str) -> tuple[Evidence, ArtifactRevision]:
        return self._load_json(self.paths.evidence_json(evidence_id), Evidence)

    def save_rule(
        self, rule: Rule, *, expected: ArtifactRevision | None = None
    ) -> ArtifactRevision:
        return self._save_json(self.paths.rule_json(rule.id), rule, expected=expected)

    def load_rule(self, rule_id: str) -> tuple[Rule, ArtifactRevision]:
        return self._load_json(self.paths.rule_json(rule_id), Rule)

    def list_rules(self) -> list[Rule]:
        if not self.paths.rules.is_dir():
            return []
        rules: list[Rule] = []
        for path in sorted(self.paths.rules.glob("R-*.json")):
            rule, _ = self._load_json(path, Rule)
            rules.append(rule)
        return rules

    def save_decision(
        self, decision: Decision, *, expected: ArtifactRevision | None = None
    ) -> ArtifactRevision:
        self.paths.decisions.mkdir(parents=True, exist_ok=True)
        return self._save_json(
            self.paths.decision_json(decision.id), decision, expected=expected
        )

    def load_decision(self, decision_id: str) -> tuple[Decision, ArtifactRevision]:
        return self._load_json(self.paths.decision_json(decision_id), Decision)

    def list_decisions(self) -> list[Decision]:
        if not self.paths.decisions.is_dir():
            return []
        items: list[Decision] = []
        for path in sorted(self.paths.decisions.glob("D-*.json")):
            decision, _ = self._load_json(path, Decision)
            items.append(decision)
        return items

    def save_bypass(
        self, bypass: BypassRecord, *, expected: ArtifactRevision | None = None
    ) -> ArtifactRevision:
        self.paths.bypasses.mkdir(parents=True, exist_ok=True)
        return self._save_json(
            self.paths.bypass_json(bypass.id), bypass, expected=expected
        )

    def load_bypass(self, bypass_id: str) -> tuple[BypassRecord, ArtifactRevision]:
        return self._load_json(self.paths.bypass_json(bypass_id), BypassRecord)

    def list_bypasses(self) -> list[BypassRecord]:
        if not self.paths.bypasses.is_dir():
            return []
        items: list[BypassRecord] = []
        for path in sorted(self.paths.bypasses.glob("B-*.json")):
            bypass, _ = self._load_json(path, BypassRecord)
            items.append(bypass)
        return items

    def save_learning(
        self,
        meta: LearningMetadata,
        body: str,
        *,
        expected: ArtifactRevision | None = None,
    ) -> ArtifactRevision:
        path = self.paths.learning_md(meta.id)
        front = json.loads(meta.model_dump_json())
        return self.save_markdown(path, body, front_matter=front, expected=expected)

    def load_learning(
        self, learning_id: str
    ) -> tuple[LearningMetadata, str, ArtifactRevision]:
        meta, body, revision = self.load_markdown(self.paths.learning_md(learning_id))
        if meta is None:
            raise IncompatibleSchemaError(f"Learning {learning_id} missing metadata")
        return LearningMetadata.model_validate(meta), body, revision

    def list_learnings(self) -> list[LearningMetadata]:
        if not self.paths.learnings.is_dir():
            return []
        items: list[LearningMetadata] = []
        for path in sorted(self.paths.learnings.glob("L-*.md")):
            meta, _, _ = self.load_markdown(path)
            if meta:
                items.append(LearningMetadata.model_validate(meta))
        return items

    def save_skill(
        self,
        skill: Skill,
        body: str,
        *,
        expected: ArtifactRevision | None = None,
    ) -> ArtifactRevision:
        path = self.paths.skill_md(skill.id)
        path.parent.mkdir(parents=True, exist_ok=True)
        front = json.loads(skill.model_dump_json())
        return self.save_markdown(path, body, front_matter=front, expected=expected)

    def load_skill(self, skill_id: str) -> tuple[Skill, str, ArtifactRevision]:
        meta, body, revision = self.load_markdown(self.paths.skill_md(skill_id))
        if meta is None:
            raise IncompatibleSchemaError(f"Skill {skill_id} missing metadata")
        return Skill.model_validate(meta), body, revision

    def list_skills(self) -> list[Skill]:
        if not self.paths.skills.is_dir():
            return []
        items: list[Skill] = []
        for path in sorted(self.paths.skills.glob("S-*")):
            skill_md = path / "SKILL.md"
            if not skill_md.is_file():
                continue
            meta, _, _ = self.load_markdown(skill_md)
            if meta:
                items.append(Skill.model_validate(meta))
        return items
