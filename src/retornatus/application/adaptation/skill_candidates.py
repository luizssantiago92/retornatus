"""Queue skill suggestions from repeated evidence. Never create a Skill here.

The detector is deterministic. It does not call a model.

Signals, scored against ``[adaptation.skill_candidates]``:

* **sequence** — the same normalized evidence-command sequence appears in at
  least ``sequence_min_count`` Changes that have green executed evidence.
* **retry** — executed evidence failed, and a later run on that Change exited 0.
* **correction** — the same user-correction pattern appears at least
  ``correction_min_count`` times.

User utterances are not stored on a Change. The correction signal runs only
when the caller passes text, which the stop hook does when the host payload
includes ``transcript_path``. A scan of recorded Changes uses sequence and
retry only. An empty result is normal.

Ids, hashes, dates, pull-request numbers, and bare numbers collapse to
variables before sequences are compared. An absolute path keeps its file name
(``<PATH>/migrate.py``) so two different scripts do not become one step, and
the same script under two directories still matches. Stable relative paths
stay, so ``python scripts/migrate.py`` can match across Changes.
Owner-declared ``required_checks`` are the project gate, not a specialization,
and are left out of the sequence. Changes whose title, demand, or contract
match ``_TRIVIAL_MARKERS`` are left out too.

A candidate is a file under ``.retornatus/adaptation/skill-candidates/``.
``skill accept`` is the only command that writes a draft Skill.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from retornatus.application.adaptation.skill_need import _TRIVIAL_MARKERS
from retornatus.application.adaptation.skills import SkillService
from retornatus.application.assurance.evidence import EvidenceService
from retornatus.application.assurance.settings import load_project_config, load_required_checks
from retornatus.domain.enums import EvidenceProvenance, SkillStatus
from retornatus.domain.models import Evidence, Skill
from retornatus.infrastructure.persistence.concurrency import ArtifactRevision
from retornatus.infrastructure.persistence.repository import FileRepository

_CANDIDATE_ID = re.compile(r"K-\d{4}")
_UUID = re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.I)
_OWNED_ID = re.compile(r"\bC-\d+/[A-Za-z0-9_.-]+\b")
_PROJECT_ID = re.compile(r"\b(?:C|A|E|S|Q|F|L|R|D|T|K)-\d+\b")
_DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?Z?)?\b")
_PR = re.compile(r"#\d+\b")
_HASH = re.compile(r"\b[0-9a-f]{7,64}\b", re.I)
_NUMBER = re.compile(r"\b\d+\b")
_REPORT_TOKEN = re.compile(
    r"\b(?:C|A|E|S|Q|F|L|R|D|T|K)-\d+\b|#\d+\b|\b\d{4}-\d{2}-\d{2}\b|\b[0-9a-f]{7,64}\b|\bPR\b",
    re.I,
)
_CORRECTION = re.compile(
    r"(?P<use>\bno,?\s+use\b|\bn[aã]o,?\s+use\b|\bnao,?\s+use\b)"
    r"|(?P<dont>\bdon['’]t\b|\bdont\b|\bdo not\b)"
    r"|(?P<actually>\bactually\b|\bna verdade\b)",
    re.IGNORECASE,
)
_TOKEN = re.compile(r"[A-Za-z][A-Za-z0-9_-]{4,}")
_NARRATIVE_PROGRAMS = frozenset({"echo", "printf", "cat", "true", "false"})
_TOKEN_STOPWORDS = frozenset(
    {
        "run",
        "python",
        "pytest",
        "check",
        "test",
        "tests",
        "true",
        "false",
        "echo",
        "print",
        "with",
        "from",
        "that",
        "this",
        "into",
        "bash",
        "exec",
        "command",
        "commands",
        "script",
        "scripts",
        "repeated",
        "procedure",
        "evidence",
        "green",
        "skill",
        "skills",
    }
)
_STATUSES = frozenset({"pending", "accepted", "rejected"})
_SESSION_NAME = "skill-candidate-sessions.json"


@dataclass(frozen=True)
class SkillCandidateSettings:
    """Score threshold and limits from ``[adaptation.skill_candidates]``."""

    enabled: bool = True
    threshold: int = 3
    sequence_min_count: int = 3
    sequence_points: int = 3
    retry_points: int = 2
    correction_min_count: int = 2
    correction_points: int = 2
    max_per_session: int = 1
    reject_rearm_count: int = 2


@dataclass(frozen=True)
class SkillCandidate:
    """One queued suggestion. Accept and reject are the only transitions."""

    id: str
    status: str
    kind: str
    theme_key: str
    title: str
    reason: str
    score: int
    signals: tuple[str, ...]
    origin_changes: tuple[str, ...]
    commands: tuple[str, ...]
    count: int
    existing_skill_id: str | None
    created_at: str
    resolved_skill_id: str | None = None
    resolved_at: str | None = None
    revision: ArtifactRevision | None = None

    def to_meta(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "id": self.id,
            "status": self.status,
            "kind": self.kind,
            "theme_key": self.theme_key,
            "title": self.title,
            "reason": self.reason,
            "score": self.score,
            "signals": list(self.signals),
            "origin_changes": list(self.origin_changes),
            "commands": list(self.commands),
            "count": self.count,
            "existing_skill_id": self.existing_skill_id,
            "created_at": self.created_at,
            "resolved_skill_id": self.resolved_skill_id,
            "resolved_at": self.resolved_at,
        }


@dataclass(frozen=True)
class ScanResult:
    """Outcome of one detector pass. ``created_id`` is None when nothing is queued."""

    created_id: str | None
    notice: str
    skipped_reason: str | None = None


@dataclass(frozen=True)
class AcceptResult:
    """What ``skill accept`` wrote. ``action`` is ``created`` or ``evolved``."""

    candidate_id: str
    action: str
    skill_id: str
    skill_version: int
    skill_status: str


@dataclass(frozen=True)
class _ChangeView:
    change_id: str
    trivial: bool
    green: bool
    sequence: tuple[str, ...]
    raw_lines: tuple[str, ...]
    retried: tuple[str, ...]
    raw_retried: tuple[str, ...]

    @property
    def retry(self) -> bool:
        return bool(self.retried)


@dataclass(frozen=True)
class _Proposal:
    theme_key: str
    title: str
    reason: str
    score: int
    signals: tuple[str, ...]
    origin_changes: tuple[str, ...]
    commands: tuple[str, ...]
    count: int
    kind: str
    existing_skill_id: str | None


def load_skill_candidate_settings(root: Path) -> SkillCandidateSettings:
    """Read the score table. Missing keys keep the defaults. Bad types raise."""
    data = load_project_config(root)
    adaptation = data.get("adaptation")
    table: dict[str, Any] = {}
    if isinstance(adaptation, dict):
        nested = adaptation.get("skill_candidates")
        if nested is None:
            table = {}
        elif isinstance(nested, dict):
            table = nested
        else:
            raise ValueError("Invalid [adaptation.skill_candidates]: expected a table")
    elif adaptation is not None:
        raise ValueError("Invalid [adaptation]: expected a table")
    enabled = True
    if "enabled" in table:
        raw_enabled = table["enabled"]
        if not isinstance(raw_enabled, bool):
            raise ValueError("Invalid [adaptation.skill_candidates] enabled: expected true or false")
        enabled = raw_enabled
    return SkillCandidateSettings(
        enabled=enabled,
        threshold=_require_int(table, "threshold", 3, minimum=1),
        sequence_min_count=_require_int(table, "sequence_min_count", 3, minimum=1),
        sequence_points=_require_int(table, "sequence_points", 3, minimum=0),
        retry_points=_require_int(table, "retry_points", 2, minimum=0),
        correction_min_count=_require_int(table, "correction_min_count", 2, minimum=1),
        correction_points=_require_int(table, "correction_points", 2, minimum=0),
        max_per_session=_require_int(table, "max_per_session", 1, minimum=0),
        reject_rearm_count=_require_int(table, "reject_rearm_count", 2, minimum=1),
    )


def normalize_command(argv: Sequence[str]) -> str:
    """Collapse variable tokens so two runs of the same procedure compare equal.

    An absolute path becomes ``<PATH>/<filename>``. A stable relative path is
    kept so the repeated step is still visible. Ids, hashes, dates,
    pull-request numbers, and bare numbers become variables.
    """
    parts = [_normalize_token(token) for token in argv if token]
    return " ".join(part for part in parts if part)


def looks_like_report(command_lines: Sequence[str]) -> bool:
    """True when the text is identifiers and dates without a reusable program.

    Three or more ids, dates, pull-request numbers, or hashes, and no program
    other than ``echo`` / ``printf`` / ``cat`` / ``true`` / ``false``.
    """
    raw = " ".join(command_lines).strip()
    if not raw:
        return False
    if len(_REPORT_TOKEN.findall(raw)) < 3:
        return False
    return not _has_reusable_step(command_lines)


def correction_counts(texts: Sequence[str]) -> dict[str, int]:
    """Count correction patterns. Keys are ``use-correction``, ``dont``, and ``actually``."""
    counts = {"use-correction": 0, "dont": 0, "actually": 0}
    for text in texts:
        for match in _CORRECTION.finditer(text):
            if match.group("use"):
                counts["use-correction"] += 1
            elif match.group("dont"):
                counts["dont"] += 1
            elif match.group("actually"):
                counts["actually"] += 1
    return counts


def user_texts_from_transcript(path: Path) -> list[str]:
    """User lines from a host JSONL transcript. Missing or unreadable files yield [].

    The line schema is not a stable contract. Objects whose role or type is
    ``user`` or ``human`` contribute text. Anything else is ignored.
    """
    try:
        if not path.is_file():
            return []
        raw = path.read_bytes()
    except OSError:
        return []
    if len(raw) > 1_000_000:
        raw = raw[-1_000_000:]
        newline = raw.find(b"\n")
        if newline == -1:
            return []
        raw = raw[newline + 1 :]
    texts: list[str] = []
    for line in raw.decode("utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            message = _user_line_text(parsed)
            if message:
                texts.append(message)
    return texts


def user_texts_from_payload(payload: Mapping[str, Any]) -> list[str]:
    """User lines from ``transcript_path`` when the host sent one."""
    path = payload.get("transcript_path")
    if not isinstance(path, str) or not path.strip():
        return []
    return user_texts_from_transcript(Path(path).expanduser())


def list_candidates(root: Path) -> list[SkillCandidate]:
    """Every readable candidate, pending first, then by id."""
    repo = FileRepository(root)
    directory = repo.paths.skill_candidates
    if not directory.is_dir():
        return []
    items: list[SkillCandidate] = []
    for path in sorted(directory.glob("K-*.md")):
        try:
            meta, _body, revision = repo.load_markdown(path)
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        item = _parse_candidate(meta, revision)
        if item is not None:
            items.append(item)
    rank = {"pending": 0, "accepted": 1, "rejected": 2}
    items.sort(key=lambda candidate: (rank.get(candidate.status, 9), candidate.id))
    return items


def pending_notice(root: Path) -> str:
    """One line for hooks. Empty when the queue has no pending candidate."""
    try:
        settings = load_skill_candidate_settings(root)
        if not settings.enabled:
            return ""
        pending = [item for item in list_candidates(root) if item.status == "pending"]
    except (OSError, ValueError, json.JSONDecodeError):
        return ""
    count = len(pending)
    if count == 0:
        return ""
    if count == 1:
        return "1 skill candidate pending: run `retornatus skill candidates`"
    return f"{count} skill candidates pending: run `retornatus skill candidates`"


def format_candidates(items: Sequence[SkillCandidate]) -> str:
    """Text for ``skill candidates``. An empty queue is a normal result."""
    if not items:
        return "No skill candidates."
    return "\n".join(_format_candidate(item) for item in items)


def scan_skill_candidates(
    root: Path,
    *,
    focal_change_id: str | None = None,
    session_id: str | None = None,
    user_texts: Sequence[str] | None = None,
) -> ScanResult:
    """Score green Changes and queue at most one candidate for this session.

    Nothing to suggest is a normal result (``created_id`` is None).
    """
    settings = load_skill_candidate_settings(root)
    if not settings.enabled:
        return ScanResult(created_id=None, notice="", skipped_reason="disabled")
    proposals, skipped = _propose(
        root,
        settings,
        focal_change_id=focal_change_id,
        user_texts=list(user_texts or []),
    )
    if not proposals:
        return ScanResult(created_id=None, notice=pending_notice(root), skipped_reason=skipped)
    session = _session_key(session_id)
    existing = list_candidates(root)
    blocked = "nothing"
    for proposal in proposals:
        theme_block = _theme_blocked(existing, proposal, settings.reject_rearm_count)
        if theme_block:
            blocked = theme_block
            continue
        if _session_count(root, session) >= settings.max_per_session:
            return ScanResult(created_id=None, notice=pending_notice(root), skipped_reason="session-limit")
        created = _write_new(FileRepository(root), proposal)
        _increment_session(root, session)
        return ScanResult(created_id=created.id, notice=pending_notice(root), skipped_reason=None)
    return ScanResult(created_id=None, notice=pending_notice(root), skipped_reason=blocked)


def notice_for_allowed_stop(root: Path, payload: Mapping[str, Any], focal_change_ids: Sequence[str]) -> str:
    """Scan, then return the pending line once per session. Failures return "".

    ``loop_count`` >= 1 means the host already continued this turn, so the
    line is omitted. The Assurance decision is the caller's job.
    """
    try:
        settings = load_skill_candidate_settings(root)
        if not settings.enabled:
            return ""
        session = _session_key(_payload_session_id(payload))
        scan_skill_candidates(
            root,
            focal_change_id=focal_change_ids[-1] if focal_change_ids else None,
            session_id=session,
            user_texts=user_texts_from_payload(payload),
        )
        loop_count = payload.get("loop_count")
        if isinstance(loop_count, int) and loop_count >= 1:
            return ""
        if _was_notified(root, session):
            return ""
        notice = pending_notice(root)
        if not notice:
            return ""
        _mark_notified(root, session)
        return notice
    except (OSError, ValueError, json.JSONDecodeError, RuntimeError):
        return ""


def accept_candidate(root: Path, candidate_id: str) -> AcceptResult:
    """Write a draft Skill, or evolve the skill the candidate named. Pending only."""
    repo = FileRepository(root)
    item = _require(repo, candidate_id)
    if item.status != "pending":
        raise ValueError(f"{item.id} is {item.status}; only a pending candidate can be accepted")
    if item.kind == "improve" and item.existing_skill_id:
        note = item.reason.replace("|", "/")[:240] or "Accepted repetition candidate"
        append = _evolve_append(item)
        skill = SkillService(root).evolve(item.existing_skill_id, note=note, body_append=append)
        action = "evolved"
    else:
        steps = [f"Run `{command}` and record the result with evidence run." for command in item.commands]
        if not steps:
            steps = ["Confirm the repeated situation with the user, then follow the accepted candidate."]
        first_change = item.origin_changes[0] if item.origin_changes else None
        shown = item.commands[0] if item.commands else item.title
        skill, _body = SkillService(root).create_for_specialization(
            specialization=_specialization_text(item),
            title=item.title,
            description=f"Use when this evidence-command sequence shows up again: {shown}",
            change_id=first_change,
            research_seed=_research_seed(item),
            procedure_steps=steps,
        )
        action = "created"
    updated = SkillCandidate(
        id=item.id,
        status="accepted",
        kind=item.kind,
        theme_key=item.theme_key,
        title=item.title,
        reason=item.reason,
        score=item.score,
        signals=item.signals,
        origin_changes=item.origin_changes,
        commands=item.commands,
        count=item.count,
        existing_skill_id=item.existing_skill_id,
        created_at=item.created_at,
        resolved_skill_id=skill.id,
        resolved_at=_now(),
        revision=item.revision,
    )
    _save(repo, updated, expected=item.revision)
    return AcceptResult(
        candidate_id=item.id,
        action=action,
        skill_id=skill.id,
        skill_version=skill.version,
        skill_status=skill.status.value,
    )


def reject_candidate(root: Path, candidate_id: str) -> SkillCandidate:
    """Mark a pending candidate rejected. The same theme waits for new occurrences."""
    repo = FileRepository(root)
    item = _require(repo, candidate_id)
    if item.status != "pending":
        raise ValueError(f"{item.id} is {item.status}; only a pending candidate can be rejected")
    updated = SkillCandidate(
        id=item.id,
        status="rejected",
        kind=item.kind,
        theme_key=item.theme_key,
        title=item.title,
        reason=item.reason,
        score=item.score,
        signals=item.signals,
        origin_changes=item.origin_changes,
        commands=item.commands,
        count=item.count,
        existing_skill_id=item.existing_skill_id,
        created_at=item.created_at,
        resolved_skill_id=None,
        resolved_at=_now(),
        revision=item.revision,
    )
    _save(repo, updated, expected=item.revision)
    return updated


def _propose(
    root: Path,
    settings: SkillCandidateSettings,
    *,
    focal_change_id: str | None,
    user_texts: list[str],
) -> tuple[list[_Proposal], str]:
    """Ranked proposals that clear the threshold and are not status reports."""
    views = _load_views(root)
    focal = next((view for view in views if view.change_id == focal_change_id), None)
    bucket, bucket_count = _top_correction(user_texts)
    correction_hit = bucket is not None and bucket_count >= settings.correction_min_count
    ranked = _qualifying_sequences(views, settings.sequence_min_count)
    proposals: list[_Proposal] = []
    reports = 0
    below = False
    for sequence, cluster_ids in ranked:
        cluster_views = [view for view in views if view.change_id in set(cluster_ids)]
        raw_lines = cluster_views[0].raw_lines if cluster_views else ()
        if raw_lines and looks_like_report(raw_lines):
            reports += 1
            continue
        signals = ["sequence"]
        score = settings.sequence_points
        origins = list(cluster_ids)
        cluster_retry = _cluster_retry(views, cluster_ids)
        if cluster_retry is not None:
            signals.append("retry")
            score += settings.retry_points
        if correction_hit:
            signals.append("correction")
            score += settings.correction_points
        if score < settings.threshold:
            below = True
            continue
        proposals.append(
            _make_proposal(
                root,
                commands=sequence,
                origins=origins,
                signals=signals,
                score=score,
                count=len(cluster_ids),
                bucket=bucket,
                bucket_count=bucket_count,
                theme_key="sequence:" + " | ".join(sequence),
            )
        )
    if ranked:
        if proposals:
            return proposals, "ok"
        if reports:
            return [], "report"
        if below:
            return [], "below-threshold"
        return [], "nothing"
    fallback, skipped = _fallback_proposal(
        root,
        settings,
        focal=focal,
        user_texts=user_texts,
        bucket=bucket,
        bucket_count=bucket_count,
        correction_hit=correction_hit,
    )
    if fallback is None:
        return [], skipped
    return [fallback], "ok"


def _fallback_proposal(
    root: Path,
    settings: SkillCandidateSettings,
    *,
    focal: _ChangeView | None,
    user_texts: list[str],
    bucket: str | None,
    bucket_count: int,
    correction_hit: bool,
) -> tuple[_Proposal | None, str]:
    """Retry and correction when no command sequence repeats often enough."""
    signals: list[str] = []
    score = 0
    commands: tuple[str, ...] = ()
    raw_lines: tuple[str, ...] = ()
    origins: list[str] = []
    count = 0
    if focal is not None and focal.retry and not focal.trivial and focal.green:
        signals.append("retry")
        score += settings.retry_points
        commands = focal.retried
        raw_lines = focal.raw_retried
        origins = [focal.change_id]
        count = 1
    if correction_hit:
        signals.append("correction")
        score += settings.correction_points
        if count == 0:
            count = bucket_count
        if focal is not None and focal.change_id not in origins:
            origins.append(focal.change_id)
    if score <= 0:
        return None, "nothing"
    if score < settings.threshold:
        return None, "below-threshold"
    if raw_lines and looks_like_report(raw_lines):
        return None, "report"
    if not raw_lines and user_texts and looks_like_report(user_texts):
        return None, "report"
    theme_key = "retry:" + " | ".join(commands) if "retry" in signals else f"correction:{bucket}"
    return (
        _make_proposal(
            root,
            commands=commands,
            origins=origins,
            signals=signals,
            score=score,
            count=count,
            bucket=bucket,
            bucket_count=bucket_count,
            theme_key=theme_key,
        ),
        "ok",
    )


def _make_proposal(
    root: Path,
    *,
    commands: tuple[str, ...],
    origins: list[str],
    signals: list[str],
    score: int,
    count: int,
    bucket: str | None,
    bucket_count: int,
    theme_key: str,
) -> _Proposal:
    match = _matching_skill(root, commands)
    skill_id = match.id if match is not None else None
    sequence_count = count if "sequence" in signals else 0
    return _Proposal(
        theme_key=theme_key,
        title=_title_from_commands(commands),
        reason=_reason(
            signals=signals,
            sequence_count=sequence_count,
            bucket=bucket,
            bucket_count=bucket_count,
            skill_id=skill_id,
        ),
        score=score,
        signals=tuple(signals),
        origin_changes=tuple(origins),
        commands=commands,
        count=count,
        kind="improve" if match is not None else "new",
        existing_skill_id=skill_id,
    )


def _qualifying_sequences(
    views: Sequence[_ChangeView],
    minimum: int,
) -> list[tuple[tuple[str, ...], tuple[str, ...]]]:
    groups: dict[tuple[str, ...], list[str]] = {}
    for view in views:
        if view.trivial or not view.green or not view.sequence:
            continue
        groups.setdefault(view.sequence, []).append(view.change_id)
    ranked: list[tuple[tuple[str, ...], tuple[str, ...]]] = []
    for sequence, change_ids in groups.items():
        if len(change_ids) < minimum:
            continue
        ranked.append((sequence, tuple(change_ids)))
    ranked.sort(key=lambda item: (len(item[1]), len(item[0]), item[0]), reverse=True)
    return ranked


def _cluster_retry(views: Sequence[_ChangeView], cluster_ids: Sequence[str]) -> _ChangeView | None:
    cluster = set(cluster_ids)
    for view in views:
        if view.change_id in cluster and view.retry and not view.trivial:
            return view
    return None


def _top_correction(texts: Sequence[str]) -> tuple[str | None, int]:
    counts = correction_counts(texts)
    bucket: str | None = None
    best = 0
    for name in ("use-correction", "dont", "actually"):
        count = counts[name]
        if count > best:
            bucket = name
            best = count
    return bucket, best


def _reason(
    *,
    signals: Sequence[str],
    sequence_count: int,
    bucket: str | None,
    bucket_count: int,
    skill_id: str | None,
) -> str:
    parts: list[str] = []
    if "sequence" in signals:
        parts.append(f"The same evidence-command sequence appears in {sequence_count} Changes with green evidence.")
    if "retry" in signals:
        parts.append("Evidence failed and a later run exited 0.")
    if "correction" in signals and bucket is not None:
        parts.append(f"The same user correction ({bucket}) appears {bucket_count} times.")
    if skill_id:
        parts.append(f"Existing skill {skill_id} already covers this theme; proposing an update.")
    return " ".join(parts)


def _theme_blocked(existing: Sequence[SkillCandidate], proposal: _Proposal, rearm: int) -> str | None:
    same = [item for item in existing if item.theme_key == proposal.theme_key]
    if any(item.status == "pending" for item in same):
        return "pending-exists"
    if any(item.status == "accepted" for item in same):
        return "accepted-exists"
    rejected = [item for item in same if item.status == "rejected"]
    if not rejected:
        return None
    seen: set[str] = set()
    for item in rejected:
        seen.update(item.origin_changes)
    if proposal.origin_changes:
        fresh = [change_id for change_id in proposal.origin_changes if change_id not in seen]
        if len(fresh) < rearm:
            return "rejected-wait"
        return None
    prior = max(item.count for item in rejected)
    if proposal.count < prior + rearm:
        return "rejected-wait"
    return None


def _load_views(root: Path) -> list[_ChangeView]:
    repo = FileRepository(root)
    required_raw, required_norm = _required_commands(root)
    evidence = EvidenceService(root)
    views: list[_ChangeView] = []
    try:
        change_ids = repo.list_change_ids()
    except OSError:
        return []
    for change_id in change_ids:
        try:
            view = _view_for(repo, evidence, change_id, required_raw, required_norm)
        except (OSError, ValueError):
            continue
        if view is not None:
            views.append(view)
    return views


def _view_for(
    repo: FileRepository,
    evidence: EvidenceService,
    change_id: str,
    required_raw: set[tuple[str, ...]],
    required_norm: set[str],
) -> _ChangeView | None:
    change, _revision = repo.load_change(change_id)
    parts = [change.title, change.demand.statement]
    try:
        loaded, _contract_rev = repo.load_contract(change_id)
    except (OSError, ValueError):
        loaded = None
    if loaded is not None:
        parts.append(loaded.what)
    trivial = _TRIVIAL_MARKERS.search(" ".join(parts)) is not None
    items = [
        item
        for item in evidence.list_for_change(change_id)
        if item.provenance == EvidenceProvenance.EXECUTED and item.command
    ]
    items.sort(key=lambda item: (item.observed_at, item.id))
    if not any(item.exit_code == 0 and not item.timed_out for item in items):
        return None
    sequence: list[str] = []
    raw_lines: list[str] = []
    for item in items:
        if item.exit_code != 0 or item.timed_out:
            continue
        argv = list(item.command or [])
        if _is_required(argv, required_raw, required_norm):
            continue
        normalized = normalize_command(argv)
        if not normalized:
            continue
        if sequence and sequence[-1] == normalized:
            continue
        sequence.append(normalized)
        raw_lines.append(" ".join(argv))
    retried, raw_retried = _retried_commands(items, required_raw, required_norm)
    return _ChangeView(
        change_id=change_id,
        trivial=trivial,
        green=True,
        sequence=tuple(sequence),
        raw_lines=tuple(raw_lines),
        retried=tuple(retried),
        raw_retried=tuple(raw_retried),
    )


def _retried_commands(
    items: Sequence[Evidence],
    required_raw: set[tuple[str, ...]],
    required_norm: set[str],
) -> tuple[list[str], list[str]]:
    failed_norm: list[str] = []
    failed_raw: list[str] = []
    saw_failure = False
    recovered = False
    for item in items:
        argv = list(item.command or [])
        failed = item.timed_out or (item.exit_code is not None and item.exit_code != 0)
        if failed:
            saw_failure = True
            if not _is_required(argv, required_raw, required_norm):
                normalized = normalize_command(argv)
                if normalized and normalized not in failed_norm:
                    failed_norm.append(normalized)
                    failed_raw.append(" ".join(argv))
        elif item.exit_code == 0 and saw_failure:
            recovered = True
    if not recovered:
        return [], []
    return failed_norm, failed_raw


def _required_commands(root: Path) -> tuple[set[tuple[str, ...]], set[str]]:
    raw: set[tuple[str, ...]] = set()
    normalized: set[str] = set()
    try:
        checks = load_required_checks(root)
    except (OSError, ValueError):
        return raw, normalized
    for check in checks:
        argv = tuple(check.run)
        raw.add(argv)
        text = normalize_command(check.run)
        if text:
            normalized.add(text)
    return raw, normalized


def _is_required(argv: Sequence[str], raw: set[tuple[str, ...]], normalized: set[str]) -> bool:
    if tuple(argv) in raw:
        return True
    return normalize_command(argv) in normalized


def _matching_skill(root: Path, commands: Sequence[str]) -> Skill | None:
    tokens = _significant_tokens(" ".join(commands))
    if not tokens:
        return None
    best: Skill | None = None
    best_score = 0
    for skill in FileRepository(root).list_skills():
        if skill.status is SkillStatus.SUPERSEDED:
            continue
        hay = " ".join([skill.name, skill.title, skill.description, skill.specialization]).lower()
        score = sum(1 for token in tokens if token in hay)
        if score > best_score:
            best = skill
            best_score = score
    if best_score < 1:
        return None
    return best


def _significant_tokens(text: str) -> set[str]:
    tokens: set[str] = set()
    for raw in _TOKEN.findall(text):
        word = raw.lower()
        if word in _TOKEN_STOPWORDS or word.startswith("<"):
            continue
        tokens.add(word)
        for part in re.split(r"[_-]", word):
            if len(part) >= 5 and part not in _TOKEN_STOPWORDS:
                tokens.add(part)
    return tokens


def _title_from_commands(commands: Sequence[str]) -> str:
    if not commands:
        return "Repeated user correction"
    shown = commands[0]
    if len(shown) > 80:
        shown = shown[:77] + "..."
    return f"Repeated procedure: {shown}"


def _specialization_text(item: SkillCandidate) -> str:
    if item.commands:
        joined = "; ".join(item.commands)
        return f"Repeated evidence commands that already succeeded: {joined}"
    return item.reason or item.title


def _research_seed(item: SkillCandidate) -> str:
    origins = ", ".join(item.origin_changes) or "(none)"
    commands = "; ".join(item.commands) or "(none)"
    return (
        f"The human accepted repetition candidate {item.id}. "
        f"Origin Changes: {origins}. Repeated commands: {commands}. "
        "Research current official documentation for these commands before activation. "
        "Record source URLs and access dates."
    )


def _evolve_append(item: SkillCandidate) -> str:
    lines = [
        f"Accepted candidate {item.id}.",
        "Origin Changes: " + (", ".join(item.origin_changes) or "(none)"),
        "Repeated commands:",
    ]
    if item.commands:
        lines.extend(f"- `{command}`" for command in item.commands)
    else:
        lines.append("- (none)")
    return "\n".join(lines)


def _write_new(repo: FileRepository, proposal: _Proposal) -> SkillCandidate:
    existing = list_candidates(repo.paths.root)
    numbers: list[int] = []
    for item in existing:
        match = _CANDIDATE_ID.fullmatch(item.id)
        if match:
            numbers.append(int(item.id.split("-", 1)[1]))
    candidate_id = f"K-{max(numbers, default=0) + 1:04d}"
    item = SkillCandidate(
        id=candidate_id,
        status="pending",
        kind=proposal.kind,
        theme_key=proposal.theme_key,
        title=proposal.title,
        reason=proposal.reason,
        score=proposal.score,
        signals=proposal.signals,
        origin_changes=proposal.origin_changes,
        commands=proposal.commands,
        count=proposal.count,
        existing_skill_id=proposal.existing_skill_id,
        created_at=_now(),
    )
    _save(repo, item, expected=None)
    return item


def _save(repo: FileRepository, item: SkillCandidate, *, expected: ArtifactRevision | None) -> None:
    repo.paths.skill_candidates.mkdir(parents=True, exist_ok=True)
    repo.save_markdown(
        repo.paths.skill_candidate_md(item.id),
        _render_body(item),
        front_matter=item.to_meta(),
        expected=expected,
    )


def _render_body(item: SkillCandidate) -> str:
    changes = "\n".join(f"- `{change_id}`" for change_id in item.origin_changes) or "- (none)"
    commands = "\n".join(f"- `{command}`" for command in item.commands) or "- (none)"
    skill = item.existing_skill_id or "(new skill)"
    signals = ", ".join(item.signals) or "(none)"
    return (
        f"# {item.id} — {item.title}\n\n"
        f"Status: {item.status}\n\n"
        f"Kind: {item.kind} ({skill})\n\n"
        f"Score: {item.score}\n\n"
        f"Signals: {signals}\n\n"
        "## Reason\n\n"
        f"{item.reason}\n\n"
        "## Origin Changes\n\n"
        f"{changes}\n\n"
        "## Repeated commands\n\n"
        f"{commands}\n"
    )


def _format_candidate(item: SkillCandidate) -> str:
    kind = item.kind
    if item.kind == "improve" and item.existing_skill_id:
        kind = f"improve\t{item.existing_skill_id}"
    changes = ", ".join(item.origin_changes) or "(none)"
    commands = "; ".join(item.commands) or "(none)"
    return (
        f"{item.id}\t{item.status}\t{kind}\tscore={item.score}\tcount={item.count}\t{item.reason}\n"
        f"  changes: {changes}\n"
        f"  commands: {commands}"
    )


def _require(repo: FileRepository, candidate_id: str) -> SkillCandidate:
    if _CANDIDATE_ID.fullmatch(candidate_id) is None:
        raise ValueError(f"Invalid skill candidate id: {candidate_id}")
    path = repo.paths.skill_candidate_md(candidate_id)
    if not path.is_file():
        raise ValueError(f"No skill candidate {candidate_id}")
    meta, _body, revision = repo.load_markdown(path)
    item = _parse_candidate(meta, revision)
    if item is None:
        raise ValueError(f"Skill candidate {candidate_id} is unreadable")
    return item


def _parse_candidate(meta: dict[str, Any] | None, revision: ArtifactRevision | None) -> SkillCandidate | None:
    if not isinstance(meta, dict):
        return None
    candidate_id = meta.get("id")
    status = meta.get("status")
    if not isinstance(candidate_id, str) or _CANDIDATE_ID.fullmatch(candidate_id) is None:
        return None
    if not isinstance(status, str) or status not in _STATUSES:
        return None
    kind = meta.get("kind")
    if kind not in {"new", "improve"}:
        kind = "new"
    return SkillCandidate(
        id=candidate_id,
        status=status,
        kind=str(kind),
        theme_key=_text(meta.get("theme_key")),
        title=_text(meta.get("title")) or candidate_id,
        reason=_text(meta.get("reason")),
        score=_int(meta.get("score")),
        signals=_str_tuple(meta.get("signals")),
        origin_changes=_str_tuple(meta.get("origin_changes")),
        commands=_str_tuple(meta.get("commands")),
        count=_int(meta.get("count")),
        existing_skill_id=_optional_text(meta.get("existing_skill_id")),
        created_at=_text(meta.get("created_at")),
        resolved_skill_id=_optional_text(meta.get("resolved_skill_id")),
        resolved_at=_optional_text(meta.get("resolved_at")),
        revision=revision,
    )


def _text(value: object) -> str:
    return value if isinstance(value, str) else ""


def _optional_text(value: object) -> str | None:
    if isinstance(value, str) and value.strip():
        return value
    return None


def _int(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        return 0
    return value


def _str_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(item for item in value if isinstance(item, str))


def _normalize_token(token: str) -> str:
    if token.startswith("/") or token.startswith("~") or re.match(r"^[A-Za-z]:[\\/]", token):
        name = _path_basename(token)
        if not name:
            return "<PATH>"
        return "<PATH>/" + _normalize_text(name)
    return _normalize_text(token)


def _path_basename(token: str) -> str:
    stripped = token.rstrip("/\\")
    if not stripped or stripped in {"~"}:
        return ""
    return re.split(r"[/\\]", stripped)[-1]


def _normalize_text(token: str) -> str:
    text = _UUID.sub("<UUID>", token)
    text = _OWNED_ID.sub("<ID>", text)
    text = _PROJECT_ID.sub("<ID>", text)
    text = _DATE.sub("<DATE>", text)
    text = _PR.sub("<PR>", text)
    text = _HASH.sub("<HASH>", text)
    text = _NUMBER.sub("<N>", text)
    return text


def _has_reusable_step(command_lines: Sequence[str]) -> bool:
    for line in command_lines:
        parts = line.split()
        if not parts:
            continue
        program = parts[0].lower()
        if program.startswith("<"):
            continue
        if program in _NARRATIVE_PROGRAMS:
            continue
        return True
    return False


def _user_line_text(obj: dict[str, Any]) -> str | None:
    message = obj.get("message")
    kind = obj.get("type")
    role = obj.get("role")
    if isinstance(message, dict):
        if not isinstance(kind, str):
            kind = message.get("type")
        if not isinstance(role, str):
            role = message.get("role")
    labels = [value.strip().casefold() for value in (kind, role) if isinstance(value, str) and value.strip()]
    if not labels or not any(label in {"user", "human"} for label in labels):
        return None
    source = message if isinstance(message, dict) else obj
    chunks = _text_chunks(source.get("text")) + _text_chunks(source.get("content"))
    joined = "\n".join(part.strip() for part in chunks if part and part.strip())
    return joined or None


def _text_chunks(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        chunks: list[str] = []
        for item in value:
            chunks.extend(_text_chunks(item))
        return chunks
    if isinstance(value, dict):
        block_type = value.get("type")
        if isinstance(block_type, str) and block_type.casefold() in {"tool_use", "tool_result", "thinking"}:
            return []
        chunks = []
        for key in ("text", "content"):
            if key in value:
                chunks.extend(_text_chunks(value[key]))
        return chunks
    return []


def _require_int(table: Mapping[str, Any], key: str, default: int, *, minimum: int) -> int:
    if key not in table:
        return default
    raw = table[key]
    if isinstance(raw, bool) or not isinstance(raw, int):
        raise ValueError(f"Invalid [adaptation.skill_candidates] {key}: expected an integer")
    if raw < minimum:
        raise ValueError(f"Invalid [adaptation.skill_candidates] {key}: expected >= {minimum}")
    return raw


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _session_path(root: Path) -> Path:
    return root / ".retornatus" / "runtime" / _SESSION_NAME


def _session_key(session_id: str | None) -> str:
    if session_id is None:
        return "default"
    text = session_id.strip()
    return text[:200] if text else "default"


def _payload_session_id(payload: Mapping[str, Any]) -> str | None:
    for key in ("session_id", "conversation_id", "composer_id"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return None


def _load_session(root: Path) -> dict[str, Any]:
    path = _session_path(root)
    if not path.is_file():
        return {"suggested": {}, "notified": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"suggested": {}, "notified": []}
    if not isinstance(data, dict):
        return {"suggested": {}, "notified": []}
    return data


def _store_session(root: Path, data: Mapping[str, Any]) -> None:
    path = _session_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _session_count(root: Path, session: str) -> int:
    suggested = _load_session(root).get("suggested")
    if not isinstance(suggested, dict):
        return 0
    raw = suggested.get(session, 0)
    if isinstance(raw, bool) or not isinstance(raw, int):
        return 0
    return raw


def _increment_session(root: Path, session: str) -> None:
    data = _load_session(root)
    suggested = data.get("suggested")
    if not isinstance(suggested, dict):
        suggested = {}
    current = suggested.get(session, 0)
    suggested[session] = current + 1 if isinstance(current, int) and not isinstance(current, bool) else 1
    data["suggested"] = suggested
    _store_session(root, data)


def _was_notified(root: Path, session: str) -> bool:
    notified = _load_session(root).get("notified")
    return isinstance(notified, list) and session in notified


def _mark_notified(root: Path, session: str) -> None:
    data = _load_session(root)
    notified = data.get("notified")
    if not isinstance(notified, list):
        notified = []
    if session not in notified:
        notified.append(session)
    data["notified"] = notified
    _store_session(root, data)
