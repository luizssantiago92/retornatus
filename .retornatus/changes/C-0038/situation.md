<!-- retornatus-meta
{
  "change_id": "C-0038",
  "schema_version": 1
}
-->

# Situation

## Demand

Prepare release 1.9.0 so the package version, changelog, and current-release docs match work already on main since 1.8.0: the untracked suppression scan, least-privilege CI job permissions, required checks, ruff format, changelog history 1.0 through 1.3, the square favicon, and the subagent-stop hook. Scope is version pins, the dated 1.9.0 changelog section, and the README and landing What's new blocks. Out of scope is merging, tagging, and publishing.

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

- Demand stated: Prepare release 1.9.0 so the package version, changelog, and current-release docs match work already on main since 1.8.0: the untracked suppression scan, least-privilege CI job permissions, required checks, ruff format, changelog history 1.0 through 1.3, the square favicon, and the subagent-stop hook. Scope is version pins, the dated 1.9.0 changelog section, and the README and landing What's new blocks. Out of scope is merging, tagging, and publishing.
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
- Proposed WHAT: Bump the declared package version from 1.8.0 to 1.9.0, move Unreleased notes under a dated 1.9.0 section, list hook subagent-stop as shipped in 1.9.0 in the README and site What's new blocks, and pin current-release docs to 1.9.0.
- DONE criterion: uv run pytest -q exits 0
- DONE criterion: uv run python scripts/build_docs_html.py --check exits 0 as a build
- DONE criterion: uv lock --check exits 0 as a build
- DONE criterion: CHANGELOG.md is documented and contains the heading ## [1.9.0] - 2026-10-01 and an empty Unreleased section
- DONE criterion: README.md is documented and contains the current release 1.9.0 and hook subagent-stop
- DONE criterion: The file /docs/index.html is documented and contains 1.9.0 and subagent-stop
- DONE criterion: The file /pyproject.toml is documented and contains version 1.9.0
- DONE criterion: The file /src/retornatus/__init__.py is documented and contains version 1.9.0
- DONE criterion: The file /.retornatus/config.toml is documented and contains version 1.9.0

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

Release prep only. Date the 1.9.0 heading 2026-10-01. Group changelog notes as Added, Changed, Fixed, and Security with pull request numbers from commits since v1.8.0. Do not merge, tag, or publish.
