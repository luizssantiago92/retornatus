# Tutorial 01 — First Change

Build a tiny governed Change end-to-end. Substitute your stack’s health route as needed.

## Setup

```bash
retornatus init
retornatus integrate
retornatus doctor
```

## Elicit and create

```bash
retornatus change elicit \
  --demand "Expose a liveness check for ops" \
  --what "GET /health returns 200 with status ok" \
  --done "Automated test covers /health" \
  --done "Endpoint documented"

retornatus change create \
  --title "Add health endpoint" \
  --demand "Expose a liveness check for ops" \
  --what "GET /health returns 200 with status ok" \
  --done "Automated test covers /health" \
  --done "Endpoint documented" \
  --objective "Implement and verify health endpoint" \
  --task "Implement handler" \
  --task "Add automated test" \
  --depends "1:0"
```

Note the printed `C-0001` / `A-001` / `T-001` ids.

## Gate and plan work

```bash
retornatus gate contract C-0001
retornatus status
retornatus loop next C-0001
retornatus run C-0001/A-001
```

Implement in your agent/host. Advance tasks:

```bash
retornatus task start C-0001/T-001
retornatus task complete C-0001/T-001
retornatus loop next C-0001
```

## Optional Skill

Only if `skill need` says specialization is required:

```bash
retornatus skill need --action C-0001/A-001
retornatus skill create --need "Framework health-check patterns (current docs)" --action C-0001/A-001
# research + fill SKILL.md
retornatus gate skill-research S-0001
retornatus skill activate S-0001
```

## Prove

Claim ids follow Contract DONE order (`claim-done-1`, …). Adjust if your inspect output differs.

```bash
retornatus evidence add -c C-0001 -t test_result -s "/health" \
  --source pytest --state passing --claim C-0001/claim-done-1
retornatus evidence add -c C-0001 -t repository_observation -s "docs/health.md" \
  --source filesystem --claim C-0001/claim-done-2
retornatus gate evidence C-0001
retornatus verify C-0001
```

Expect `SATISFIED`. If `INCONCLUSIVE`, check `--claim` binding.

## Preserve

```bash
retornatus change learn \
  --title "Health endpoint Evidence must be Claim-bound" \
  --body "Tutorial 01: verify required --claim on evidence add."
```

## Checkpoint

- [ ] `gate contract` exited 0
- [ ] Tasks progressed via lifecycle commands
- [ ] `verify` returned SATISFIED
- [ ] Learning recorded
