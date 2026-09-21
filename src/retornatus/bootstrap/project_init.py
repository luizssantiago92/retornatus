"""Brownfield project continuity bootstrap (PRD Memory / Wake)."""

from __future__ import annotations

from pathlib import Path

from retornatus.bootstrap.init import initialize_project, is_initialized
from retornatus.infrastructure.environment.adapters import detect_environment
from retornatus.infrastructure.persistence.atomic import atomic_write_text
from retornatus.infrastructure.persistence.paths import RetornatusPaths


IMPORTANT_DIRS = (
    "src",
    "lib",
    "app",
    "tests",
    "test",
    "docs",
    "scripts",
    ".github",
    ".cursor",
    "prd",
)


def detect_ci(root: Path) -> list[str]:
    found: list[str] = []
    gh = root / ".github" / "workflows"
    if gh.is_dir():
        found.extend(sorted(p.name for p in gh.glob("*.yml"))[:8])
        found.extend(sorted(p.name for p in gh.glob("*.yaml"))[:8])
    for name in ("Jenkinsfile", ".gitlab-ci.yml", "azure-pipelines.yml", "buildkite.yml"):
        if (root / name).exists():
            found.append(name)
    return found


def detect_tests(root: Path) -> list[str]:
    signals: list[str] = []
    for name in ("tests", "test", "spec", "__tests__"):
        if (root / name).is_dir():
            signals.append(f"{name}/")
    for name in ("pytest.ini", "pyproject.toml", "package.json", "Cargo.toml"):
        p = root / name
        if not p.is_file():
            continue
        text = p.read_text(encoding="utf-8", errors="replace").lower()
        if name == "pyproject.toml" and "pytest" in text:
            signals.append("pytest (pyproject)")
        if name == "package.json" and any(
            k in text for k in ('"jest"', '"vitest"', '"mocha"', '"test":')
        ):
            signals.append("js test script")
    return signals


def architecture_clues(root: Path) -> list[str]:
    clues: list[str] = []
    for name in ("ARCHITECTURE.md", "architecture.md", "docs/architecture.md", "AGENTS.md"):
        if (root / name).is_file():
            clues.append(name)
    src = root / "src"
    if src.is_dir():
        pkgs = [p.name for p in src.iterdir() if p.is_dir() and not p.name.startswith(".")]
        if pkgs:
            clues.append("src packages: " + ", ".join(sorted(pkgs)[:12]))
    return clues


# Back-compat aliases used by older call sites
_detect_ci = detect_ci
_detect_tests = detect_tests
_architecture_clues = architecture_clues


def project_init(root: Path) -> Path:
    """
    Map a repository into `.retornatus/project/project.md` continuity notes.

    Lightweight brownfield context for Situation and Context Assembly —
    not a universal semantic code index.
    """
    root = root.resolve()
    if not is_initialized(root):
        initialize_project(root)

    paths = RetornatusPaths(root)
    markers: list[str] = []
    for name in (
        "pyproject.toml",
        "package.json",
        "Cargo.toml",
        "go.mod",
        "pom.xml",
        "composer.json",
        "Gemfile",
        "requirements.txt",
        "Pipfile",
    ):
        if (root / name).exists():
            markers.append(name)

    readme = ""
    for candidate in ("README.md", "Readme.md", "readme.md"):
        p = root / candidate
        if p.is_file():
            text = p.read_text(encoding="utf-8", errors="replace")
            readme = text.strip().splitlines()[0] if text.strip() else ""
            break

    dirs = [d for d in IMPORTANT_DIRS if (root / d).exists()]
    tests = detect_tests(root)
    ci = detect_ci(root)
    arch = architecture_clues(root)
    adapter, caps = detect_environment(root)

    retornatus_state: list[str] = []
    if paths.changes.is_dir():
        changes = sorted(p.name for p in paths.changes.iterdir() if p.is_dir())
        retornatus_state.append(f"changes: {len(changes)}")
    if paths.rules.is_dir():
        retornatus_state.append(
            f"rules: {len(list(paths.rules.glob('R-*.json')))}"
        )
    if paths.skills.is_dir():
        retornatus_state.append(
            f"skills: {len([p for p in paths.skills.iterdir() if p.is_dir()])}"
        )

    body = f"""# Project

Retornatus continuity map for `{root.name}`.

## Identity

- Path: `{root}`
- README signal: {readme or "(none)"}

## Language / stack

{chr(10).join(f"- `{m}`" for m in markers) or "- (none detected)"}

## Important directories

{chr(10).join(f"- `{d}`" for d in dirs) or "- (none of the common dirs detected)"}

## Tests

{chr(10).join(f"- {t}" for t in tests) or "- (no test signals detected)"}

## CI

{chr(10).join(f"- `{c}`" for c in ci) or "- (none detected)"}

## Architecture clues

{chr(10).join(f"- {a}" for a in arch) or "- (none detected)"}

## Environment capabilities

- Detected: `{adapter.kind.value}`
- native_rules: {caps.native_rules}
- native_skills: {caps.native_skills}
- native_sandbox: {caps.native_sandbox}

## Existing Retornatus state

{chr(10).join(f"- {s}" for s in retornatus_state) or "- fresh project (no changes/rules/skills yet)"}

## Conventions

_Agents: update this file when durable project conventions are discovered._

## Stack notes

_Fill during Wake / first Change. Prefer facts from the repo over assumptions._
"""
    # Allow overwrite of project.md on re-init of brownfield map
    if paths.project_md.exists():
        paths.project_md.write_text(body, encoding="utf-8")
    else:
        atomic_write_text(paths.project_md, body)
    return paths.project_md
