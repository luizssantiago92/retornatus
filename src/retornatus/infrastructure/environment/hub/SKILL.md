---
name: retornatus
description: >-
  Retornatus hub — govern software Changes with Demand→Situation→Contract→Action,
  on-demand specialization Skills, Evidence bound to Claims, and Assurance.
  Use whenever implementing product work in a Retornatus-governed repository (.retornatus/).
---

# Retornatus Hub

> Govern the work. Bound the agent. Verify the outcome.

You are working inside a **Retornatus** harness. Do **not** jump straight to code.
Durable truth lives in `.retornatus/`, not in chat.

## Default construction loop

1. `retornatus wake` (or `wake --bridges`) / `project-init` for brownfield context
2. Elicit Situation when needed: `retornatus change elicit --demand "..." --what "..." --done "..."`
3. If no Change: `retornatus change create ...` (use `--draft-contract` when Situation is incomplete)
4. Activate draft Contracts when ready: `retornatus change activate <C-id>`
5. Gate: `retornatus gate contract <C-id>` — must exit 0
6. Check derived status: `retornatus status` (tasks, open questions, next work, assurance)
7. If specialization needed: `retornatus skill need --action <A-id>` then `skill create --need "..." --action <A-id>`
8. **Research current sources on the web**, fill RESEARCH + PROCEDURE in `SKILL.md`
9. `retornatus gate skill-research <S-id>` then `retornatus skill activate <S-id>`
   - Bypass only as governed decision: `skill activate --force --reason "..."`
10. Optional: `retornatus skill export <S-id>` for native Cursor loading
11. `retornatus run <A-id>` — read ExecutionContext (rules, learnings, skills)
12. Implement **ready** work: `retornatus loop next <C-id>` (use `--all-ready` for parallelizable tasks)
13. Advance Tasks: `task start|complete|fail|reopen`
14. Record proof bound to Claims: `retornatus evidence add ... --type test_result --claim <claim-id>`
15. If blocked by discovery: `finding add` → `question open` (IDs auto-number) → resolve with Evidence
16. Reopen Questions when the condition reappears: `question reopen <Q-id>`
17. `retornatus gate evidence <C-id>` and `retornatus verify <C-id>` / `gate assurance` (exit 0)
18. Independent review when needed: `retornatus run <A-id> --assurance`
19. Material Contract change: `change reopen` (archives prior version)
20. Preserve: `retornatus change learn ...` and `retornatus skill evolve ...`
21. Rule Candidates require HUMAN Decision: `decision record` → `rule activate --decision D-xxxx`
22. Hygiene: `retornatus doctor` (draft contracts, skill research gaps, inactive rules)

## Hard rules

- Never claim DONE without Assurance `SATISFIED` from Claim-bound Evidence
- Never activate a Skill with empty RESEARCH (no source URLs) without governed bypass
- Prefer native environment tools; do not reinvent sandboxes
- Subagents consume the same Skill snapshot — do not rewrite Skill mid-execution
- Learning informs; Rules constrain — no automatic authoritative Rules
- Do not invent fake Task dependencies from declaration order
- Bypass is a governed decision, not absence of governance
- Status is a derived projection — durable truth lives in artifacts under `.retornatus/`

## CLI map

| Intent | Command |
| --- | --- |
| Continuity | `wake`, `doctor`, `status`, `project-init` |
| Situation | `change elicit`, `change create`, `change activate`, `change reopen` |
| Skill | `skill create/list/need/activate/evolve/export` |
| Proof | `evidence add --claim`, `verify`, `gate *` |
| Problems | `finding add`, `question open/resolve/reopen` |
| Tasks | `task start/complete/fail/reopen` |
| Next work | `loop next`, `loop next --all-ready` |
| Human boundary | `decision record`, `rule propose/activate` |
