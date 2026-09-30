<!-- retornatus-meta
{
  "change_id": "C-0017",
  "schema_version": 1
}
-->

# Situation

## Demand

CLI users must initialize a Django repository with retornatus init --preset django. The preset extends python-platform, adds scope globs for manage.py, */settings*.py, */urls.py, apps/**, */migrations/**, templates/**, and static/**, comments suggested evidence commands for python manage.py check --deploy, python manage.py makemigrations --check --dry-run, and pytest-django or manage.py test, and treats **/migrations/** as a ship surface that requires a rollback note describing how to reverse the migration. The migration check is optional. Out of scope: a version bump, merging, and publishing.

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

- Demand stated: CLI users must initialize a Django repository with retornatus init --preset django. The preset extends python-platform, adds scope globs for manage.py, */settings*.py, */urls.py, apps/**, */migrations/**, templates/**, and static/**, comments suggested evidence commands for python manage.py check --deploy, python manage.py makemigrations --check --dry-run, and pytest-django or manage.py test, and treats **/migrations/** as a ship surface that requires a rollback note describing how to reverse the migration. The migration check is optional. Out of scope: a version bump, merging, and publishing.
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
- Proposed WHAT: The django preset extends python-platform, renders a valid config, is listed by init --list-presets, and makes migration paths trigger the ship surface rollback note.
- DONE criterion: pytest exits 0
- DONE criterion: ruff check of src tests and scripts exits 0
- DONE criterion: mypy exits 0
- DONE criterion: The HTML documentation check exits 0
- DONE criterion: uv lock check exits 0
- DONE criterion: pytest confirms django extends python-platform and python
- DONE criterion: init --list-presets prints django
- DONE criterion: pytest confirms migration paths trigger the ship surface
- DONE criterion: CHANGELOG Unreleased records the django preset

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

Packaged presets already exist under src/retornatus/bootstrap/presets. python-platform extends python, and fastapi extends python-platform. Django defaults must reuse that extends mechanism, keep optional tools commented, and require a ship rollback note when migration paths match. Spec Guardrails appendix B names a migrate reverse plan; this preset records that plan as the rollback note and does not run migrate.
