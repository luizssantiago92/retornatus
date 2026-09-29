<!-- retornatus-meta
{
  "change_id": "C-0005",
  "schema_version": 1
}
-->

# Situation

## Demand

Prepare the 1.4.0 release so publish preflight accepts tag v1.4.0. Scope is the package version, CHANGELOG.md, pinned installs in templates and docs, and README text that would be wrong after PyPI has 1.4.0. Out of scope is merging the pull request, creating a git tag, and publishing to PyPI.

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
- `prd`

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

- Demand stated: Prepare the 1.4.0 release so publish preflight accepts tag v1.4.0. Scope is the package version, CHANGELOG.md, pinned installs in templates and docs, and README text that would be wrong after PyPI has 1.4.0. Out of scope is merging the pull request, creating a git tag, and publishing to PyPI.
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
- `prd`
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
- Proposed WHAT: Bump the declared package version from 1.3.0 to 1.4.0, move Unreleased changelog notes under a dated 1.4.0 section, pin consumer installs to retornatus==1.4.0, and correct README and docs that still describe 1.3.0 as the current release or as missing post-1.3.0 commands.
- DONE criterion: pyproject.toml, src/retornatus/__init__.py, and uv.lock contain version 1.4.0
- DONE criterion: CHANGELOG.md includes a 1.4.0 section dated 2026-09-29 and keeps an empty Unreleased heading above it
- DONE criterion: README.md, docs/guide/Cloud-agents.md, docs/guide/Quick-start.md, docs/guide/README.md, and templates/ci/retornatus-pr.yml contain the 1.4.0 pin or version
- DONE criterion: scripts/publish_preflight.py exits 0 for tag v1.4.0 and prints that 1.4.0 is not on PyPI yet

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

Release preparation for 1.4.0. The owner merges and tags v1.4.0 after this Change; the agent does not merge, tag, or publish.
