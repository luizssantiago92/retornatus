<!-- retornatus-meta
{
  "change_id": "C-0025",
  "schema_version": 1
}
-->

# Situation

## Demand

The Stop hook blocks once when the agent stops to ask the user a question. Allow that stop for Claude Code, Cursor, and Codex without weakening the unsatisfied-Change block.

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

- Demand stated: The Stop hook blocks once when the agent stops to ask the user a question. Allow that stop for Claude Code, Cursor, and Codex without weakening the unsatisfied-Change block.
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
- Proposed WHAT: hook stop allows a question to the user, keeps stop_hook_active and Cursor aborted or error, and reads allow_questions from config.
- DONE criterion: pytest exits 0 for the stop question tests
- DONE criterion: Question stops are documented in the agent hooks guide
- DONE criterion: The question-stop fix is documented in the Unreleased changelog
- DONE criterion: ruff check exits 0
- DONE criterion: mypy exits 0
- DONE criterion: html check exits 0
- DONE criterion: uv lock check exits 0

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

Host Stop payloads were checked against current official docs on 2026-09-30. Every field is optional. The hook does not invent fields.

## Host payloads

- [Claude Code hooks](https://code.claude.com/docs/en/hooks). Common input includes `session_id`, `prompt_id`, `transcript_path`, `cwd`, `permission_mode`, `effort`, and `hook_event_name`. Stop adds `stop_hook_active`, `last_assistant_message` (text of the final response), `background_tasks`, and `session_crons`. The docs say to prefer `last_assistant_message` because `transcript_path` can lag the current turn.
- [Claude Code sessions](https://code.claude.com/docs/en/sessions). Transcripts are JSONL. Each line is a JSON object. The entry format is internal and can change between versions.
- [Claude Agent SDK agent loop](https://code.claude.com/docs/en/agent-sdk/agent-loop). An assistant message uses `type: "assistant"` and text on `message.content`.
- [Cursor hooks](https://cursor.com/docs/hooks). Common input includes `conversation_id`, `generation_id`, `model`, `model_id`, `model_params`, `hook_event_name`, `cursor_version`, `workspace_roots`, `user_email`, and `transcript_path` (`string` or `null`). The `stop` input is `status` (`completed`, `aborted`, or `error`) and `loop_count`. There is no `last_assistant_message` on `stop`. `afterAgentResponse.text` is a different event.
- [Codex hooks](https://developers.openai.com/codex/hooks). Common input includes `session_id`, `transcript_path` (`string` or `null`), `cwd`, `hook_event_name`, `model`, and `permission_mode`. Stop adds `turn_id`, `stop_hook_active`, and `last_assistant_message` (`string` or `null`). The transcript line format is not a stable interface.

When `last_assistant_message` is a string (Claude and Codex), that string is the assistant text. Otherwise the hook reads the last 256 KiB of `transcript_path` as JSONL, drops a partial first line, and ignores malformed lines. A line counts only when `type` or `role` is `assistant`. Text is taken from optional `text` or `content` strings, or from text blocks. If no text is available, the hook keeps the previous decision.

The question heuristic: drop trailing code fences, take the last non-empty paragraph, ignore fenced code, inline code, and URLs, then allow the stop when that paragraph ends with `?` or `？`, or when it starts with (or follows a sentence boundary with) one of: should i, shall i, do you want, would you like, want me to, quer que eu, posso seguir, posso continuar, devo seguir, devo continuar, você quer, voce quer, prefere que eu.

`[hooks] allow_questions` in `.retornatus/config.toml` defaults to true. Only boolean false disables the exception. Cursor `status` `aborted` or `error`, and Claude/Codex `stop_hook_active`, still allow the stop before that check. Fail-open and the block message stay as they are.
