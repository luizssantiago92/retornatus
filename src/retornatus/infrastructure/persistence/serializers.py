"""Serializers for JSON, Markdown, and TOML canonical formats (PRD §6)."""

from __future__ import annotations

import json
import tomllib
from typing import Any, TypeVar

import tomli_w
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def dump_json_model(model: BaseModel) -> bytes:
    return (
        model.model_dump_json(indent=2, exclude_none=False) + "\n"
    ).encode("utf-8")


def load_json_model(data: bytes, model_type: type[T]) -> T:
    return model_type.model_validate_json(data)


def dump_toml_dict(data: dict[str, Any]) -> bytes:
    return tomli_w.dumps(data).encode("utf-8")


def load_toml_dict(data: bytes) -> dict[str, Any]:
    return tomllib.loads(data.decode("utf-8"))


def dump_markdown(
    body: str,
    *,
    front_matter: dict[str, Any] | None = None,
) -> str:
    """Persist Markdown with optional JSON metadata in an HTML comment."""
    if not front_matter:
        return body if body.endswith("\n") else body + "\n"
    meta = json.dumps(front_matter, indent=2, sort_keys=True)
    return f"<!-- retornatus-meta\n{meta}\n-->\n\n{body.rstrip()}\n"


def load_markdown(text: str) -> tuple[dict[str, Any] | None, str]:
    marker = "<!-- retornatus-meta\n"
    if not text.startswith(marker):
        return None, text
    end = text.find("\n-->\n")
    if end < 0:
        return None, text
    meta_raw = text[len(marker) : end]
    body = text[end + len("\n-->\n") :].lstrip("\n")
    return json.loads(meta_raw), body
