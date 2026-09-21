"""SQLite derived index with FTS5 (PRD §58 / M8)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from retornatus.infrastructure.persistence.paths import RetornatusPaths
from retornatus.infrastructure.persistence.repository import FileRepository


SCHEMA = """
CREATE TABLE IF NOT EXISTS entities (
    id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    title TEXT,
    change_id TEXT,
    path TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS relations (
    source_id TEXT NOT NULL,
    type TEXT NOT NULL,
    target_id TEXT NOT NULL
);
CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
    id,
    kind,
    body,
    tokenize = 'porter'
);
"""


class RetornatusIndex:
    def __init__(self, root: Path) -> None:
        self.paths = RetornatusPaths(root)
        self.repo = FileRepository(root)

    def connect(self) -> sqlite3.Connection:
        self.paths.index_db.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.paths.index_db)
        conn.executescript(SCHEMA)
        return conn

    def rebuild(self) -> int:
        """Rebuild derived index from canonical files. Returns entity count."""
        if self.paths.index_db.exists():
            self.paths.index_db.unlink()
        conn = self.connect()
        count = 0
        try:
            for change_id in self.repo.list_change_ids():
                change, _ = self.repo.load_change(change_id)
                count += self._upsert(
                    conn,
                    change.id,
                    "change",
                    change.title,
                    change_id,
                    str(self.paths.change_json(change_id)),
                    f"{change.title}\n{change.demand.statement}",
                )
                # situation
                try:
                    _, body, _ = self.repo.load_situation(change_id)
                    count += self._upsert(
                        conn,
                        f"{change_id}/situation",
                        "situation",
                        "Situation",
                        change_id,
                        str(self.paths.situation_md(change_id)),
                        body,
                    )
                except FileNotFoundError:
                    pass

                actions_dir = self.paths.change_dir(change_id) / "actions"
                if actions_dir.is_dir():
                    for path in actions_dir.glob("A-*.json"):
                        action, _ = self.repo.load_action(f"{change_id}/{path.stem}")
                        count += self._upsert(
                            conn,
                            action.id,
                            "action",
                            action.objective,
                            change_id,
                            str(path),
                            action.objective + "\n" + "\n".join(action.success_conditions),
                        )
                        for rel in action.relations:
                            conn.execute(
                                "INSERT INTO relations(source_id, type, target_id) VALUES (?,?,?)",
                                (action.id, rel.type.value, rel.target_id),
                            )

            for learning in self.repo.list_learnings():
                _, body, _ = self.repo.load_learning(learning.id)
                count += self._upsert(
                    conn,
                    learning.id,
                    "learning",
                    learning.title,
                    None,
                    str(self.paths.learning_md(learning.id)),
                    f"{learning.title}\n{learning.summary or ''}\n{body}",
                )

            for rule in self.repo.list_rules():
                count += self._upsert(
                    conn,
                    rule.id,
                    "rule",
                    rule.statement,
                    None,
                    str(self.paths.rule_json(rule.id)),
                    f"{rule.statement}\n{rule.applicability}",
                )

            for skill in self.repo.list_skills():
                _, body, _ = self.repo.load_skill(skill.id)
                count += self._upsert(
                    conn,
                    skill.id,
                    "skill",
                    skill.title,
                    skill.change_id,
                    str(self.paths.skill_md(skill.id)),
                    f"{skill.title}\n{skill.specialization}\n{body}",
                )

            conn.commit()
        finally:
            conn.close()
        return count

    def _upsert(
        self,
        conn: sqlite3.Connection,
        entity_id: str,
        kind: str,
        title: str | None,
        change_id: str | None,
        path: str,
        body: str,
    ) -> int:
        conn.execute(
            "INSERT OR REPLACE INTO entities(id, kind, title, change_id, path) VALUES (?,?,?,?,?)",
            (entity_id, kind, title, change_id, path),
        )
        conn.execute(
            "INSERT INTO documents_fts(id, kind, body) VALUES (?,?,?)",
            (entity_id, kind, body),
        )
        return 1

    def search(self, query: str, *, limit: int = 20) -> list[dict[str, str]]:
        if not self.paths.index_db.is_file():
            self.rebuild()
        conn = self.connect()
        try:
            rows = conn.execute(
                """
                SELECT documents_fts.id, documents_fts.kind, entities.title
                FROM documents_fts
                JOIN entities ON entities.id = documents_fts.id
                WHERE documents_fts MATCH ?
                LIMIT ?
                """,
                (query, limit),
            ).fetchall()
            return [
                {"id": r[0], "kind": r[1], "title": r[2] or ""}
                for r in rows
            ]
        finally:
            conn.close()
