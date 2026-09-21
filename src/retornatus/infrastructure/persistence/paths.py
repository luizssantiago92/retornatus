"""Filesystem layout helpers under `.retornatus/` (PRD §52)."""

from __future__ import annotations

from pathlib import Path

from retornatus.constants import RETORNATUS_DIR
from retornatus.domain.ids import change_id_of


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
    def learnings(self) -> Path:
        return self.retornatus / "adaptation" / "learnings"

    @property
    def skills(self) -> Path:
        return self.retornatus / "adaptation" / "skills"

    @property
    def index_db(self) -> Path:
        return self.retornatus / "index" / "retornatus.db"

    @property
    def runtime(self) -> Path:
        return self.retornatus / "runtime"

    def change_dir(self, change_id: str) -> Path:
        return self.changes / change_id

    def change_json(self, change_id: str) -> Path:
        return self.change_dir(change_id) / "change.json"

    def situation_md(self, change_id: str) -> Path:
        return self.change_dir(change_id) / "situation.md"

    def contract_json(self, change_id: str) -> Path:
        return self.change_dir(change_id) / "contract.json"

    def action_json(self, action_id: str) -> Path:
        change = change_id_of(action_id)
        local = action_id.split("/", 1)[1]
        return self.change_dir(change) / "actions" / f"{local}.json"

    def finding_json(self, finding_id: str) -> Path:
        change = change_id_of(finding_id)
        local = finding_id.split("/", 1)[1]
        return self.change_dir(change) / "findings" / f"{local}.json"

    def question_json(self, question_id: str) -> Path:
        change = change_id_of(question_id)
        local = question_id.split("/", 1)[1]
        return self.change_dir(change) / "questions" / f"{local}.json"

    def evidence_json(self, evidence_id: str) -> Path:
        change = change_id_of(evidence_id)
        local = evidence_id.split("/", 1)[1]
        return self.change_dir(change) / "evidence" / f"{local}.json"

    def rule_json(self, rule_id: str) -> Path:
        return self.rules / f"{rule_id}.json"

    def learning_md(self, learning_id: str) -> Path:
        return self.learnings / f"{learning_id}.md"

    def skill_dir(self, skill_id: str) -> Path:
        return self.skills / skill_id

    def skill_md(self, skill_id: str) -> Path:
        return self.skill_dir(skill_id) / "SKILL.md"
