# Skills

Retornatus does **not** ship a giant library of preloaded skills that rot.

When work needs specialization, you create **one** Skill for that need, research **current** sources, then activate under a gate. An Action is **optional** — propose Skills as soon as the need is visible in chat.

## Lifecycle

```text
skill need? (prompt or Action) → create → research (web/docs) → fill RESEARCH + PROCEDURE
           → gate skill-research → activate → export? → evolve from Learning
```

```bash
# Early — freeform prompt, before Contract/Action
retornatus skill need --prompt "Add Stripe webhook signature verification"
retornatus skill create --need "Stripe webhook signatures (current API)"

# Later — bound to an Action when one exists
retornatus skill need --action C-0001/A-001
retornatus skill create --need "Stripe webhook signatures (current API)" --action C-0001/A-001
retornatus inspect S-0001
# agent fills .retornatus/adaptation/skills/S-0001/SKILL.md
retornatus gate skill-research S-0001
retornatus skill activate S-0001
retornatus skill export S-0001
retornatus skill evolve S-0001 --note "Added timestamp tolerance"
```

## Storage vs projection

| Location | Role |
| --- | --- |
| `.retornatus/adaptation/skills/S-xxxx/SKILL.md` | Canonical Skill |
| `.cursor/skills/…` (or host equivalent) | Native projection via `export` / hub |

Subagents should consume the **same snapshot** — do not rewrite Skill mid-execution.

## Complexity-sensitive need

`skill need` skips ceremony for trivial work (e.g. typo fixes) and flags specialization when complexity or novelty warrants it. Use `--prompt` / `--demand` / `--what` so agents can offer Skills **without waiting for an Action**.

## Bypass

```bash
retornatus skill activate S-0001 --force --reason "…"
```

Records Bypass + Decision. Prefer research; bypass is governed exception, not the default path.

See also: hub skill text under `src/retornatus/infrastructure/environment/hub/SKILL.md` (installed by `integrate`).
