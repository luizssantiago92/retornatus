# Landscape — adjacent harnesses

How Retornatus sits next to other open-source “agent governance / harness” projects (as of research in 2026). This is **positioning**, not a claim that Retornatus replaces them.

## Family resemblance

All of these attack the same pain: agents are optimistic; “done” needs structure and proof. They differ in **where** they put authority (repo files vs runtime wrapper vs crypto receipts).

| Project | Core bet | Similar to Retornatus? |
| --- | --- | --- |
| **Retornatus** | Repo-native Change loop under `.retornatus/`; host writes code; Evidence ≠ Assurance | — |
| [Spec Guardrails](https://github.com/luizssantiago92/spec-guardrails) | Predecessor; `.specs/` + skill-driven phases | **Closest lineage** — same family, different architecture |
| [TAUSIK](https://github.com/Kibertum/tausik-core) | Fail-closed gates + **ed25519 signed receipts** | Similar *goals*; heavier crypto/enforcement product |
| [Claim Plane](https://github.com/SkeinRank/claim-plane) | Control plane around Codex: scope admission, diff verify, sealed digests | Similar *proof-of-delivery*; more session/runtime control plane |
| [MartinLoop](https://github.com/Keesan12/martin-loop) | Budgets, verifier gates, signed run records around CLIs | Similar *gates*; focuses on run budgets / wrappers |
| [HighHarness](https://github.com/MAHADEV369/HighHarness) | Default-deny tool permissions + hash-chained episode logs | Similar *audit trail*; permission engine is host-layer (we stay native-first) |
| [obsigna / Agent Receipts](https://github.com/agent-receipts/obsigna) | Cryptographic receipt protocol (PyPI SDK + daemon) | Complementary — we now emit a **light HMAC receipt** on `verify`; not a full receipt mesh |
| [Microsoft AGT](https://github.com/microsoft/agent-governance-toolkit) | MCP-governed tool calls + offline receipts / SLSA | Enterprise toolkit; different packaging surface |
| [OpenAI harness practice](https://openai.com/index/harness-engineering/) | `AGENTS.md` map + mechanical CI invariants | Pattern we adopt for discoverability — not a competing product |
| [loop-harness](https://github.com/breim/loop-harness) | Qualify/scaffold autonomous loops (maker/checker) | Adjacent for *ops loops*; Retornatus `ops` stays lighter |

## Are we “the same”?

**Short answer: same problem class, different product shape.**

- **Yes, similar:** plan/gates/proof/memory; host-agnostic intent; stop-on-failure exits.
- **No, not clones:** Retornatus is a **structured Change method** (Situation→Contract→Evidence→Assurance) in Python under git — not a permission proxy, not a Codex control plane, not a signed-receipt network.

## What Retornatus uniquely emphasizes

1. **Situation as requirements analysis** before Contract  
2. **Evidence bound to Claims** with Assurance as a separate judgment  
3. **Complexity lanes** (QUICK / STANDARD / COMPLEX)  
4. **Human-controlled Skill intake** (`CREATE=yes`)  
5. **Native-first** — prefer Cursor/Codex isolation over rebuilding sandboxes  

## What we borrowed as ideas (not code)

| Idea in Retornatus | Inspired by (class) |
| --- | --- |
| `verify --receipt` (HMAC, local key) | TAUSIK / obsigna / AGT receipt class |
| Optional Action attempt budget | MartinLoop budget class |
| `AGENTS.md` map | OpenAI harness practice |
| Docs HTML `--check` in CI | Doc-gardening / mechanical invariants |

No code was vendored from those repositories. Relationship is conceptual.

## Honest overlap gaps

| They often have | Retornatus stance |
| --- | --- |
| Live multi-provider agent runtime tests | Environment owns agents (non-goal) |
| Enforced sandbox orchestration | Advisory Boundaries + host native tools |
| Default-deny tool firewall | Host policy; not rebuilt here |
| Full Ed25519 receipt mesh / SLSA export | Start with local HMAC receipt; expand if needed |
