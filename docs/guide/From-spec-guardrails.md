# From Spec Guardrails

[Spec Guardrails](https://github.com/luizssantiago92/spec-guardrails) is the **direct predecessor** of Retornatus. This page is a migration map — not a 1:1 command clone.

Retornatus preserves the *guarantees* (plan before code, gates as brakes, proof before done, repo memory, human checkpoints) and rethinks the *mechanisms*.

## Phase → Retornatus

| Spec Guardrails idea | Retornatus equivalent |
| --- | --- |
| Spec / clarify before code | **Situation** via `change elicit` (requirements analysis) |
| Written acceptance | **Contract** (WHAT + DONE) → `gate contract` |
| Tasks / waves | **Action** + embedded **Tasks** → `loop next` / `task *` |
| Execute under host | `run` assembles ExecutionContext (agent still writes code) |
| Verify / proof | Claim-bound **Evidence** → `verify` / `gate assurance` |
| Memory / restart | `.retornatus/` + `wake` / Learnings |
| Human approval | **Decision** → Rule activate; Policy `REQUIRE_HUMAN` |
| Skills pack | Hub skill + **one** on-demand Skill (`intake analyze` / `skill create`) |

## Mental remap

```text
SG:   Spec → Tasks → Execute → Verify
Reto: Situation → Contract → Action(+Tasks) → Evidence → Assurance → Learning
```

## Commands people ask about

| You used to think… | Try in Retornatus |
| --- | --- |
| “Write the spec” | `change elicit` then `change create` / `change activate` |
| “Break into tasks” | `change create --task …` or Tasks on the Action |
| “What’s next?” | `loop next <C-id>` / `change overview <C-id>` |
| “Are we done?” | `evidence add --claim …` then `verify <C-id>` |
| “Load the skill pack” | `integrate` (hub) + optional `intake analyze` / `skill need --prompt` |
| “Doctor / health” | `doctor` (Process vs Brakes) |

## What deliberately did **not** come over

- Drop-in CLI clone of Spec Guardrails commands
- npm packaging / `.specs/` layout
- Rebuilding host sandboxes inside the harness

See [Credits & lineage](../credits-and-lineage.md) and [Non-goals](Non-goals.md).
