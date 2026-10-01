<!-- retornatus-meta
{
  "change_id": "C-0033",
  "schema_version": 1
}
-->

# Situation

## Demand

Declare the commands this repository must run before verify accepts execution evidence. In scope: pytest, ruff, mypy, the docs HTML build check, and uv lock --check in .retornatus/config.toml, plus short notes in CONTRIBUTING.md and CHANGELOG.md. Out of scope: rewriting historic Change evidence, merging, and publishing.

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

- Demand stated: Declare the commands this repository must run before verify accepts execution evidence. In scope: pytest, ruff, mypy, the docs HTML build check, and uv lock --check in .retornatus/config.toml, plus short notes in CONTRIBUTING.md and CHANGELOG.md. Out of scope: rewriting historic Change evidence, merging, and publishing.
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
- Proposed WHAT: Set [assurance] required_checks in .retornatus/config.toml to the five commands this repository always runs, document them in CONTRIBUTING.md and CHANGELOG.md, and keep verify SATISFIED for this Change after those commands are recorded on a clean tree. Older Changes stay unmodified.
- DONE criterion: uv run pytest -q exits 0
- DONE criterion: uv run ruff check src tests scripts exits 0
- DONE criterion: uv run mypy exits 0
- DONE criterion: uv run python scripts/build_docs_html.py --check is a passing build
- DONE criterion: uv lock --check is a passing build
- DONE criterion: CONTRIBUTING.md documents the repository required checks
- DONE criterion: CHANGELOG.md documents an Unreleased required checks entry
- DONE criterion: The file /.retornatus/config.toml documents required_checks

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

Dogfood [assurance] required_checks on this repository. Historic Change files stay as recorded. Evidence for this Change is recorded after the implementation commit, on a clean tree.
