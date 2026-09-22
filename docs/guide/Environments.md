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

When Rules are activated, bridges refresh so the host sees the same constraints. Markers:

```html
<!-- retornatus-active-rules:begin -->
…
<!-- retornatus-active-rules:end -->
```

Canonical Rules remain in `.retornatus/governance/`.

## Hub skill

`integrate` installs progressive disclosure text so the agent learns the construction loop without pasting the entire PRD each turn.

Source template: `src/retornatus/infrastructure/environment/hub/SKILL.md`.
