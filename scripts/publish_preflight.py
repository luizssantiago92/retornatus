#!/usr/bin/env python3
"""Decide whether a PyPI publish should run.

Tag pushes must be named v<version> (the caller already checked the commit is on main).
A new version needs a matching changelog section. A version already on PyPI is skipped.
"""

from __future__ import annotations

import os
import re
import sys
import tomllib
import urllib.error
import urllib.request
from pathlib import Path


def _append_output(key: str, value: str) -> None:
    path = os.environ.get("GITHUB_OUTPUT")
    line = f"{key}={value}\n"
    if not path:
        print(line, end="")
        return
    with Path(path).open("a", encoding="utf-8") as handle:
        handle.write(line)


def changelog_has_version(text: str, version: str) -> bool:
    """True for ``## [1.2.3]`` or ``## 1.2.3`` headings. Unreleased does not count."""
    pattern = re.compile(
        rf"^## \[?{re.escape(version)}\]?(?:\s|$)",
        re.MULTILINE,
    )
    return pattern.search(text) is not None


def version_on_pypi(name: str, version: str) -> bool:
    url = f"https://pypi.org/pypi/{name}/{version}/json"
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            return response.status == 200
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return False
        raise


def main() -> int:
    project = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))["project"]
    name = str(project["name"])
    version = str(project["version"])
    event = os.environ.get("GITHUB_EVENT_NAME", "")
    ref_name = os.environ.get("GITHUB_REF_NAME", "")

    if event == "push" and ref_name != f"v{version}":
        print(
            f"Tag {ref_name!r} does not match package version {version} (expected v{version}).",
            file=sys.stderr,
        )
        return 1

    exists = version_on_pypi(name, version)
    _append_output("version", version)
    _append_output("skip", "true" if exists else "false")
    if exists:
        print(f"{name} {version} is already on PyPI — publish will be skipped.")
        return 0

    changelog_path = Path("CHANGELOG.md")
    if not changelog_path.is_file():
        print("CHANGELOG.md is missing. Add a Keep a Changelog section before publishing.", file=sys.stderr)
        return 1
    changelog = changelog_path.read_text(encoding="utf-8")
    if not changelog_has_version(changelog, version):
        print(
            f"CHANGELOG.md must include a ## [{version}] section before publishing {version}.",
            file=sys.stderr,
        )
        print("Move the Unreleased notes under that heading in the release PR.", file=sys.stderr)
        return 1
    print(f"{name} {version} is not on PyPI yet — publish may continue.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
