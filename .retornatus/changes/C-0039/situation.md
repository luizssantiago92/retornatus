<!-- retornatus-meta
{
  "change_id": "C-0039",
  "schema_version": 1
}
-->

# Situation

## Demand

GitHub Marketplace rejects the Action because action.yml description must be under 125 characters. Shorten that description, lock it with a regression test, and prepare patch 1.9.1 by bumping every current-release pin that 1.9.0 changed. Out of scope: merge, tag, and publish.

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

- Demand stated: GitHub Marketplace rejects the Action because action.yml description must be under 125 characters. Shorten that description, lock it with a regression test, and prepare patch 1.9.1 by bumping every current-release pin that 1.9.0 changed. Out of scope: merge, tag, and publish.
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
- Proposed WHAT: Shorten the GitHub Action description in action.yml to under 125 characters, add a regression test for that Marketplace limit, and bump the declared package version from 1.9.0 to 1.9.1 with a dated changelog Fixed note and empty Unreleased.
- DONE criterion: uv run pytest -q exits 0
- DONE criterion: uv run python scripts/build_docs_html.py --check exits 0 as a build
- DONE criterion: uv lock --check exits 0 as a build
- DONE criterion: CHANGELOG.md is documented and contains the heading ## [1.9.1] - 2026-10-01 and an empty Unreleased section
- DONE criterion: README.md is documented and contains the current release 1.9.1
- DONE criterion: The file /docs/index.html is documented and contains 1.9.1
- DONE criterion: The file /pyproject.toml is documented and contains version 1.9.1
- DONE criterion: The file /src/retornatus/__init__.py is documented and contains version 1.9.1
- DONE criterion: The file /.retornatus/config.toml is documented and contains version 1.9.1
- DONE criterion: The file /action.yml is documented and its description is shorter than 125 characters

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

Marketplace publish fails on the folded action.yml description. Name, icon check-circle, color green, and README are already acceptable. The patch dates 1.9.1 on 2026-10-01 and does not merge, tag, or publish.
