<!-- retornatus-meta
{
  "change_id": "C-0027",
  "schema_version": 1
}
-->

# Situation

## Demand

Prepare release 1.7.0 so the package version, changelog, and current-release docs match the Stop hook question exception and the SessionStart context hook already on main. Scope is version pins, the dated 1.7.0 changelog section, the landing What's new block, and distribution checks. Out of scope is merging, tagging, and publishing.

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

- Demand stated: Prepare release 1.7.0 so the package version, changelog, and current-release docs match the Stop hook question exception and the SessionStart context hook already on main. Scope is version pins, the dated 1.7.0 changelog section, the landing What's new block, and distribution checks. Out of scope is merging, tagging, and publishing.
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
- Proposed WHAT: Bump the declared package version from 1.6.0 to 1.7.0, move the Unreleased Stop-hook question exception and SessionStart notes under a dated 1.7.0 section, mention the SessionStart hook in the site What's new block, and pin current-release docs to 1.7.0.
- DONE criterion: pyproject.toml, src/retornatus/__init__.py, and uv.lock contain version 1.7.0
- DONE criterion: .retornatus/config.toml version equals installed package version 1.7.0
- DONE criterion: CHANGELOG.md contains the heading ## [1.7.0] - 2026-09-30 and an empty Unreleased section above it
- DONE criterion: The file /docs/index.html news section contains 1.7.0 and SessionStart
- DONE criterion: docs/guide/Cloud-agents.md, docs/guide/Quick-start.md, and docs/guide/README.md contain version 1.7.0
- DONE criterion: action.yml and the file /docs/guide/GitHub-Action.md contain version example 1.7.0
- DONE criterion: README.md contains the current release version 1.7.0
- DONE criterion: uv build exits 0
- DONE criterion: scripts/check_dist_contents.py exits 0
- DONE criterion: uvx twine check exits 0
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

America/Sao_Paulo date for the 1.7.0 heading is 2026-09-30. The owner merges, tags, and publishes. dist/ is not committed.
