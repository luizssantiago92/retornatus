# Agent hooks

An opt-in Stop hook asks the coding agent to keep going when an active Change is not `SATISFIED`. Git hooks (`hooks install`) still run at commit time. This page is the agent turn-end hook.

The hook is a guardrail inside the agent loop. It can be skipped, it can fail open, and a host can cap how many times it continues the turn. **CI remains the source of truth.** The pull-request check (`verify`, `gate suppressions`, `gate scope`) is the result that counts. See [Cloud agents](Cloud-agents.md) and [GitHub Action](GitHub-Action.md).

Phase 1 is the turn-end hook only. Session start, tool gates, subagent hooks, and MCP are not installed.

This repository does not write the hook into its own `.claude/`, `.cursor/hooks.json`, or `.codex/`. Run the command in the project you want to guard.

## Install

The CLI must be on `PATH` (`uv tool install retornatus`). Plain `integrate` does not change hook files.

```bash
retornatus integrate --hooks
retornatus integrate --hooks --host cursor
retornatus integrate --remove-hooks
retornatus doctor
```

`--host` is repeatable. Omit it to update Claude, Cursor, and Codex. `--remove-hooks` deletes only the Retornatus command. Other hooks and keys stay. A second `--hooks` updates the Retornatus entry in place and does not add a duplicate.

`doctor` prints `agent hooks:` with `installed`, `absent`, or `unreadable` for each host. Absent is normal. The hook is opt-in, and a missing hook does not fail `doctor`.

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
| Any active Change is not `SATISFIED` | Exit 0 and a host JSON object that continues the turn. The text names the unproven claim ids and a `retornatus evidence run …` command. When `[assurance] required_checks` is set, that command uses the first matching argv. |
| Invalid JSON, unknown host, or any internal error | Exit 0, no block payload. One `fail-open` line goes to stderr. |

Claude and Codex receive:

```json
{"decision": "block", "reason": "C-0001 is NOT_SATISFIED. Unproven claims: C-0001/claim-done-1 (INCONCLUSIVE). Next: retornatus evidence run …"}
```

Cursor receives:

```json
{"followup_message": "C-0001 is NOT_SATISFIED. Unproven claims: C-0001/claim-done-1 (INCONCLUSIVE). Next: retornatus evidence run …"}
```

`decision` is omitted when the stop is allowed. Cursor's `followup_message` is omitted in that case too.

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
    ]
  }
}
```

Existing `version`, permissions, matchers, and other commands stay. The Retornatus command is the identity of the entry, so a later install can replace the timeout or `loop_limit` without adding a second hook.

## Loop guard

Claude and Codex set `stop_hook_active` to true when this turn is already a continuation from a Stop hook. The command allows the stop in that case, so it does not block twice in a row. Claude also stops continuing after eight blocks in a row (`CLAUDE_CODE_STOP_HOOK_BLOCK_CAP`). Codex treats `continue: false` from any matching Stop hook as stronger than a block from another hook.

Cursor has no `stop_hook_active` field. The generated `stop` entry sets `loop_limit` to 1 (the host default is 5). That is one automatic follow-up. `followup_message` is only applied when `status` is `completed`. An `aborted` or `error` status allows the stop. `failClosed` is left at its default, false, so a crash or a timeout does not trap the agent.

## Fail-open

A policy hook that crashes should not freeze the session. Invalid stdin, an unknown `--host`, a raised exception, and a missing project all exit 0 with no block JSON. The diagnostic is a single stderr line that starts with `retornatus hook stop: fail-open`. The command timeout in the Claude and Codex files is 30 seconds (the host default is 600).

## Codex trust

Codex does not run a project hook until you review and trust that exact definition. Trust is stored against the hook's hash, so the next edit is skipped until you trust it again in `/hooks`. Project hooks also require the `.codex/` layer to be trusted. Untrusted projects still load user and system hooks from their own layers. This page does not enable `--dangerously-bypass-hook-trust`.

Codex can also read inline `[hooks]` from `config.toml`. If one layer contains both `hooks.json` and `[hooks]`, Codex loads both and warns. `integrate --hooks` writes `.codex/hooks.json` only.

## Host notes that differ from earlier write-ups

Checked against the host docs on 2026-09-30:

- [Claude Code hooks](https://code.claude.com/docs/en/hooks). Stop still lives in `.claude/settings.json`. Exit 2 still blocks, and so does exit 0 with `decision: "block"` and `reason`. This hook uses the JSON decision and exit 0. `hookSpecificOutput.additionalContext` can continue the turn as feedback instead of a block; this hook uses `decision`. An `if` filter does not run on Stop, so the generated entry has none. The 8-continuation cap is in addition to `stop_hook_active`.
- [Cursor hooks](https://cursor.com/docs/hooks). Project hooks are `.cursor/hooks.json`. `stop` answers with `followup_message`, not `decision`. Cloud agents run command hooks from that file, including `stop`, once the machine is writable. They do not run hooks during an early read-only turn, and they do not run `sessionStart`. `~/.cursor/hooks.json` is not available on a cloud agent VM.
- [Codex hooks](https://developers.openai.com/codex/hooks). The project file is `.codex/hooks.json`. Stop uses `decision: "block"` and `reason`, and it expects JSON on stdout when the process exits 0. Empty stdout allows the stop. Plain text on stdout is invalid for this event.

## Related

- [CLI](CLI.md) for `hook stop` and `integrate --hooks`
- [Gates](Gates.md) for what `SATISFIED` means
- [JSON output](JSON-output.md) for the verdict the hook evaluates
- [Cloud agents](Cloud-agents.md) for a clean VM
