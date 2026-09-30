<!-- retornatus-meta
{
  "change_id": "C-0026",
  "schema_version": 1
}
-->

# Situation

## Demand

Add an opt-in session-start hook so Claude Code, Cursor, and Codex inject the active Change finish line when a session starts.

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

- Demand stated: Add an opt-in session-start hook so Claude Code, Cursor, and Codex inject the active Change finish line when a session starts.
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
- Proposed WHAT: Add retornatus hook session-start for Claude, Cursor, and Codex, install it with integrate --hooks beside the Stop hook, honor [hooks] session_context, and document the injected context.
- DONE criterion: tests/test_agent_hooks.py exits 0
- DONE criterion: src/retornatus/cli/hook.py contains session-start for claude, cursor, and codex
- DONE criterion: The file /guide/Agent-hooks.md contains SessionStart, additionalContext, additional_context, and session_context
- DONE criterion: The file /CLI.md contains hook session-start
- DONE criterion: The file /guide/README.md contains session-start
- DONE criterion: The file /README.md contains session-start
- DONE criterion: The file /CHANGELOG.md contains an Unreleased session-start entry
- DONE criterion: The file /Cloud-agents.md contains sessionStart
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

Phase 2a adds a session-start hook beside the Stop hook. Host docs checked 2026-09-30: Claude Code SessionStart returns hookSpecificOutput.additionalContext (https://code.claude.com/docs/en/hooks). Cursor sessionStart returns additional_context (https://cursor.com/docs/hooks). Codex SessionStart returns hookSpecificOutput.additionalContext (https://developers.openai.com/codex/hooks). All three hosts are in scope because each documents a session-start context field. PreToolUse, subagent hooks, MCP, and enabling hooks in this repository stay out of scope. The command computes active Changes in-process, caps context near 2 KB, emits nothing when no Change is active, and fails open.
