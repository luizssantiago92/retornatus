<!-- retornatus-meta
{
  "change_id": "C-0022",
  "schema_version": 1
}
-->

# Situation

## Demand

PyPI readers of the retornatus CLI must see an MIT license expression, trove classifiers, and project URLs, and every README link must resolve on PyPI. Scope is package metadata, absolute README links, and release 1.5.0 notes. Out of scope is merging, tagging, and publishing.

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

- Demand stated: PyPI readers of the retornatus CLI must see an MIT license expression, trove classifiers, and project URLs, and every README link must resolve on PyPI. Scope is package metadata, absolute README links, and release 1.5.0 notes. Out of scope is merging, tagging, and publishing.
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
- Proposed WHAT: Declare PEP 639 license MIT with license-files, add trove classifiers and project URLs, rewrite README non-anchor links to absolute GitHub URLs, and record release 1.5.0 in the changelog and version pins.
- DONE criterion: pyproject.toml contains license = "MIT", license-files, classifiers, and Documentation and Changelog project URLs
- DONE criterion: pytest fails when README.md contains a relative non-anchor link
- DONE criterion: pyproject.toml, src/retornatus/__init__.py, and uv.lock contain version 1.5.0
- DONE criterion: .retornatus/config.toml version equals installed package version 1.5.0
- DONE criterion: CHANGELOG.md contains the heading ## [1.5.0] - 2026-09-30 and an empty Unreleased section above it
- DONE criterion: docs/guide/Cloud-agents.md, docs/guide/Quick-start.md, and docs/guide/README.md contain version 1.5.0
- DONE criterion: uv run pytest -q exits 0
- DONE criterion: uv run ruff check src tests scripts exits 0
- DONE criterion: uv run mypy exits 0
- DONE criterion: uv run python scripts/build_docs_html.py --check exits 0
- DONE criterion: uv lock --check exits 0

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

Audit I3 on current main: classifiers are empty, license is the legacy text table, and project URLs omit Documentation and Changelog. README still has relative links that break on PyPI. Unreleased since 1.4.1 contains features, so the release is 1.5.0. The owner merges, tags, and publishes.
