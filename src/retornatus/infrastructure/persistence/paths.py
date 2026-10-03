"""Filesystem layout helpers under `.retornatus/` (PRD §52)."""

from __future__ import annotations

import re
from pathlib import Path

from retornatus.constants import RETORNATUS_DIR
from retornatus.domain.errors import PathEscapeError
from retornatus.domain.ids import (
    change_id_of,
    validate_action_id,
    validate_bypass_id,
    validate_change_id,
    validate_decision_id,
    validate_evidence_id,
    validate_finding_id,
    validate_learning_id,
    validate_question_id,
    validate_rule_id,
    validate_skill_id,
)


class RetornatusPaths:
    """Resolves canonical artifact paths for a project root."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.retornatus = self.root / RETORNATUS_DIR

    @property
    def config(self) -> Path:
        return self.retornatus / "config.toml"

    @property
    def project_md(self) -> Path:
        return self.retornatus / "project" / "project.md"

    @property
    def changes(self) -> Path:
        return self.retornatus / "changes"

    @property
    def rules(self) -> Path:
        return self.retornatus / "governance" / "rules"

    @property
    def bypasses(self) -> Path:
        return self.retornatus / "governance" / "bypasses"

    @property
    def decisions(self) -> Path:
        return self.retornatus / "project" / "decisions"

    @property
    def learnings(self) -> Path:
        return self.retornatus / "adaptation" / "learnings"

    @property
    def skills(self) -> Path:
        return self.retornatus / "adaptation" / "skills"

    @property
    def skill_candidates(self) -> Path:
        return self.retornatus / "adaptation" / "skill-candidates"

    @property
    def index_db(self) -> Path:
        return self.retornatus / "index" / "retornatus.db"

    @property
    def runtime(self) -> Path:
        return self.retornatus / "runtime"

    @property
    def keys(self) -> Path:
        """Committed Ed25519 public keys (``.retornatus/keys/<key-id>.pub``)."""
        return self.retornatus / "keys"

    def _inside(self, path: Path) -> Path:
        """Reject paths that resolve outside ``.retornatus``."""
        resolved = path.resolve()
        base = self.retornatus.resolve()
        if resolved != base and base not in resolved.parents:
            raise PathEscapeError(f"Refusing path outside .retornatus: {path}")
        return path

    def change_dir(self, change_id: str) -> Path:
        validate_change_id(change_id)
        return self._inside(self.changes / change_id)

    def change_json(self, change_id: str) -> Path:
        return self._inside(self.change_dir(change_id) / "change.json")

    def situation_md(self, change_id: str) -> Path:
        return self._inside(self.change_dir(change_id) / "situation.md")

    def contract_json(self, change_id: str) -> Path:
        return self._inside(self.change_dir(change_id) / "contract.json")

    def contract_archive_json(self, change_id: str, version: int) -> Path:
        archive = self.change_dir(change_id) / "contracts"
        return self._inside(archive / f"v{version}.json")

    def _owned_file(self, owned_id: str, kind_dir: str, suffix: str) -> Path:
        change = change_id_of(owned_id)
        local = owned_id.split("/", 1)[1]
        return self._inside(self.change_dir(change) / kind_dir / f"{local}{suffix}")

    def action_json(self, action_id: str) -> Path:
        validate_action_id(action_id)
        return self._owned_file(action_id, "actions", ".json")

    def finding_json(self, finding_id: str) -> Path:
        validate_finding_id(finding_id)
        return self._owned_file(finding_id, "findings", ".json")

    def question_json(self, question_id: str) -> Path:
        validate_question_id(question_id)
        return self._owned_file(question_id, "questions", ".json")

    def evidence_json(self, evidence_id: str) -> Path:
        validate_evidence_id(evidence_id)
        return self._owned_file(evidence_id, "evidence", ".json")

    def evidence_output(self, evidence_id: str) -> Path:
        """Full combined stdout/stderr captured for executed Evidence."""
        return self.evidence_json(evidence_id).with_suffix(".output.txt")

    def rule_json(self, rule_id: str) -> Path:
        validate_rule_id(rule_id)
        return self._inside(self.rules / f"{rule_id}.json")

    def decision_json(self, decision_id: str) -> Path:
        validate_decision_id(decision_id)
        return self._inside(self.decisions / f"{decision_id}.json")

    def bypass_json(self, bypass_id: str) -> Path:
        validate_bypass_id(bypass_id)
        return self._inside(self.bypasses / f"{bypass_id}.json")

    def learning_md(self, learning_id: str) -> Path:
        validate_learning_id(learning_id)
        return self._inside(self.learnings / f"{learning_id}.md")

    def skill_dir(self, skill_id: str) -> Path:
        validate_skill_id(skill_id)
        return self._inside(self.skills / skill_id)

    def skill_md(self, skill_id: str) -> Path:
        return self._inside(self.skill_dir(skill_id) / "SKILL.md")

    def skill_candidate_md(self, candidate_id: str) -> Path:
        if re.fullmatch(r"K-\d{4}", candidate_id) is None:
            raise PathEscapeError(f"Refusing skill candidate id: {candidate_id!r}")
        return self._inside(self.skill_candidates / f"{candidate_id}.md")

    def public_key_path(self, key_id: str) -> Path:
        if not key_id or any(sep in key_id for sep in ("/", "\\", "..")):
            raise PathEscapeError(f"Refusing public key id: {key_id!r}")
        return self._inside(self.keys / f"{key_id}.pub")
