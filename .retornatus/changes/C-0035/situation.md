<!-- retornatus-meta
{
  "change_id": "C-0035",
  "schema_version": 1
}
-->

# Situation

## Demand

Maintainers need CHANGELOG.md to record releases 1.0.0, 1.1.0, 1.1.1, 1.2.0, 1.2.1, and 1.3.0 from git tags, GitHub Releases, merged pull requests, and commit ranges. Scope is CHANGELOG.md plus one new Change record. Out of scope: product code, merge, and publish.

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

- Demand stated: Maintainers need CHANGELOG.md to record releases 1.0.0, 1.1.0, 1.1.1, 1.2.0, 1.2.1, and 1.3.0 from git tags, GitHub Releases, merged pull requests, and commit ranges. Scope is CHANGELOG.md plus one new Change record. Out of scope: product code, merge, and publish.
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
- Proposed WHAT: Replace the 1.2.1 and 1.3.0 changelog stubs with sourced Keep a Changelog sections for 1.0.0, 1.1.0, 1.1.1, 1.2.0, 1.2.1, and 1.3.0, dated from the tags, grouped under Added, Changed, Fixed, and Security, with pull request numbers where the history records them.
- DONE criterion: uv run pytest -q exits 0
- DONE criterion: uv run python scripts/build_docs_html.py --check exits 0 as a build
- DONE criterion: uv lock --check exits 0 as a build
- DONE criterion: CHANGELOG.md is documented with dated sections for 1.0.0 through 1.3.0

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

CHANGELOG.md stops at stub lines for 1.2.1 and 1.3.0. Tags v1.0.0, v1.1.0, v1.1.1, v1.2.0, v1.2.1, and v1.3.0 exist. The finish line is sourced Keep a Changelog sections for those versions only, plus this Change record. No product code.
