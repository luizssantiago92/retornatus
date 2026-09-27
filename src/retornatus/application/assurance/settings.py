"""Project-level assurance settings from ``.retornatus/config.toml``."""

from __future__ import annotations

from pathlib import Path


def allow_self_reported_enabled(root: Path) -> bool:
    """True only when ``[assurance] allow_self_reported`` is boolean true.

    Missing config, a missing key, or any other value keeps the strict default:
    self-reported execution evidence does not satisfy Claims.
    """
    from retornatus.infrastructure.persistence.repository import FileRepository

    try:
        data, _ = FileRepository(root).load_config()
    except (OSError, FileNotFoundError, ValueError):
        return False
    assurance = data.get("assurance")
    if not isinstance(assurance, dict):
        return False
    return assurance.get("allow_self_reported") is True
