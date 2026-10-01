# Agent hooks

Three opt-in hooks sit in the agent loop. A session-start hook injects the active Change so the agent begins with the finish line. A file-edit hook warns when an edit leaves that Change's declared scope. A Stop hook asks the agent to keep going when the Change is not `SATISFIED`. Git hooks (`hooks install`) still run at commit time.

All three can be skipped, all three fail open, and a host can cap how many times Stop continues the turn. **CI remains the source of truth.** The pull-request check (`verify`, `gate suppressions`, `gate scope`) is the result that counts. The file-edit hook is an early warning. It does not replace `gate scope`. See [Cloud agents](Cloud-agents.md) and [GitHub Action](GitHub-Action.md).

Subagent hooks and MCP are not installed. The file-edit hook is the only tool hook, and only on the edit events documented below.

This repository does not write the hooks into its own `.claude/`, `.cursor/hooks.json`, or `.codex/`. Run the command in the project you want to guard.

## Install

The CLI must be on `PATH` (`uv tool install retornatus`). Plain `integrate` does not change hook files.

```bash
retornatus integrate --hooks
retornatus integrate --hooks --host cursor
retornatus integrate --remove-hooks
retornatus doctor
```

`--host` is repeatable. Omit it to update Claude, Cursor, and Codex. `--remove-hooks` deletes only the Retornatus Stop, session-start, and file-edit commands. Other hooks and keys stay. A second `--hooks` updates those entries in place and does not add a duplicate.

`doctor` prints `agent hooks:` for each host. `absent` means the file is missing, unreadable as JSON is `unreadable`, and a file with no Retornatus command is `absent`. When a Retornatus command is present the line names each hook, for example `stop=installed session-start=installed file-edit=installed` or `stop=installed session-start=absent file-edit=absent`. Absent is normal. The hooks are opt-in, and a missing hook does not fail `doctor`. For an initialized project, `doctor` also prints `hooks scope_mode:` as `warn`, `block`, `off`, or `invalid`.

## What the hook runs

Each host runs:

```bash
retornatus hook stop --host claude
retornatus hook stop --host cursor
retornatus hook stop --host codex
```

The command reads the host JSON object from stdin. Extra fields are ignored. A non-object is treated as an empty object. It finds `.retornatus/` from the working directory (parents included) and loads every Change whose Contract is active, the same list as the git pre-commit scope hook.

It then runs the same in-process evaluation as `verify --json`. There is no network call and no subprocess back into the CLI.

| Situation | Result |
| --- | --- |
| No `.retornatus/`, or no active Change | Exit 0, no stdout. The turn ends. |
| Every active Change is `SATISFIED` | Exit 0, no stdout. The turn ends. |
| Any active Change is not `SATISFIED`, and the turn is not a question or an interrupted Cursor run | Exit 0 and a host JSON object that continues the turn. The text names the unproven claim ids and a `retornatus evidence run …` command. When `[assurance] required_checks` is set, that command uses the first matching argv. |
| The last assistant message is a question to the user, and `[hooks] allow_questions` is not `false` | Exit 0, no stdout. The turn ends so the person can answer. |
| Invalid JSON, unknown host, or any internal error | Exit 0, no block payload. One `fail-open` line goes to stderr. |

Claude and Codex receive:

```json
{"decision": "block", "reason": "C-0001 is NOT_SATISFIED. Unproven claims: C-0001/claim-done-1 (INCONCLUSIVE). Next: retornatus evidence run …"}
```

Cursor receives:

```json
{"followup_message": "C-0001 is NOT_SATISFIED. Unproven claims: C-0001/claim-done-1 (INCONCLUSIVE). Next: retornatus evidence run …"}
```

`decision` is omitted when the stop is allowed. Cursor's `followup_message` is omitted in that case too. The block text is the same when the hook does continue the turn.

## Questions to the user

Stopping to ask the person a question is allowed. A previous version blocked that turn once, the same way it blocks an unfinished Change. The check is deterministic and does not call a model.

`[hooks] allow_questions` in `.retornatus/config.toml` defaults to `true`. Only a boolean `false` turns it off. A missing key, a missing file, or any other value keeps the default. `doctor` prints `hooks allow_questions: true` or `false` for an initialized project. This table is Retornatus config. It is not the Codex `[hooks]` table, which lives in Codex's own `config.toml`.

