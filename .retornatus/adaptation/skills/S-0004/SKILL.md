---
name: github-presence
id: S-0004
status: draft
description: >-
  GitHub repository presence for Retornatus — README positioning, About/homepage/topics,
  discoverability, and release/PR process habits. Use when improving how the project
  appears and is used on GitHub.
---

# GitHub presence (positioning + process)

Specialize when changing the public GitHub face of Retornatus: README, About box,
homepage URL, topics, badges, issue/PR hygiene, and how visitors find the website/docs.

## RESEARCH

Sources consulted:

- https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes — README should say why useful, what it does, how to start
- https://vitaecontext.github.io/playbooks/github/ — About as meta description; homepage URL; Quickstart near the top; front-load value
- https://github.com/mattinannt/repository-best-practices — description, topics, README as home page of the repo
- https://github.com/banesullivan/README — install must be audience-friendly; highlights early; avoid scaring users with contributor-only build steps first
- https://www.daytona.io/dotfiles/how-to-write-4000-stars-github-readme-for-your-project — value prop, quick start, hygiene (no broken links / empty sections)

### Retornatus defaults

| Surface | Job |
| --- | --- |
| **About description** | One line: companion that keeps AI coding agents honest with goals, memory, proof |
| **Homepage** | `https://luizssantiago92.github.io/retornatus/` |
| **README** | Positioning + what/why/how it proves + install explained + links to site docs |
| **Website** | Product story (non-jargon) + HTML docs (full reading, not raw `.md`) |
| **Markdown under `docs/guide/`** | Source of truth for technical depth; build HTML for Pages |

Suggested topics: `python`, `ai`, `governance`, `developer-tools`, `cursor`, `cli`, `uv`

## PROCEDURE

### Positioning (README / About)

1. Lead with **Website →** plus Docs / Quick start / PyPI — visitors must not hunt.
2. Sections in order: **What it is** → **What it does** → **How it proves** → **Install (explained)** → What’s new → Doc map.
3. Install steps name *who* runs them (your app repo vs this harness) and *what each command does*.
4. Prefer site HTML links for reading; keep relative markdown links for contributors editing sources.
5. Do not dump full CLI matrices in the README — link the docs hub.

### Process (how we use GitHub)

1. **Tier 0** local commit OK; **Tier 1** push/PR only when asked; **Tier 2** merge/publish/tag = owner only (see Git governance).
2. PR descriptions should cite Change id (`C-xxxx`) when dogfooding Retornatus.
3. After docs markdown changes, run `python scripts/build_docs_html.py` so Pages stays in sync.
4. Keep CI green before asking for merge; never `--no-verify` unless the human asks.
5. Homepage + topics: `gh repo edit --homepage URL` and set topics when metadata drifts.
6. Badges: Website, PyPI, CI, license — avoid redundant “docs” badges that hide the live site.

### Checks

- [ ] README answers what / why / how to install without opening another file
- [ ] Homepage URL set; Website link above the fold
- [ ] Docs and Quick start open as HTML on Pages (not raw markdown)
- [ ] No broken relative links in README table
- [ ] `build_docs_html.py` run after guide markdown edits
