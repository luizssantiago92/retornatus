<!-- retornatus-meta
{
  "change_id": "C-0040",
  "schema_version": 1
}
-->

# Situation

## Demand

The project owner wants the agent to suggest a skill when the same evidence-command sequence repeats across completed Changes, or when evidence fails and then passes. The user must accept before any skill file is written. The CLI and agent hooks must show one pending candidate without blocking the turn for that reason alone.

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

- Demand stated: The project owner wants the agent to suggest a skill when the same evidence-command sequence repeats across completed Changes, or when evidence fails and then passes. The user must accept before any skill file is written. The CLI and agent hooks must show one pending candidate without blocking the turn for that reason alone.
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
- Proposed WHAT: Add a deterministic repetition detector that queues skill candidates, CLI commands to list, accept, and reject them, and a one-line notice on the stop hook and session start. Accept is the only command that writes a draft skill.
- DONE criterion: uv run pytest -q exits 0
- DONE criterion: uv run python scripts/build_docs_html.py --check exits 0 as a build
- DONE criterion: uv lock --check exits 0 as a build
- DONE criterion: The file /CHANGELOG.md is documented and contains skill candidate
- DONE criterion: The file /README.md is documented and contains skill candidates
- DONE criterion: The file /docs/guide/Skills.md is documented and contains skill candidates
- DONE criterion: The file /docs/guide/CLI.md is documented and contains skill accept
- DONE criterion: The file /docs/guide/Agent-hooks.md is documented and contains skill candidate
- DONE criterion: The file /src/retornatus/infrastructure/environment/hub/SKILL.md is documented and contains skill accept
- DONE criterion: The file /.retornatus/config.toml is documented and contains skill_candidates

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

Owners using the CLI and agent hooks need a suggestion when the same non-trivial evidence commands repeat on at least three Changes with green executed evidence, or when a Change retries evidence until it passes. The score threshold lives in config. The agent asks once and waits. skill accept is the only writer of a draft SKILL.md. User utterances are not stored on Changes. The stop hook may read a host transcript when one is present. Out of scope: automatic skill creation, a release, and a version bump.
