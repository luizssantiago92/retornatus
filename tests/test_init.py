"""Tests for `retornatus init` (M0 acceptance)."""

from __future__ import annotations

from pathlib import Path

import tomllib

from retornatus.bootstrap.init import (
    DIRECTORY_TREE,
    initialize_project,
    is_initialized,
)


def test_initialize_creates_minimal_tree(tmp_path: Path) -> None:
    result = initialize_project(tmp_path)

    assert result.created is True
    assert result.already_initialized is False
    assert is_initialized(tmp_path)

    retornatus = tmp_path / ".retornatus"
    assert (retornatus / "config.toml").is_file()
    assert (retornatus / "project" / "project.md").is_file()

    for relative in DIRECTORY_TREE:
        assert (retornatus / relative).is_dir()

    with (retornatus / "config.toml").open("rb") as handle:
        config = tomllib.load(handle)

    assert config["schema_version"] == 1
    assert config["project"]["initialized"] is True


def test_initialize_is_idempotent_without_force(tmp_path: Path) -> None:
    first = initialize_project(tmp_path)
    second = initialize_project(tmp_path)

    assert first.created is True
    assert second.created is False
    assert second.already_initialized is True


def test_force_recreates_config(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    config = tmp_path / ".retornatus" / "config.toml"
    config.write_text("schema_version = 0\n", encoding="utf-8")

    result = initialize_project(tmp_path, force=True)

    assert result.created is True
    with config.open("rb") as handle:
        data = tomllib.load(handle)
    assert data["schema_version"] == 1
