<!-- retornatus-meta
{
  "change_id": "C-0020",
  "schema_version": 1
}
-->

# Situation

## Demand

CLI users must initialize a background-job repository (Celery, RQ, Dramatiq, arq, scheduled jobs) with retornatus init --preset worker. The preset extends python-platform, adds scope globs for tasks, workers, jobs, schedules, and the Celery app, adds ship globs for task, worker, job, Celery app, beat and schedule, and queue config paths, requires a ship rollback and job retry note that explains retry behavior and why re-running a job is safe when those paths change, keeps celery inspect ping as an optional check, and comments suggested commands for eager-task pytest, an RQ burst worker, and an arq health check. README, the docs guide, and the site list six presets. Out of scope: a new surface kind, a version bump, merging, and publishing. verify checks that the note exists; it does not judge idempotency.

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

- Demand stated: CLI users must initialize a background-job repository (Celery, RQ, Dramatiq, arq, scheduled jobs) with retornatus init --preset worker. The preset extends python-platform, adds scope globs for tasks, workers, jobs, schedules, and the Celery app, adds ship globs for task, worker, job, Celery app, beat and schedule, and queue config paths, requires a ship rollback and job retry note that explains retry behavior and why re-running a job is safe when those paths change, keeps celery inspect ping as an optional check, and comments suggested commands for eager-task pytest, an RQ burst worker, and an arq health check. README, the docs guide, and the site list six presets. Out of scope: a new surface kind, a version bump, merging, and publishing. verify checks that the note exists; it does not judge idempotency.
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
- Proposed WHAT: The worker preset extends python-platform, renders a valid config, is listed by init --list-presets, and makes task paths trigger the ship surface with a retry note while non-task paths stay not required.
- DONE criterion: pytest exits 0
- DONE criterion: ruff check of src tests and scripts exits 0
- DONE criterion: mypy exits 0
- DONE criterion: The HTML documentation check exits 0
- DONE criterion: uv lock check exits 0
- DONE criterion: pytest confirms worker extends python-platform and python
- DONE criterion: init --list-presets prints worker
- DONE criterion: pytest confirms task paths require the retry note
- DONE criterion: pytest confirms non-task paths stay not required
- DONE criterion: pytest confirms README guide and site list six presets
- DONE criterion: CHANGELOG Unreleased records the worker preset

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

Retornatus only has ship and AI surface kinds. The worker preset reuses the ship surface with an optional worker check that covers task, job, schedule, and queue paths, and overrides the ship note subject to ship rollback and job retry, so a task change needs a note on retries and safe re-runs and a deploy change in the same repo needs the same note. The celery inspect ping check is optional because it needs a running broker. tests/test_tasks.py and docs/jobs.md do not match the ship globs.
