<!-- retornatus-meta
{
  "change_id": "C-0003",
  "schema_version": 1
}
-->

# Situation

## Demand

Maintainers must harden GitHub Actions, private-key file creation, and supply-chain config. Scope is workflows, the consumer CI template, the Ed25519 key writer, SECURITY.md, CodeQL, Dependabot, and the ruff 0.16.8 StrEnum migration. Out of scope is publishing to PyPI.

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
- ci: `ci.yml`, `pages.yml`, `publish.yml`
- architecture: AGENTS.md; src packages: retornatus
- code path present: `src`
- Retornatus already initialized

## Known facts

- Demand stated: Maintainers must harden GitHub Actions, private-key file creation, and supply-chain config. Scope is workflows, the consumer CI template, the Ed25519 key writer, SECURITY.md, CodeQL, Dependabot, and the ruff 0.16.8 StrEnum migration. Out of scope is publishing to PyPI.
- Repo: stack manifests: `pyproject.toml`
- Repo: tests: tests/, pytest (pyproject)
- Repo: ci: `ci.yml`, `pages.yml`, `publish.yml`
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
- Proposed WHAT: Pin every GitHub Action in .github/workflows and templates/ci/retornatus-pr.yml to the current main commit SHA with a version comment, set top-level permissions contents read, disable uv cache on publish jobs, create the Ed25519 private key at mode 0600, add SECURITY.md and a least-privilege CodeQL workflow, keep Dependabot on github-actions, and bump ruff to 0.16.8 using StrEnum without changing serialized enum values.
- DONE criterion: Workflows and the consumer template use full commit SHAs, contents read, and persist-credentials false except where a job must push
- DONE criterion: Publish jobs do not enable the uv cache; pytest shows the private key file is mode 0600 from creation on POSIX
- DONE criterion: ruff 0.16.8, mypy, pytest, docs check, and retornatus verify pass, and JSON enum values match the pre-migration output

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

Audit found tag-pinned actions including pypa/gh-action-pypi-publish@release/v1 on the id-token write job, missing least-privilege permissions, uv cache in publish, a chmod-after-write private key, no SECURITY.md or CodeQL, and ruff 0.16.8 UP042 on twenty str Enum classes. Dependabot already lists github-actions. Constraint: do not merge, tag, or publish to PyPI. Serialized JSON and receipt enum values must stay identical.
