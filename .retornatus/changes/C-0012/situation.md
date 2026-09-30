<!-- retornatus-meta
{
  "change_id": "C-0012",
  "schema_version": 1
}
-->

# Situation

## Demand

retornatus init does not add ignore rules for the local index and cache it generates, nor for secret-like files. A private signing key was committed in a sibling project. Make init append an idempotent gitignore block, keep public keys committable, write signing private keys outside the repo, and warn when git tracks a pem or key file. Out of scope: a version bump, merging, and publishing.

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

- Demand stated: retornatus init does not add ignore rules for the local index and cache it generates, nor for secret-like files. A private signing key was committed in a sibling project. Make init append an idempotent gitignore block, keep public keys committable, write signing private keys outside the repo, and warn when git tracks a pem or key file. Out of scope: a version bump, merging, and publishing.
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
- Proposed WHAT: init creates or updates .gitignore with one delimited block for the local index and cache, pem and key files, and env files, while .env.example and public keys under .retornatus/keys stay committable. A second init does not duplicate that block or remove existing lines. receipt keygen keeps the private key outside the repository, and init plus keygen print a warning when git tracks a pem or key file. The changelog, CLI reference, and vulnerability policy describe that behavior.
- DONE criterion: pytest exits 0 for fresh, repeated, and preserved gitignore lines
- DONE criterion: git check-ignore exits 1 for a pub file and exits 0 for pem
- DONE criterion: CHANGELOG Unreleased and CLI.md contain the init ignore rules
- DONE criterion: The vulnerability policy file contains the init ignore rules
- DONE criterion: keygen prints a warning when git tracks a pem file

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

Audit of retornatus 1.4.1: init creates .retornatus/index and .retornatus/runtime but does not teach git to ignore them or secret-like files. Public keys in .retornatus/keys must stay committable. Private signing keys already go to the user config directory; init and keygen should warn when git tracks a pem or key file. No package version bump.
