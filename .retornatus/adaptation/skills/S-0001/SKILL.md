---
name: product-marketing-site
id: S-0001
status: draft
description: >-
  Product marketing for Retornatus public surfaces — landing page and README
  positioning, benefits, install CTA, non-technical product story.
---

# Product marketing site

Specialize when rewriting `docs/index.html`, the root `README.md`, or other public
copy so visitors understand **what Retornatus does for them**, why to install, and
where technical depth lives (docs) — not in the hero.

## RESEARCH

Sources consulted (current public guidance):

- https://markcmo.com/magnet/website-landing-page-blueprint.html — hero = value prop + ICP in ~10s; one primary CTA; page architecture before decoration
- https://newsletter.buildingmomentum.io/p/customer-value-positioning-framework — outcomes → how product helps → headline/slogan; features support benefits
- https://peak-demand.com/2025/08/12/the-messaging-matrix-how-to-craft-positioning-that-connects/ — value prop → supporting benefits → proof → CTA; lead with value not features
- https://dev.to/prateekshaweb/designing-high-converting-landing-pages-for-single-product-stores-5230 — single-product flow: hero → benefits → proof → details → final CTA
- https://www.macrowebber.com/landing-page-optimization/ — message match, one dominant CTA, mobile-first clarity

### Positioning for Retornatus (derived)

| Layer | Message |
| --- | --- |
| Who | People who ship software with AI coding agents |
| Problem | Agents jump to code, declare “done,” and lose context when the chat ends |
| Outcome | Clear finish line, repo memory, proof before done |
| Frame | Repo-native companion that governs work; the agent still writes code |
| Primary CTA | Install (then Quick start) |
| Secondary | Docs / GitHub |

### README vs site vs docs

| Surface | Job |
| --- | --- |
| **Site** | Product story: why, how to use, install, what’s new, concept — minimal jargon |
| **README** | Positioning + install + links into docs; not a CLI encyclopedia |
| **docs/guide** | Technical depth: gates, lanes, skills, architecture, governance |

## PROCEDURE

1. State the **outcome** in the hero before any mechanism names (Contract, Evidence, etc.).
2. Keep brand name as the hero-level signal; one headline, one lede, one primary CTA.
3. Benefits section: user verbs (“stay in control”, “stop losing context”) — not internal artifact IDs.
4. “How you use it”: 4–6 human steps; point to guide for mechanics.
5. Install block: shortest path (`uv tool install` → `init` → `integrate` → `doctor`).
6. What’s new: user-visible capabilities; link releases/docs for changelogs.
7. README: slim comparison table + why + install + doc map; move CLI tables, gate matrices, and policy to `docs/guide/`.
8. Avoid inventing metrics or testimonials you do not have.
9. After copy edits: check mobile nav, CTA contrast, and that Docs is one click away.
10. Record Evidence as screenshot or URL of the updated page/README when closing the Action.

## Checks

- [ ] Hero understandable without knowing Demand/Contract vocabulary
- [ ] One primary CTA (Install); secondary is clearly subordinate
- [ ] Technical depth only via links to docs
- [ ] README does not duplicate the full guide
