<!-- retornatus-meta
{
  "change_id": "C-0008",
  "schema_version": 1
}
-->

# Situation

## Demand

Published retornatus 1.4.0 fails to import on a CLI that already has Typer older than 0.27.2. Scope is the runtime dependency floors, a lowest-direct CI job, a CLI version smoke test, and the 1.4.1 version bump. Out of scope is merging the pull request, creating a git tag, and publishing to PyPI.

## Project context

# Project

Retornatus continuity map for `retornatus`.

## Identity

- Path: repository root (clone path varies by machine)
- README signal: # Retornatus

## Language / stack

- `pyproject.toml`

## Important directories

- `src`
- `tests`
- `docs`
- `.github`
- `.cursor`
- `docs/archive`

## Tests

- tests/
- pytest (pyproject)

## CI

- `ci.yml`
- `publish.yml`

## Architecture clues

- src packages: retornatus

## Environment capabilities

- Detected: `cursor`
- native_rules: True
- native_skills: True
- native_sandbox: False

## Existing Retornatus state

- changes: 1
- rules: 0
- skills: 0

## Conventions

_Agents: update this file when durable project conventions are discovered._

## Stack notes

_Fill during Wake / first Change. Prefer facts from the repo over assumptions._

## Kickoff sources

- `docs/archive/PRD.md`

## Repo signals (inferred)

- stack manifests: `pyproject.toml`
- tests: tests/, pytest (pyproject)
- ci: `ci.yml`, `codeql.yml`, `pages.yml`, `publish.yml`
- architecture: AGENTS.md; src packages: retornatus
- code path present: `src`
- Retornatus already initialized

## Known facts

- Demand stated: Published retornatus 1.4.0 fails to import on a CLI that already has Typer older than 0.27.2. Scope is the runtime dependency floors, a lowest-direct CI job, a CLI version smoke test, and the 1.4.1 version bump. Out of scope is merging the pull request, creating a git tag, and publishing to PyPI.
- Repo: stack manifests: `pyproject.toml`
- Repo: tests: tests/, pytest (pyproject)
- Repo: ci: `ci.yml`, `codeql.yml`, `pages.yml`, `publish.yml`
- Repo: architecture: AGENTS.md; src packages: retornatus
- Repo: code path present: `src`
- Repo: Retornatus already initialized
- Kickoff `docs/archive/PRD.md` present (1494 chars loaded)
- From `docs/archive/PRD.md`: Govern the work. Bound the agent. Verify the outcome.**
- From `docs/archive/PRD.md`: coordination;
- Path: repository root (clone path varies by machine)
- README signal: # Retornatus
- `pyproject.toml`
- `src`
- `tests`
- `docs`
- `.github`
- `.cursor`
- `docs/archive`
- tests/
- pytest (pyproject)
- `ci.yml`
- `publish.yml`
- src packages: retornatus
- Detected: `cursor`
- native_rules: True
- native_skills: True
- native_sandbox: False
- Situation narrative provided by agent/human
- Proposed WHAT: Raise the declared floors to typer>=0.27.2 and pydantic>=2.1, keep cryptography>=42 and tomli-w>=1.0 when a lowest-direct pytest run passes, add an Ubuntu Python 3.11 lowest-direct CI job, add a CLI smoke test that prints the package version, and bump the package version to 1.4.1.
- DONE criterion: pyproject.toml declares typer>=0.27.2 and pydantic>=2.1 and version 1.4.1
- DONE criterion: src/retornatus/__init__.py and uv.lock contain version 1.4.1
- DONE criterion: CHANGELOG.md contains the heading ## [1.4.1] - 2026-09-30 and keeps an empty Unreleased heading above it
- DONE criterion: README.md, docs/guide/Cloud-agents.md, docs/guide/Quick-start.md, docs/guide/README.md, and templates/ci/retornatus-pr.yml contain the 1.4.1 pin or version
- DONE criterion: A permission check shows .github/workflows/ci.yml contains resolution lowest-direct on ubuntu-latest with Python 3.11
- DONE criterion: scripts/publish_preflight.py exits 0 for tag v1.4.1 and prints that 1.4.1 is not on PyPI yet
- DONE criterion: tests/test_cli.py asserts the CLI prints the __version__ string
- DONE criterion: uv run pytest exits 0 after a lowest-direct dependency sync
- DONE criterion: retornatus doctor and retornatus ops run gate-scan exit 0
- DONE criterion: retornatus gate suppressions exits 0 against origin/main

## Constraints

- Prefer pytest for automated verification (inferred from repo)
- Prefer pytest for automated verification (inferred from repo)

## Assumptions

- (none)

## Ambiguities

- (none)

## Missing decisions

- (none)

## Contract readiness

- Sufficient: **yes**
- Rationale: Demand, WHAT, and DONE are sufficiently clear; repo/kickoff signals incorporated; no material requirements ambiguity detected

## Agent narrative

The published 1.4.0 package imports typer.exceptions, which exists only from Typer 0.27.2, and StringConstraints, which exists only from Pydantic 2.1. The declared floors are typer>=0.12 and pydantic>=2.0, so a pip install into an older environment breaks the CLI. Reproduction: uv run --no-project --with retornatus==1.4.0 --with typer==0.26.* retornatus --version raises ModuleNotFoundError. The owner merges and tags v1.4.1 after this Change; the agent does not merge, tag, or publish.
