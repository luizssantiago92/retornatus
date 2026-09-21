"""Bundled Retornatus hub skill text (native Cursor/Claude progressive disclosure)."""

from __future__ import annotations

from pathlib import Path

# Kept as a module constant so wheel installs always include the hub skill.
HUB_SKILL_MD = """---
name: retornatus
description: >-
  Retornatus hub — govern software Changes with Demand→Contract→Action,
  on-demand specialization Skills, Evidence, and Assurance. Use whenever
  implementing product work in a Retornatus-governed repository (.retornatus/).
---

# Retornatus Hub

> Govern the work. Bound the agent. Verify the outcome.

You are working inside a **Retornatus** harness. Do **not** jump straight to code.
Durable truth lives in `.retornatus/`, not in chat.

## Default construction loop

1. `retornatus wake` (or `wake --bridges`)
2. If no Change: `retornatus change create ...`
3. Gate: `retornatus gate contract <C-id>` — must exit 0
4. If specialization needed: `retornatus skill create --need "..." --action <A-id>`
5. **Research current sources on the web**, fill RESEARCH + PROCEDURE in `SKILL.md`
6. `retornatus gate skill-research <S-id>` then `retornatus skill activate <S-id>`
7. Optional: `retornatus skill export <S-id>` for native Cursor loading
8. `retornatus run <A-id>` — read ExecutionContext (rules, learnings, skills)
9. Implement **one** next unit: `retornatus loop next <C-id>`
10. Record proof: `retornatus evidence add ... --type test_result`
11. If blocked by discovery: `retornatus finding add` → `retornatus question open`
12. `retornatus gate evidence <C-id>` and `retornatus verify <C-id>` (exit 0 required)
13. Preserve: `retornatus change learn ...` and `retornatus skill evolve ...`

## Hard rules

- Never claim DONE without Assurance `SATISFIED`
- Never activate a Skill with empty RESEARCH (no source URLs)
- Prefer native environment tools; do not reinvent sandboxes
- Subagents consume the same Skill snapshot — do not rewrite Skill mid-execution
- Learning informs; Rules constrain — no automatic authoritative Rules

## CLI map

| Intent | Command |
| --- | --- |
| Continuity | `wake`, `doctor`, `project-init` |
| Change | `change create`, `status`, `inspect` |
| Skill | `skill create/list/activate/evolve/export` |
| Proof | `evidence add`, `verify`, `gate *` |
| Problems | `finding add`, `question open/resolve` |
| Next work | `loop next` |
"""


def install_hub_skill(root: Path) -> Path:
    """Install the Retornatus hub skill into `.cursor/skills/retornatus/`."""
    dest_dir = root.resolve() / ".cursor" / "skills" / "retornatus"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / "SKILL.md"
    dest.write_text(HUB_SKILL_MD, encoding="utf-8")
    return dest
