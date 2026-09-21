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
3. If no Change: `retornatus change create ...` (Contract activates only when Situation is sufficient)
4. Gate: `retornatus gate contract <C-id>` — must exit 0
5. If specialization needed: `retornatus skill create --need "..." --action <A-id>`
6. **Research current sources on the web**, fill RESEARCH + PROCEDURE in `SKILL.md`
7. `retornatus gate skill-research <S-id>` then `retornatus skill activate <S-id>`
   - Bypass only as governed decision: `skill activate --force --reason "..."`
8. Optional: `retornatus skill export <S-id>` for native Cursor loading
9. `retornatus run <A-id>` — read ExecutionContext (rules, learnings, skills)
10. Implement **ready** work: `retornatus loop next <C-id>` (use `--all-ready` for parallelizable tasks)
11. Record proof bound to Claims: `retornatus evidence add ... --type test_result --claim <claim-id>`
12. If blocked by discovery: `retornatus finding add` → `retornatus question open`
13. Resolve Questions with Evidence: `question resolve ... --evidence <E-id>` (not summary alone)
14. `retornatus gate evidence <C-id>` and `retornatus verify <C-id>` / `gate assurance` (exit 0)
15. Independent review when needed: `retornatus run <A-id> --assurance`
16. Preserve: `retornatus change learn ...` and `retornatus skill evolve ...`
17. Rule Candidates require HUMAN Decision: `decision record` → `rule activate --decision D-xxxx`

## Hard rules

- Never claim DONE without Assurance `SATISFIED` from Claim-bound Evidence
- Never activate a Skill with empty RESEARCH (no source URLs) without governed bypass
- Prefer native environment tools; do not reinvent sandboxes
- Subagents consume the same Skill snapshot — do not rewrite Skill mid-execution
- Learning informs; Rules constrain — no automatic authoritative Rules
- Do not invent fake Task dependencies from declaration order
- Bypass is a governed decision, not absence of governance

## CLI map

| Intent | Command |
| --- | --- |
| Continuity | `wake`, `doctor`, `project-init` |
| Situation | `change elicit`, `change create` |
| Skill | `skill create/list/activate/evolve/export` |
| Proof | `evidence add --claim`, `verify`, `gate *` |
| Problems | `finding add`, `question open/resolve` |
| Next work | `loop next`, `loop next --all-ready` |
| Human boundary | `decision record`, `rule propose/activate` |
