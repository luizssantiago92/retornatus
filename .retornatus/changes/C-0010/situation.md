<!-- retornatus-meta
{
  "change_id": "C-0010",
  "schema_version": 1
}
-->

# Situation

## Demand

Machine-readable CLI consumers such as hooks, CI comments, and dashboards must read verify, gate, and change overview verdicts as one versioned JSON document on stdout. Scope is the --json flag, the verdict schema, tests, and the docs page. Out of scope is a GitHub Action, an MCP server, a package version bump, and merging the pull request.

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

- Demand stated: Machine-readable CLI consumers such as hooks, CI comments, and dashboards must read verify, gate, and change overview verdicts as one versioned JSON document on stdout. Scope is the --json flag, the verdict schema, tests, and the docs page. Out of scope is a GitHub Action, an MCP server, a package version bump, and merging the pull request.
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
- Proposed WHAT: Add a stable schema_version 1 JSON envelope to retornatus verify, every gate subcommand, and change overview, with stdout limited to that document when --json is set.
- DONE criterion: pytest exits 0 for the JSON verdict command tests
- DONE criterion: ruff check of src tests and scripts exits 0
- DONE criterion: mypy on the retornatus package exits 0
- DONE criterion: The HTML documentation check exits 0
- DONE criterion: uv lock check exits 0
- DONE criterion: CHANGELOG Unreleased section records the JSON verdict envelope
- DONE criterion: The CLI reference contains a link to the JSON output page

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

Consumers cannot parse Rich or prose verdicts reliably. The CLI already prints AssuranceResult JSON from verify mixed with labels, and gates print message lines. This Change adds one versioned envelope and a JSON Schema. Constraints: exit codes stay identical to text mode, and the package version is not bumped. Out of scope: GitHub Action, MCP server, merge, and publish.
