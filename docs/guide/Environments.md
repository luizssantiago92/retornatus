# Environments

Retornatus prefers **native Environment capabilities** over reimplementation.

## Detection

```bash
retornatus wake
retornatus integrate
```

| Kind | Detected when | Bridges |
| --- | --- | --- |
| `cursor` | `.cursor/` or Cursor env markers | Hub skill + `retornatus.mdc` (+ active Rules) |
| `claude_code` | `CLAUDE.md` or `.claude/` | CLAUDE.md markers + Rules section |
| `codex` | `AGENTS.md` or `.codex/` | AGENTS.md markers + Rules section |
| `github_copilot` | `.github/copilot-instructions.md` or `.github/` | `.github/copilot-instructions.md` |
| `generic` | none of the above | `.retornatus/` only (+ hub install still available) |

## What “native first” means

| Capability | Preference |
| --- | --- |
| Rules / instructions | Host rule files |
| Skills | Host skill directories + `skill export` |
| Isolation | Host worktree / sandbox / subagents (advisory Boundaries) |
| Execution | Host agent runtime |

Retornatus records `HostExecutionRecord` observations; it does not spawn agents.

## Active Rule projection

When Rules are activated, bridges refresh so the host sees the same constraints. The instruction block uses begin/end markers and is replaced when its text changes (it is not appended again):

```html
<!-- retornatus-bridge:begin -->
…
<!-- retornatus-bridge:end -->
```

Active Rules use a separate marked section:

```html
<!-- retornatus-active-rules:begin -->
…
<!-- retornatus-active-rules:end -->
```

Canonical Rules remain in `.retornatus/governance/`.

## Hub skill

`integrate` installs progressive disclosure text so the agent learns the construction loop without pasting the entire PRD each turn.

Source template: `src/retornatus/infrastructure/environment/hub/SKILL.md`.

## Remote machines

Detection is the same on a cloud VM. The CLI and git hooks are not in the clone: install them on that machine, leave receipts unsigned, and let the GitHub pull request run `verify` and the diff gates. See [Cloud agents](Cloud-agents.md).
