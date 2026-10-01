<!-- retornatus-meta
{
  "change_id": "C-0032",
  "schema_version": 1
}
-->

# Situation

## Demand

Harden GitHub Actions in .github/workflows and action.yml: third-party uses stay on full commit SHAs with version comments, workflows default to contents read, read-only jobs set that permission on the job, checkout sets persist-credentials false, Dependabot updates github-actions weekly, CONTRIBUTING.md states the rule, and CHANGELOG Unreleased has a Security entry. Job names, the test matrix, and the pypi environment approval flow stay unchanged.

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

- Demand stated: Harden GitHub Actions in .github/workflows and action.yml: third-party uses stay on full commit SHAs with version comments, workflows default to contents read, read-only jobs set that permission on the job, checkout sets persist-credentials false, Dependabot updates github-actions weekly, CONTRIBUTING.md states the rule, and CHANGELOG Unreleased has a Security entry. Job names, the test matrix, and the pypi environment approval flow stay unchanged.
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
- Proposed WHAT: Read-only CI and publish jobs set permissions contents read on the job itself. Existing SHA pins, persist-credentials false, Dependabot, and the pypi environment stay. CONTRIBUTING.md and CHANGELOG Unreleased document the rule, and tests lock the pins, permissions, Dependabot schedule, and pypi environment.
- DONE criterion: pytest reports that third-party uses are pinned to 40-character commit SHAs with a version comment
- DONE criterion: pytest reports that read-only jobs set a permission of contents read
- DONE criterion: pytest reports that every checkout step sets persist-credentials to false
- DONE criterion: pytest reports that dependabot schedules github-actions weekly
- DONE criterion: pytest reports that the publish job keeps environment name pypi
- DONE criterion: CONTRIBUTING.md documents that third-party actions are pinned to commit SHAs and workflows default to contents read
- DONE criterion: CHANGELOG.md Unreleased contains a Security entry for pinned actions and least-privilege token scopes
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

Workflows already pin third-party actions to the current release SHAs (verified against GitHub on 2026-10-01) and set top-level contents read. Read-only jobs still inherit that default instead of setting it on the job. CONTRIBUTING.md does not state the pin rule. CHANGELOG Unreleased has no Security entry for it. Job names, the matrix, and the pypi environment must stay.
