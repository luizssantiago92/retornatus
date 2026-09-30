<!-- retornatus-meta
{
  "change_id": "C-0023",
  "schema_version": 1
}
-->

# Situation

## Demand

Add an opt-in agent Stop hook so Claude Code, Cursor, and Codex cannot finish a turn while an active Change is not SATISFIED.

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

- Demand stated: Add an opt-in agent Stop hook so Claude Code, Cursor, and Codex cannot finish a turn while an active Change is not SATISFIED.
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
- Proposed WHAT: Add retornatus hook stop and retornatus integrate --hooks for Claude, Cursor, and Codex turn-end hooks, report them from doctor, and document the guardrail.
- DONE criterion: tests/test_agent_hooks.py exits 0
- DONE criterion: src/retornatus/cli/hook.py contains hook stop for claude, cursor, and codex
- DONE criterion: The file /guide/Agent-hooks.md contains loop guard, fail-open, and CI as the source of truth
- DONE criterion: The file /README.md contains a link to Agent-hooks
- DONE criterion: The file /guide/README.md contains a link to Agent-hooks
- DONE criterion: The file /index.html contains a link to Agent-hooks
- DONE criterion: The file /CHANGELOG.md contains an Unreleased agent hooks entry
- DONE criterion: The file /Cloud-agents.md contains that Cursor cloud agents run project hooks
- DONE criterion: The file /CLI.md contains hook stop and integrate --hooks
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

Phase 1 installs an opt-in turn-end hook only. retornatus hook stop reads host JSON from stdin, verifies active Changes in-process, allows SATISFIED, and blocks NOT_SATISFIED in each host format. No active Change or missing .retornatus allows the stop. stop_hook_active and Cursor loop_limit prevent a second block. Internal errors fail open. SessionStart, PreToolUse, subagent hooks, and MCP are out of scope. Hooks are not enabled in this repository.
