"""Decide whether the agent stopped to ask the user a question.

Hosts document an assistant-text field on some Stop payloads and a transcript
path on all three. The transcript line schema is not a stable contract, so the
tail reader accepts a few optional shapes and ignores everything else.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

# Last slice of a transcript file. A partial first line after the cut is dropped.
TRANSCRIPT_TAIL_BYTES = 256 * 1024

# Claude Code and Codex document this Stop field. Cursor's stop input does not.
_DIRECT_MESSAGE_FIELD = {
    "claude": "last_assistant_message",
    "codex": "last_assistant_message",
}

_FENCE_LINE = re.compile(r"^[ \t]*```")
_FENCED_BLOCK = re.compile(r"```.*?```", re.DOTALL)
_INLINE_CODE = re.compile(r"`[^`\n]*`")
_URL = re.compile(r"(?:https?://|www\.)\S+", re.IGNORECASE)
_TRAILING_CLOSERS = "\"'”’)]」"
_ASK_PHRASE = re.compile(
    r"(?:^|(?<=[.!?]\s)|(?<=\n))"
    r"(?:should i|shall i|do you want|would you like|want me to|"
    r"quer que eu|posso seguir|posso continuar|devo seguir|devo continuar|"
    r"você quer|voce quer|prefere que eu)\b",
    re.IGNORECASE,
)
_SKIP_BLOCK_TYPES = frozenset({"tool_use", "tool_result", "thinking"})
_NON_ASSISTANT = frozenset({"user", "system", "tool", "human"})


def assistant_message_text(host: str, payload: dict[str, Any]) -> str | None:
    """Last assistant text from a documented field, else the transcript tail.

    A present string field wins, including a statement that is not a question.
    ``null`` and a missing field fall through to ``transcript_path``. An empty
    string does not. Any read error returns None so the caller keeps today's
    decision.
    """
    field = _DIRECT_MESSAGE_FIELD.get(host)
    if field is not None and field in payload and isinstance(payload[field], str):
        text = payload[field].strip()
        return text or None
    return _text_from_transcript_field(payload, "transcript_path")


def subagent_assistant_text(host: str, payload: dict[str, Any]) -> str | None:
    """Last subagent text from the fields each host documents for subagent stop.

    Claude Code and Codex prefer ``last_assistant_message``. A present string
    wins, including a statement. ``null`` and a missing field fall through to
    ``agent_transcript_path`` (the subagent transcript), then the parent
    ``transcript_path``. Cursor ``subagentStop`` has no assistant-text field.
    It uses ``agent_transcript_path``, then ``transcript_path``, then
    ``summary``.
    """
    field = _DIRECT_MESSAGE_FIELD.get(host)
    if field is not None and field in payload and isinstance(payload[field], str):
        text = payload[field].strip()
        return text or None
    for key in ("agent_transcript_path", "transcript_path"):
        found = _text_from_transcript_field(payload, key)
        if found:
            return found
    if host == "cursor":
        summary = payload.get("summary")
        if isinstance(summary, str) and summary.strip():
            return summary.strip()
    return None


def _text_from_transcript_field(payload: dict[str, Any], key: str) -> str | None:
    path = payload.get(key)
    if not isinstance(path, str) or not path.strip():
        return None
    return read_transcript_assistant_text(Path(path).expanduser())


def read_transcript_assistant_text(path: Path) -> str | None:
    """Assistant text from the last complete JSONL lines of ``path``."""
    try:
        if not path.is_file():
            return None
        raw = _tail_bytes(path, TRANSCRIPT_TAIL_BYTES)
    except OSError:
        return None
    text = raw.decode("utf-8", errors="replace")
    return last_assistant_text_from_jsonl(text)


def last_assistant_text_from_jsonl(text: str) -> str | None:
    """Walk JSONL from the end. Malformed and non-assistant lines are skipped."""
    for line in reversed(text.splitlines()):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        if not isinstance(parsed, dict):
            continue
        message = _assistant_line_text(parsed)
        if message:
            return message
    return None


def is_question_to_user(text: str) -> bool:
    """True when the final visible paragraph asks the user something.

    Trailing fenced code and whitespace are ignored. A ``?`` or full-width
    ``？`` inside a code span or a URL does not count. An explicit ask phrase
    at the start of that paragraph, or after a sentence boundary, also counts.
    """
    if not text.strip():
        return False
    body = _strip_trailing_fences(text)
    paragraphs = re.split(r"\n\s*\n", body)
    for paragraph in reversed(paragraphs):
        visible = _visible_prose(paragraph)
        if not visible:
            continue
        return _ends_with_question_mark(visible) or _ASK_PHRASE.search(visible) is not None
    return False


def _strip_trailing_fences(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").rstrip()
    lines = normalized.split("\n") if normalized else []
    while True:
        fence_indexes = [index for index, line in enumerate(lines) if _FENCE_LINE.match(line)]
        if not lines:
            break
        if len(fence_indexes) % 2 == 1:
            lines = lines[: fence_indexes[-1]]
        elif fence_indexes and _FENCE_LINE.match(lines[-1]):
            lines = lines[: fence_indexes[-2]]
        else:
            break
        while lines and not lines[-1].strip():
            lines.pop()
    return "\n".join(lines).rstrip()


def _visible_prose(paragraph: str) -> str:
    without_fences = _FENCED_BLOCK.sub(" ", paragraph)
    without_inline = _INLINE_CODE.sub(" ", without_fences)
    without_urls = _URL.sub(" ", without_inline)
    return " ".join(without_urls.split())


def _ends_with_question_mark(visible: str) -> bool:
    trimmed = visible.rstrip()
    while trimmed and trimmed[-1] in _TRAILING_CLOSERS:
        trimmed = trimmed[:-1].rstrip()
    return bool(trimmed) and trimmed[-1] in "?？"


def _tail_bytes(path: Path, limit: int) -> bytes:
    with path.open("rb") as handle:
        handle.seek(0, os.SEEK_END)
        size = handle.tell()
        start = max(0, size - limit)
        handle.seek(start)
        raw = handle.read(limit)
    if start > 0:
        newline = raw.find(b"\n")
        if newline == -1:
            return b""
        raw = raw[newline + 1 :]
    return raw


def _assistant_line_text(obj: dict[str, Any]) -> str | None:
    message = obj.get("message")
    kind = obj.get("type")
    role = obj.get("role")
    if isinstance(message, dict):
        if not isinstance(kind, str):
            kind = message.get("type")
        if not isinstance(role, str):
            role = message.get("role")
    if not _is_assistant(kind, role):
        return None
    source = message if isinstance(message, dict) else obj
    chunks: list[str] = []
    _collect_text(source.get("text"), chunks)
    _collect_text(source.get("content"), chunks)
    joined = "\n".join(part.strip() for part in chunks if part and part.strip())
    return joined or None


def _is_assistant(kind: object, role: object) -> bool:
    labels: list[str] = []
    for value in (kind, role):
        if isinstance(value, str) and value.strip():
            labels.append(value.strip().casefold())
    if not labels or any(label in _NON_ASSISTANT for label in labels):
        return False
    return "assistant" in labels


def _collect_text(value: object, chunks: list[str]) -> None:
    if isinstance(value, str):
        chunks.append(value)
        return
    if not isinstance(value, list):
        return
    for item in value:
        if isinstance(item, str):
            chunks.append(item)
            continue
        if not isinstance(item, dict):
            continue
        block_type = item.get("type")
        if isinstance(block_type, str) and block_type.casefold() in _SKIP_BLOCK_TYPES:
            continue
        text = item.get("text")
        if isinstance(text, str):
            chunks.append(text)
