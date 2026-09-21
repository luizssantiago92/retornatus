"""Host Execution records — observe Environment work without orchestrating agents.

Retornatus does not run Cursor/Claude/Codex. It records that Host work happened
so Assurance and continuity can reference an attributable Execution boundary.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from pydantic import Field

from retornatus.domain.base import DomainModel
from retornatus.domain.relations import Relation, RelationType
from retornatus.infrastructure.persistence.atomic import atomic_write_bytes
from retornatus.infrastructure.persistence.paths import RetornatusPaths
from retornatus.infrastructure.persistence.serializers import dump_json_model


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class HostExecutionRecord(DomainModel):
    """Durable observation of a Host/Environment execution for an Action."""

    id: str = Field(min_length=1)
    action_id: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    ok: bool = True
    artifact_paths: list[str] = Field(default_factory=list)
    producer: str = "host"
    recorded_at: datetime = Field(default_factory=_utc_now)
    subject_state: str | None = None
    relations: list[Relation] = Field(default_factory=list)


class HostExecutionService:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.paths = RetornatusPaths(self.root)

    def _executions_dir(self) -> Path:
        dest = self.paths.runtime / "executions"
        dest.mkdir(parents=True, exist_ok=True)
        return dest

    def next_id(self) -> str:
        existing = list(self._executions_dir().glob("X-*.json"))
        nums: list[int] = []
        for path in existing:
            try:
                nums.append(int(path.stem.split("-", 1)[1]))
            except (IndexError, ValueError):
                continue
        return f"X-{max(nums, default=0) + 1:04d}"

    def record(
        self,
        *,
        action_id: str,
        summary: str,
        ok: bool = True,
        artifact_paths: list[str] | None = None,
        producer: str = "host",
        subject_state: str | None = None,
        capture_git: bool = True,
    ) -> HostExecutionRecord:
        from retornatus.application.assurance.subject_state import capture_subject_state

        state = subject_state
        if state is None and capture_git:
            state = capture_subject_state(self.root, use_git=True)

        record = HostExecutionRecord(
            id=self.next_id(),
            action_id=action_id,
            summary=summary,
            ok=ok,
            artifact_paths=list(artifact_paths or []),
            producer=producer,
            subject_state=state,
            relations=[
                Relation(type=RelationType.APPLIES_TO, target_id=action_id),
            ],
        )
        path = self._executions_dir() / f"{record.id}.json"
        atomic_write_bytes(path, dump_json_model(record))
        return record

    def list_for_action(self, action_id: str) -> list[HostExecutionRecord]:
        items: list[HostExecutionRecord] = []
        for path in sorted(self._executions_dir().glob("X-*.json")):
            raw = path.read_text(encoding="utf-8")
            record = HostExecutionRecord.model_validate_json(raw)
            if record.action_id == action_id:
                items.append(record)
        return items
