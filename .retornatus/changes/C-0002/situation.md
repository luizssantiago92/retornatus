<!-- retornatus-meta
{
  "change_id": "C-0002",
  "schema_version": 1
}
-->

# Situation

## Demand

Replace HMAC receipts with Ed25519 public keys and harden the CLI against path and search crashes

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

- `prd/PRD.md`

## Repo signals (inferred)

- stack manifests: `pyproject.toml`
- tests: tests/, pytest (pyproject)
- ci: `ci.yml`, `pages.yml`, `publish.yml`
- architecture: AGENTS.md; src packages: retornatus
- code path present: `src`
- Retornatus already initialized

## Known facts

- Demand stated: Replace HMAC receipts with Ed25519 public keys and harden the CLI against path and search crashes
- Repo: stack manifests: `pyproject.toml`
- Repo: tests: tests/, pytest (pyproject)
- Repo: ci: `ci.yml`, `pages.yml`, `publish.yml`
- Repo: architecture: AGENTS.md; src packages: retornatus
- Repo: code path present: `src`
- Repo: Retornatus already initialized
- Kickoff `prd/PRD.md` present (1494 chars loaded)
- From `prd/PRD.md`: Govern the work. Bound the agent. Verify the outcome.**
- From `prd/PRD.md`: coordination;
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
- Proposed WHAT: Receipts are Ed25519-signed with the private key outside the repo and the public key committed; the CLI rejects bad ids and bad FTS queries with documented exit codes
- DONE criterion: Tampered or wrong-key receipts fail verification
- DONE criterion: A fresh clone verifies with only the committed public key
- DONE criterion: Invalid ids and FTS queries print a clean error and a documented exit code

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

HMAC key lives in .retornatus/runtime and README calls receipts portable. CLI prints Rich tracebacks for path traversal ids and raw FTS queries. Private key must never be stored in the repo. Legacy HMAC receipts remain verifiable as legacy_hmac and not portable. Do not bump version or touch release workflows.
