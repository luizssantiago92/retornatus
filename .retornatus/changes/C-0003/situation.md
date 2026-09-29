<!-- retornatus-meta
{
  "change_id": "C-0003",
  "schema_version": 1
}
-->

# Situation

## Demand

Document using Retornatus on cloud and remote coding agents

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

- Demand stated: Document using Retornatus on cloud and remote coding agents
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
- Proposed WHAT: A concise guide covers clean-VM CLI install, hook reinstall, unsigned receipts, and GitHub CI enforcement, and is linked from the docs hub, README, and changelog
- DONE criterion: docs/guide/Cloud-agents.md names uv tool install of a pinned version, hooks install, hooks status, and doctor
- DONE criterion: The guide states the private signing key stays off the agent VM and cloud agents leave receipts unsigned
- DONE criterion: The guide points at templates/ci/retornatus-pr.yml running verify, gate suppressions --base, and gate scope --base on pull requests
- DONE criterion: docs/guide/README.md, docs/guide/index.html, the HTML build page list, README.md, and CHANGELOG Unreleased reference the new page

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

Cloud and remote agents (Cursor cloud agents, Codex, Claude Code on a remote VM, CI sandboxes) clone the repo onto a clean machine. The retornatus CLI is not in git. Git hooks are not versioned, so hooks install must run on every fresh clone. Receipt signing keys must not be present on that VM. Enforcement that counts is the GitHub Actions workflow copied from templates/ci/retornatus-pr.yml. Out of scope: changing CLI behavior, publishing a release, or putting a signing key in the agent environment.

## Reopened Situation

Appended a security-test DONE line so gate scope can accept workflow paths that later commits added on top of this Change. Prior DONE lines are unchanged.
