# Memory

Memory is durable engineering continuity — not Runtime, not Status, not Evidence.

> Memory remembers; it does not decide.

## What persists

| Artifact | Where | Role |
| --- | --- | --- |
| Learnings | `.retornatus/adaptation/learnings/` | Validated experience |
| Rules | `.retornatus/governance/rules/` | Constraints (after Human Decision) |
| Change history | `.retornatus/changes/` | Situation, Contracts, Evidence, Questions |
| Project notes | `.retornatus/project/project.md` | Brownfield continuity (`project-init`) |

## Derived index

SQLite + FTS5 under `.retornatus/index/` is **disposable**:

```bash
rm .retornatus/index/retornatus.db   # safe
retornatus wake                      # rebuilds from files
retornatus search "evidence"
```

## Recording Learning

```bash
retornatus change learn \
  --title "Always bind Evidence with --claim" \
  --body "Verify stayed INCONCLUSIVE until Claims were linked." \
  --summary "Claim-bound Evidence"
```

Learnings may seed Rule Candidates; they never auto-activate Rules.

## Context assembly

`retornatus run <action-id>` selects **relevant** Rules and Learnings (applicability / tokens) — sufficient context, not the entire history.

Independent Assurance contexts omit author-linked Learning conclusions (`run --assurance`).

## Wake Up

```bash
retornatus wake
retornatus wake --bridges
retornatus doctor
```

Wake reports Environment, Changes, Rules, Learnings, index health, and hygiene warnings (draft Contracts, inactive Rules, …).

See PRD §§36–38, §45.
