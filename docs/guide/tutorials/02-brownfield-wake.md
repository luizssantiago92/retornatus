# Tutorial 02 — Brownfield wake

Install Retornatus on an **existing** application repo and recover continuity.

## Setup

```bash
cd /path/to/existing-app
retornatus init
retornatus project-init
retornatus integrate
retornatus wake --bridges
retornatus doctor
```

Inspect `.retornatus/project/project.md` — stack, tests, and layout signals should appear for Situation elicitation.

## Open a small Change

Pick a real, low-risk improvement (docs fix, health check, logging). Prefer a Demand you can prove with a test or repository observation.

```bash
retornatus change elicit --demand "…" --what "…" --done "…"
retornatus change create …
retornatus gate contract C-0001
```

If elicitation is insufficient, keep a draft Contract and activate later:

```bash
retornatus change create … --draft-contract
# …gather answers…
retornatus change activate C-0001
```

## Prove continuity after interruption

```bash
rm .retornatus/index/retornatus.db
retornatus wake
retornatus status
retornatus search "health"   # or a token from your Learning/Change
```

Change ids, Rules, and Learnings should still resolve; the index count should be non-zero after wake.

## Checkpoint

- [ ] `project.md` exists and reflects the repo
- [ ] Host bridges exist for your Environment
- [ ] Index rebuilds after deletion
- [ ] `doctor` shows no blocking diagnostics (warnings about drafts are OK)
