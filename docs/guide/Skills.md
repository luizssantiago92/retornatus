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

## Repetition candidates

`skill need` looks for specialization words in the Action or the prompt. It does not notice that the same procedure already succeeded several times. A separate detector does that, without a model, and it only **queues** a suggestion.

It runs when `verify` reaches `SATISFIED`, and when the stop hook allows the turn because Assurance is already satisfied. Nothing to suggest is a normal result.

| Signal | What it measures | Default |
| --- | --- | --- |
| Sequence | The same normalized evidence-command sequence appears in at least `sequence_min_count` Changes that have green executed evidence | 3 Changes, 3 points |
| Retry | Executed evidence failed, and a later run on that Change exited 0 | 2 points |
| Correction | The same user correction appears at least `correction_min_count` times | 2 occurrences, 2 points |

A suggestion is queued when the score reaches `threshold` (default 3). Sequence alone can meet it. Retry alone does not, until you lower the threshold. The two add together when both are present.

Before comparing commands, an absolute path becomes `<PATH>/<filename>` so two different scripts do not collapse into one step, and the same script in two directories still matches. Ids, hashes, dates, pull-request numbers, and bare numbers become variables. A stable relative path such as `scripts/migrate.py` stays, so the same procedure can match. Commands that are exactly an owner-declared `required_checks` entry are the project gate, not a specialization, and are ignored. Changes whose title, demand, or contract matches the trivial markers used by `skill need` (`typo`, `rename`, `docs only`, and the rest) are ignored.

User chat is **not** stored on a Change. The correction signal runs only when the stop hook can read user lines from the host `transcript_path`. Patterns are `no, use`, `don't` / `do not`, `actually`, `não, use`, and `na verdade`. A scan of recorded Changes uses sequence and retry only.

The queue is one markdown file per candidate:

```text
.retornatus/adaptation/skill-candidates/K-0001.md
```

The file names the origin Changes, the repeated commands, the score, and the reason. If an existing `S-000N` already covers the theme, the candidate proposes an update to that skill instead of a new one.

```bash
retornatus skill candidates
retornatus skill accept K-0001
retornatus skill reject K-0001
```

`skill accept` is the only command that writes a Skill from this queue. A new theme becomes a draft `SKILL.md` in the same shape as `skill create`. An update theme evolves the existing skill and does not add a second id. `skill reject` drops the candidate. The same theme comes back only after at least `reject_rearm_count` new origin Changes (default 2).

At most `max_per_session` new candidates are written per session (default 1). A candidate that is mostly ids, dates, and pull-request numbers, with no reusable program, is not queued.

```toml
[adaptation.skill_candidates]
enabled = true
threshold = 3
sequence_min_count = 3
sequence_points = 3
retry_points = 2
correction_min_count = 2
correction_points = 2
max_per_session = 1
reject_rearm_count = 2
```

Missing keys keep these defaults. `enabled = false` turns the detector and the hook line off.

The stop hook and session start may show:

```text
1 skill candidate pending: run `retornatus skill candidates`
```

That line does not block the agent. Ask the user once, with the reason, and do not run `skill accept` unless they say so. See [Agent hooks](Agent-hooks.md).

## Bypass

```bash
retornatus skill activate S-0001 --force --reason "…"
```

Records Bypass + Decision. Prefer research; bypass is governed exception, not the default path.

See also: hub skill text under `src/retornatus/infrastructure/environment/hub/SKILL.md` (installed by `integrate`).
