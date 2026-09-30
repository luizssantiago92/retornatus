<!-- retornatus-meta
{
  "change_id": "C-0014",
  "schema_version": 1
}
-->

# Situation

## Demand

CLI users must initialize a Retornatus project with a packaged config preset. python covers uv pytest ruff and mypy. python-platform extends python and adds path-triggered ship and AI evidence rules. Out of scope: a version bump, merging, and publishing.

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

- Demand stated: CLI users must initialize a Retornatus project with a packaged config preset. python covers uv pytest ruff and mypy. python-platform extends python and adds path-triggered ship and AI evidence rules. Out of scope: a version bump, merging, and publishing.
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
- Proposed WHAT: retornatus init --preset writes a packaged TOML preset into config.toml, and verify enforces ship and AI surface rules only when changed or scoped paths match.
- DONE criterion: pytest exits 0 for the preset and surface tests
- DONE criterion: ruff check of src tests and scripts exits 0
- DONE criterion: mypy on the retornatus package exits 0
- DONE criterion: The HTML documentation check exits 0
- DONE criterion: uv lock check exits 0
- DONE criterion: An unknown preset name exits with the available preset list
- DONE criterion: init without a preset preserves the gitignore block
- DONE criterion: python-platform preset extends the python checks
- DONE criterion: CHANGELOG Unreleased section records config presets
- DONE criterion: verify reports surface status not required when no infra or AI paths match

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

The CLI init path writes a minimal config and the C-0012 gitignore block. Presets are TOML data files in the wheel. python-platform extends python. Ship and AI rules require executed evidence when paths match, and report not required otherwise. No design.md workflow.