```toml
[hooks]
allow_questions = true
```

The text comes from a documented payload field when the host has one. Otherwise the hook reads the tail of `transcript_path`. If neither is available, the hook behaves as it did before this exception: an unsatisfied Change still blocks.

| Host | Assistant text on Stop | Transcript path |
| --- | --- | --- |
| Claude Code | `last_assistant_message` (text of the final response). Prefer this. The transcript can lag the current turn. | Common field `transcript_path` (a `.jsonl` path) |
| Codex | `last_assistant_message` (`string` or `null`) | Common field `transcript_path` (`string` or `null`). The line format is not a stable interface. |
| Cursor | No assistant-text field on `stop`. `afterAgentResponse.text` is a different event and is not read. | Common field `transcript_path` (`string` or `null`). The `stop` object itself is `status` and `loop_count`. |

Checked against the host docs on 2026-09-30:

- [Claude Code hooks](https://code.claude.com/docs/en/hooks) — common fields include `transcript_path`; Stop adds `stop_hook_active`, `last_assistant_message`, `background_tasks`, and `session_crons`.
- [Claude Code sessions](https://code.claude.com/docs/en/sessions) — transcripts are JSONL. Each line is a JSON object. The entry format is internal and can change.
- [Claude Agent SDK agent loop](https://code.claude.com/docs/en/agent-sdk/agent-loop) — an assistant message has `type: "assistant"` and text on `message.content`.
- [Cursor hooks](https://cursor.com/docs/hooks) — common fields include `transcript_path`. `stop` input is `status` (`completed`, `aborted`, or `error`) and `loop_count`. There is no `last_assistant_message`.
- [Codex hooks](https://developers.openai.com/codex/hooks) — common fields include `transcript_path`. Stop adds `turn_id`, `stop_hook_active`, and `last_assistant_message`.

Every field is optional. Extra fields are ignored. Cursor does not use `last_assistant_message` even if a caller adds it, because that field is not in the Cursor `stop` schema.

The transcript read is the last 256 KiB. The partial first line after that cut is dropped. Lines are UTF-8 JSON objects. Malformed lines, non-objects, and lines that are not an assistant turn are ignored. An assistant line is one whose `type` or `role` is `assistant` (also accepted on `message`). Text is an optional string at `text` or `content`, or `message.content` when that is a string or a list of text blocks (`type` `text` and string `text`). Tool, result, and thinking blocks are skipped. A missing file, a non-file, or a read error leaves the text unavailable.

Heuristic, applied to that text:

1. Normalize newlines and strip trailing whitespace.
2. Drop a trailing unclosed fence, then drop trailing closed ` ``` ` blocks.
3. Take the last paragraph that still has visible prose. Paragraphs are separated by a blank line.
4. Remove fenced code, inline code spans, and URL tokens (`http://`, `https://`, `www.`) from that paragraph.
5. It is a question when the remainder ends with `?` or full-width `？` (trailing quotes and brackets do not count), or when it contains one of these phrases at the start or after a sentence boundary: `should i`, `shall i`, `do you want`, `would you like`, `want me to`, `quer que eu`, `posso seguir`, `posso continuar`, `devo seguir`, `devo continuar`, `você quer`, `voce quer`, `prefere que eu`.

A `?` only inside a code fence, an inline span, or a URL does not allow the stop. A question in an earlier paragraph does not count when the final paragraph is a statement. `stop_hook_active` and Cursor `status` `aborted` or `error` are decided before this heuristic. They still allow the stop when `allow_questions` is `false`.

## Session start

Each host also runs:

```bash
retornatus hook session-start --host claude
retornatus hook session-start --host cursor
retornatus hook session-start --host codex
```

The command reads the host JSON object from stdin and ignores extra fields. A non-object is treated as an empty object. It finds `.retornatus/` from the working directory (parents included) and loads every Change whose Contract is active. Evaluation is the same in-process check as `verify --json`. There is no subprocess back into the CLI.

The injected text names, for each active Change:

- id and title
- goal (the Contract WHAT)
- verify status (`SATISFIED`, `NOT_SATISFIED`, or `INCONCLUSIVE`)
- scope summary (the declared Task resources, or `(none declared)`)
- each unproven claim id, its status, and the `retornatus evidence run …` command that would prove it

A satisfied Change still appears, with `unproven: none`, so the session starts on the finish line. The text is capped at 2048 UTF-8 bytes. A longer note ends with `…(truncated)`.

| Situation | Result |
| --- | --- |
| No `.retornatus/`, or no active Change | Exit 0, no stdout |
| `[hooks] session_context = false` | Exit 0, no stdout. The default is true, including when the key is absent |
| One or more active Changes | Exit 0 and the host JSON below |
| Invalid JSON, unknown host, a non-boolean `session_context`, or any internal error | Exit 0, no context. One `fail-open` line goes to stderr |

Claude and Codex receive:

```json
{"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "Retornatus active Change context:\nC-0001 Health command — INCONCLUSIVE\ngoal: The health command exits 0\nscope: src/retornatus/\nunproven: C-0001/claim-done-1 (INCONCLUSIVE). Next: retornatus evidence run …"}}
```

Cursor receives:

```json
{"additional_context": "Retornatus active Change context:\nC-0001 Health command — INCONCLUSIVE\ngoal: The health command exits 0\nscope: src/retornatus/\nunproven: C-0001/claim-done-1 (INCONCLUSIVE). Next: retornatus evidence run …"}
```

Checked against the host docs on 2026-09-30. All three hosts document this event, so all three are installed:

- [Claude Code hooks](https://code.claude.com/docs/en/hooks). `SessionStart` runs from `.claude/settings.json`. Stdin adds `source` (`startup`, `resume`, `clear`, `compact`, or `fork`) to the common fields. Omitting `matcher` runs on every source. Context comes back as `hookSpecificOutput.hookEventName` = `SessionStart` and `hookSpecificOutput.additionalContext`. Plain stdout would also be added as context; this hook uses the JSON form.
- [Cursor hooks](https://cursor.com/docs/hooks). `sessionStart` lives in `.cursor/hooks.json`. Stdin carries `session_id`, `is_background_agent`, and optional `composer_mode`. The output field is `additional_context`. The hook is fire-and-forget. Cloud agents defer `sessionStart` (it would run after the first write, not at true session start). Self-hosted pool workers do run it when a session claims the worker.
- [Codex hooks](https://developers.openai.com/codex/hooks). `SessionStart` lives in `.codex/hooks.json`. That page currently redirects to `https://learn.chatgpt.com/docs/hooks`. Stdin adds `source` (`startup`, `resume`, `clear`, or `compact`). Omitting `matcher` matches every source. JSON on stdout uses the same `hookSpecificOutput.additionalContext` shape as Claude. Plain text on stdout is also extra developer context; invalid JSON is not.

`[hooks] session_context` is Retornatus project config in `.retornatus/config.toml`, the same table as `allow_questions` and `scope_mode`, not the host's `[hooks]` table. Codex can also read inline `[hooks]` from its own `config.toml`. `integrate --hooks` still writes `.codex/hooks.json` only.

```toml
[hooks]
session_context = false
```

## File edit

Each host also runs:

```bash
retornatus hook file-edit --host claude
retornatus hook file-edit --host cursor
retornatus hook file-edit --host codex
```

The command reads the host JSON object from stdin and ignores extra fields. A non-object is treated as an empty object. It finds `.retornatus/` from the working directory (parents included) and loads every Change whose Contract is active. Each edited path is resolved against the repo root and compared with `path_in_scope`, the same match `gate scope` uses for Task resources and `.retornatus/**`. There is no subprocess and no git call.

A path inside the declared scope, a project with no active Change, and anything under `.retornatus/` print nothing. The edit proceeds. A path outside every matching rule prints a short warning: the path, each active Change that does not cover it, that Change's declared scope, and the next step (revert the edit, or add the path to the Change's Task resources). One file must sit inside every active Change, the same way the pre-commit scope hook checks the diff against each active Change.

| Situation | Result |
| --- | --- |
| No `.retornatus/`, or no active Change | Exit 0, no stdout |
| Path in scope for every active Change, or under `.retornatus/` | Exit 0, no stdout |
| `[hooks] scope_mode = "off"` | Exit 0, no stdout. The default is `warn`, including when the key is absent |
| Out of scope, mode `warn` | Exit 0 and the host warning below. The edit is not blocked |
| Out of scope, mode `block`, on an event that documents a deny | Exit 0 and a deny payload. The warning is the deny reason |
| Out of scope, mode `block`, on an event that cannot deny | Exit 0 and the warn payload for that event |
| Invalid JSON, unknown host, a bad `scope_mode`, or any internal error | Exit 0, no decision. One `fail-open` line goes to stderr |

`[hooks] scope_mode` accepts `warn`, `block`, or `off`. Any other value fails open.

```toml
[hooks]
scope_mode = "warn"
```

Checked against the host docs on 2026-10-01. All three hosts have a documented way to put a message back in front of the agent, so all three are installed. Events that cannot carry that message are skipped.

- [Claude Code hooks](https://code.claude.com/docs/en/hooks). `PreToolUse` runs before the tool call. The matcher is `Edit|Write|MultiEdit`. `Write` and `Edit` put the absolute path in `tool_input.file_path` (Windows paths use backslashes; the hook normalizes them). The current reference lists `Write` and `Edit`, not `MultiEdit`; the matcher still includes `MultiEdit` so an older client that sends that name with `file_path` is covered. A warning is `hookSpecificOutput.additionalContext` with `hookEventName` `PreToolUse`. A block is `permissionDecision` `deny` plus `permissionDecisionReason`, which is shown to Claude. `PostToolUse` can also carry `additionalContext`, but it cannot undo the edit, so `block` on that event falls back to the warning.
- [Cursor hooks](https://cursor.com/docs/hooks). `afterFileEdit` matches `Write` and the input field is `file_path`. That section documents no output fields, so the event is not installed. `beforeReadFile` can deny a read with `user_message` shown to the user. That is not an edit, and it is not a message to the agent, so it is not installed. `preToolUse` and `postToolUse` match `Write`. `preToolUse` can return `permission` `deny` and `agent_message` (delivered when the action is denied). It does not document a warning that still lets the tool run, so warn mode stays silent on that event. `postToolUse` returns `additional_context`, which is injected after the tool result. Warn mode uses that field. Block mode denies on `preToolUse` and, if `postToolUse` still runs, falls back to `additional_context`.
- [Codex hooks](https://developers.openai.com/codex/hooks). `PreToolUse` intercepts file edits made through `apply_patch`. The matcher is `apply_patch|Edit|Write`. Stdin still reports `tool_name` `apply_patch`, and the patch body is `tool_input.command`. Paths are the `*** Add File:`, `*** Update File:`, `*** Delete File:`, and `*** Move to:` headers from the [apply_patch grammar](https://github.com/openai/codex/blob/main/codex-rs/prompts/templates/apply_patch_tool_instructions.md). A warning is `hookSpecificOutput.additionalContext`. A block is `permissionDecision` `deny` plus `permissionDecisionReason`. `PostToolUse` can add context after the edit and cannot undo it, so `block` there falls back to the warning.

Claude and Codex, warn mode:

```json
{"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": "src/other.py is outside C-0001 scope (src/retornatus/). Revert the edit, or update the Change scope (Task resources) to include this path."}}
```

Claude and Codex, block mode:

```json
{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": "src/other.py is outside C-0001 scope (src/retornatus/). Revert the edit, or update the Change scope (Task resources) to include this path."}}
```

Cursor warn mode (`postToolUse`):

```json
{"additional_context": "src/other.py is outside C-0001 scope (src/retornatus/). Revert the edit, or update the Change scope (Task resources) to include this path."}
```

Cursor block mode (`preToolUse`):

```json
{"permission": "deny", "agent_message": "src/other.py is outside C-0001 scope (src/retornatus/). Revert the edit, or update the Change scope (Task resources) to include this path."}
```

## Files

Fresh install, with no other keys in the file:

`.claude/settings.json`

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "retornatus hook stop --host claude",
            "timeout": 30
          }
        ]
      }
    ],
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "retornatus hook session-start --host claude",
            "timeout": 30
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "retornatus hook file-edit --host claude",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

`.cursor/hooks.json`

```json
{
  "version": 1,
  "hooks": {
    "stop": [
      {
        "command": "retornatus hook stop --host cursor",
        "loop_limit": 1
      }
    ],
    "sessionStart": [
      {
        "command": "retornatus hook session-start --host cursor",
        "timeout": 30
      }
    ],
    "preToolUse": [
      {
        "command": "retornatus hook file-edit --host cursor",
        "matcher": "Write",
        "timeout": 30
      }
    ],
    "postToolUse": [
      {
        "command": "retornatus hook file-edit --host cursor",
        "matcher": "Write",
        "timeout": 30
      }
    ]
  }
}
```

`.codex/hooks.json`

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "retornatus hook stop --host codex",
            "timeout": 30
          }
        ]
      }
    ],
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "retornatus hook session-start --host codex",
            "timeout": 30
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "apply_patch|Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "retornatus hook file-edit --host codex",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

Existing `version`, permissions, matchers, and other commands stay. The Retornatus command is the identity of the entry, so a later install can replace the timeout or `loop_limit` without adding a second hook.

## Loop guard

Claude and Codex set `stop_hook_active` to true when this turn is already a continuation from a Stop hook. The command allows the stop in that case, so it does not block twice in a row. Claude also stops continuing after eight blocks in a row (`CLAUDE_CODE_STOP_HOOK_BLOCK_CAP`). Codex treats `continue: false` from any matching Stop hook as stronger than a block from another hook.

Cursor has no `stop_hook_active` field. The generated `stop` entry sets `loop_limit` to 1 (the host default is 5). That is one automatic follow-up. `followup_message` is only applied when `status` is `completed`. An `aborted` or `error` status allows the stop. `failClosed` is left at its default, false, so a crash or a timeout does not trap the agent.

## Fail-open

A policy hook that crashes should not freeze the session. Invalid stdin, an unknown `--host`, a raised exception, and a missing project all exit 0 with no block JSON. The diagnostic is a single stderr line that starts with `retornatus hook stop: fail-open`, `retornatus hook session-start: fail-open`, or `retornatus hook file-edit: fail-open`. The command timeout in the Claude and Codex files is 30 seconds (the host default is 600). Cursor's session-start and file-edit entries use the same 30 second timeout. `failClosed` stays at its default, false.

## Codex trust

Codex does not run a project hook until you review and trust that exact definition. Trust is stored against the hook's hash, so the next edit is skipped until you trust it again in `/hooks`. Project hooks also require the `.codex/` layer to be trusted. Untrusted projects still load user and system hooks from their own layers. This page does not enable `--dangerously-bypass-hook-trust`.

Codex can also read inline `[hooks]` from `config.toml`. If one layer contains both `hooks.json` and `[hooks]`, Codex loads both and warns. `integrate --hooks` writes `.codex/hooks.json` only.

## Host notes that differ from earlier write-ups

Checked against the host docs on 2026-09-30:

- [Claude Code hooks](https://code.claude.com/docs/en/hooks). Stop still lives in `.claude/settings.json`. Exit 2 still blocks, and so does exit 0 with `decision: "block"` and `reason`. The Stop hook uses the JSON decision and exit 0. `hookSpecificOutput.additionalContext` on Stop can continue the turn as feedback instead of a block; Stop uses `decision`. Session start uses `additionalContext` inside `hookSpecificOutput`, with `hookEventName` set to `SessionStart`. An `if` filter does not run on Stop, so the generated Stop entry has none. The 8-continuation cap is in addition to `stop_hook_active`. Stop input includes `last_assistant_message`; the hook prefers that field over `transcript_path` because the transcript file can lag the turn.
- [Cursor hooks](https://cursor.com/docs/hooks). Project hooks are `.cursor/hooks.json`. `stop` answers with `followup_message`, not `decision`. `sessionStart` answers with `additional_context`. File edits warn through `postToolUse` `additional_context` and block through `preToolUse` `permission` `deny`. `afterFileEdit` has no documented output fields. Cloud agents run command hooks from that file, including `stop`, once the machine is writable. They do not run hooks during an early read-only turn, and they defer `sessionStart`. `~/.cursor/hooks.json` is not available on a cloud agent VM.
- [Codex hooks](https://developers.openai.com/codex/hooks). The project file is `.codex/hooks.json`. Stop uses `decision: "block"` and `reason`, and it expects JSON on stdout when the process exits 0. Empty stdout allows the stop. Plain text on stdout is invalid for Stop. Session start accepts `hookSpecificOutput.additionalContext` and also treats plain stdout as developer context.

## Related

- [CLI](CLI.md) for `hook file-edit`, `hook session-start`, `hook stop`, and `integrate --hooks`
- [Gates](Gates.md) for what `SATISFIED` means
- [JSON output](JSON-output.md) for the verdict the hook evaluates
- [Cloud agents](Cloud-agents.md) for a clean VM
