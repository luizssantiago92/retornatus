<!-- retornatus-meta
{
  "change_id": "C-0034",
  "schema_version": 1
}
-->

# Situation

## Demand

Maintainers must adopt ruff format for Python under src, tests, and scripts. Scope is one formatting commit, a root .git-blame-ignore-revs file naming that commit, a CONTRIBUTING.md note for blame.ignoreRevsFile, a ruff format --check step on the existing CI lint job, and a CHANGELOG Unreleased entry. Out of scope: behavior changes, job renames, matrix changes, merging, and publishing.

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

- Demand stated: Maintainers must adopt ruff format for Python under src, tests, and scripts. Scope is one formatting commit, a root .git-blame-ignore-revs file naming that commit, a CONTRIBUTING.md note for blame.ignoreRevsFile, a ruff format --check step on the existing CI lint job, and a CHANGELOG Unreleased entry. Out of scope: behavior changes, job renames, matrix changes, merging, and publishing.
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
- Proposed WHAT: Apply ruff format to src, tests, and scripts in one dedicated commit, record that full commit SHA in .git-blame-ignore-revs, document git config blame.ignoreRevsFile .git-blame-ignore-revs in CONTRIBUTING.md, add ruff format --check src tests scripts beside the existing CI lint step without renaming jobs or changing the matrix, and add a CHANGELOG Unreleased entry.
- DONE criterion: uv run pytest -q exits 0
- DONE criterion: uv run python scripts/build_docs_html.py --check exits 0 as a build
- DONE criterion: uv lock --check exits 0 as a build
- DONE criterion: CONTRIBUTING.md is documented and contains git config blame.ignoreRevsFile .git-blame-ignore-revs
- DONE criterion: CHANGELOG.md is documented and contains an Unreleased ruff format entry
- DONE criterion: Human review of /.github/workflows/ci.yml confirms the format check stays in the existing lint job

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

Python sources under src, tests, and scripts are not yet formatted by ruff format, CI does not check formatting, and git blame has no ignore-revs file. The finish line is a formatting-only commit, a blame ignore file that names that commit, a CONTRIBUTING note, an unchanged CI job matrix with a format check step, and a changelog entry. Behavior stays the same.
