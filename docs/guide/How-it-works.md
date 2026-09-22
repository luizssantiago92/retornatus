# How it works

A complete Change from demand to continuity.

## 1. Continuity first

```bash
retornatus wake
# or: retornatus wake --bridges
```

Wake reconstructs Environment capabilities, Change ids, Rules, Learnings, and rebuilds the disposable SQLite index from files.

## 2. Demand and Situation

A **Demand** is the human intent. **Situation** is enough project understanding to formalize a Contract — not a full design doc.

```bash
retornatus change elicit --demand "…" --what "…" --done "…"
```

Exit `0` means Situation looks sufficient; exit `1` means focused questions remain. Repo signals (stack, tests, CI) feed elicitation on brownfield projects (`project-init`).

## 3. Contract

An active **Contract** is the authoritative obligation: WHAT, constraints, DONE.

```bash
retornatus change create …          # activates when Situation is sufficient
retornatus change create … --draft-contract
retornatus change activate C-0001   # later
retornatus gate contract C-0001     # must exit 0
```

Material changes archive the prior version (`change reopen`) — Contracts are not silently mutated.

## 4. Action and Tasks

An **Action** is a bounded unit of work under Authority. **Tasks** appear when decomposition helps; declaration order is **not** an automatic dependency chain.

```bash
retornatus change create … --task "Implement" --task "Test" --depends "1:0"
retornatus loop next C-0001
retornatus task start C-0001/T-001
```

`loop next` never returns BLOCKED work as “next”.

## 5. Specialization (optional)

```bash
retornatus skill need --action C-0001/A-001
retornatus skill create --need "…" --action C-0001/A-001
# agent researches current docs → fills RESEARCH + PROCEDURE
retornatus gate skill-research S-0001
retornatus skill activate S-0001
retornatus skill export S-0001
```

Governed bypass: `skill activate --force --reason "…"` records Bypass + Decision.

## 6. Execution context

```bash
retornatus run C-0001/A-001
retornatus run C-0001/A-001 --strict-policy
```

Retornatus assembles Rules, Learnings, Skills, Boundaries, and Policy — it does **not** run the model. The host agent implements.

## 7. Evidence and Assurance

```bash
retornatus evidence add -c C-0001 -t test_result -s "…" \
  --source pytest --claim C-0001/claim-done-1
retornatus gate evidence C-0001
retornatus verify C-0001
```

Verdicts: `SATISFIED` · `NOT_SATISFIED` · `INCONCLUSIVE`. Evidence must bind to Claims; staleness uses path-aware `commit:<sha>` when available.

Independent review when needed: `assurance plan` / `assurance review` / `run --assurance`.

## 8. Problems become structure

```bash
retornatus finding add --change C-0001 --observation "…"
retornatus question open --change C-0001 --statement "…" --finding C-0001/F-001
retornatus question resolve C-0001/Q-001 --summary "…" --evidence C-0001/E-001
retornatus question reopen C-0001/Q-001   # if the condition returns
```

Verifiable Questions require Evidence — a summary alone is not establishment.

## 9. Adaptation

```bash
retornatus change learn --title "…" --body "…"
retornatus skill evolve S-0001 --note "…"
retornatus rule propose --statement "Do not …" --applicability "…"
retornatus decision record --kind APPROVE_RULE_ACTIVATION \
  --subject R-0001 --summary "…" --confirm R-0001
retornatus rule activate R-0001 --decision D-0001
```

Learning informs; Rules constrain. Activation always needs a Human Decision.

## 10. Restart

Delete `.retornatus/index/retornatus.db` and run `wake` — semantic history in files remains; the index rebuilds.

Full acceptance narrative: PRD §69.
