#!/usr/bin/env python3
"""Fail when an sdist or wheel ships test fixtures, tests, scripts, or assets."""

from __future__ import annotations

import sys
import tarfile
import zipfile
from pathlib import Path

# Modules that exist only for dogfood tests. They must not be installed.
FORBIDDEN_FILE_NAMES = frozenset({"host_boundary.py", "brownfield_fixture.py"})
# Top-level trees that are repo tooling, not the package.
LEAK_SEGMENTS = frozenset({"tests", "scripts", ".assets", "assets"})


def offending_members(names: list[str]) -> list[str]:
    """Return archive member names that must not ship."""
    bad: list[str] = []
    for name in names:
        parts = [part for part in name.replace("\\", "/").split("/") if part]
        if not parts:
            continue
        if parts[-1] in FORBIDDEN_FILE_NAMES:
            bad.append(name)
            continue
        if any(part in LEAK_SEGMENTS for part in parts):
            bad.append(name)
    return bad


def members_of(path: Path) -> list[str]:
    if path.suffix == ".whl":
        with zipfile.ZipFile(path) as archive:
            return archive.namelist()
    if path.name.endswith(".tar.gz"):
        with tarfile.open(path) as archive:
            return [item.name for item in archive.getmembers() if item.isfile()]
    return []


def check_dist(dist_dir: Path) -> list[str]:
    problems: list[str] = []
    artifacts = sorted(dist_dir.glob("*"))
    wheels = [path for path in artifacts if path.suffix == ".whl"]
    sdists = [path for path in artifacts if path.name.endswith(".tar.gz")]
    if not wheels or not sdists:
        problems.append(f"{dist_dir} must contain one sdist and one wheel")
    for path in wheels + sdists:
        for name in offending_members(members_of(path)):
            problems.append(f"{path.name}: {name}")
    return problems


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    dist_dir = Path(args[0] if args else "dist")
    if not dist_dir.is_dir():
        print(f"dist directory not found: {dist_dir}", file=sys.stderr)
        return 1
    problems = check_dist(dist_dir)
    if problems:
        print("Distribution contents check failed:", file=sys.stderr)
        for problem in problems:
            print(f"  {problem}", file=sys.stderr)
        return 1
    print(f"Distribution contents OK ({dist_dir})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
