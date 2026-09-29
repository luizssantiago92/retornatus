<!-- retornatus-meta
{
  "change_id": "C-0006",
  "schema_version": 1
}
-->

# Situation

## Demand

The harness CLI must keep doctor and gate-scan green, historical Change scope honest, suppression scans quiet on markdown code spans, and CI running those gates from the local checkout.

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

- Demand stated: The harness CLI must keep doctor and gate-scan green, historical Change scope honest, suppression scans quiet on markdown code spans, and CI running those gates from the local checkout.
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
- Proposed WHAT: Repair C-0001 done criteria and evidence, backfill C-0003 and C-0004 task resources, skip markdown code spans in gate suppressions, stamp init with the package version, fix the project map and credits link, and run the harness gates in CI.
- DONE criterion: retornatus doctor and retornatus ops run gate-scan exit 0
- DONE criterion: retornatus gate scope for C-0004 against its parent commit exits 0
- DONE criterion: retornatus gate scope for C-0003 against its parent commit exits 0
- DONE criterion: pytest shows markdown code spans are not suppression hits
- DONE criterion: pytest shows initialize_project writes the package version into config.toml
- DONE criterion: project.md contains the docs archive path and does not name a prd directory
- DONE criterion: docs README links credits to the Pages site and the source markdown file
- DONE criterion: security test shows workflow permission contents read
- DONE criterion: The CI workflow file contains doctor, gate-scan, and suppressions steps

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

Owner-approved repair of active-contract hygiene on main. C-0005 stays reserved for the unmerged 1.4.0 PR.
