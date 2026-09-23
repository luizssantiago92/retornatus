# Skills

Retornatus does **not** ship a giant library of preloaded skills that rot.

When work needs specialization, you create **one** Skill for that need, research **current** sources, then activate under a gate.

## Two worlds

| Path | When | Control |
| --- | --- | --- |
| **Analyzed intake** | Freeform chat prompt may need specialization | `intake analyze` → human answers → `--create-skill` |
| **Manual** | Human explicitly asks for a Skill | `skill create --need "…"` |

Agents must **not** auto-create Skills from a prompt without human `CREATE=yes`.

```bash
retornatus intake analyze --prompt "Add Stripe webhook signature verification"
# ask Focused questions in chat, then:
retornatus intake analyze --prompt "…" \
  --answer "SPECIALIZATION=yes — create a Skill" \
  --answer "NEED=Stripe webhook signatures (current API)" \
  --answer "CREATE=yes — create DRAFT now" \
  --create-skill
```

## Lifecycle

```text
intake analyze? / skill need? → (human confirm) → create → research → activate
```

```bash
# Early signal only (no create):
retornatus skill need --prompt "Add Stripe webhook signature verification"

# Bound to an Action when one exists:
retornatus skill need --action C-0001/A-001
retornatus skill create --need "Stripe webhook signatures (current API)" --action C-0001/A-001
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
