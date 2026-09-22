# Retornatus

<p align="center">
  <img src=".assets/retornatus-mascot.png" alt="Retornatus Seedcore mascot" width="280" />
</p>

<p align="center">
  <strong>Keep AI coding agents honest — with goals, memory, and proof.</strong><br />
  <em>Govern the work. Bound the agent. Verify the outcome.</em>
</p>

<p align="center">
  <a href="https://luizssantiago92.github.io/retornatus/"><strong>Website →</strong></a>
  ·
  <a href="https://luizssantiago92.github.io/retornatus/guide/">Docs</a>
  ·
  <a href="https://luizssantiago92.github.io/retornatus/guide/quick-start.html">Quick start</a>
  ·
  <a href="https://pypi.org/project/retornatus/">PyPI</a>
</p>

[![Website](https://img.shields.io/badge/website-live-14b8a6?style=flat)](https://luizssantiago92.github.io/retornatus/)
[![PyPI version](https://img.shields.io/pypi/v/retornatus.svg)](https://pypi.org/project/retornatus/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/luizssantiago92/retornatus/actions/workflows/ci.yml/badge.svg)](https://github.com/luizssantiago92/retornatus/actions/workflows/ci.yml)
[![license: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Retornatus is a **repo-native companion** for people who ship software with AI coding agents.
It helps you agree on what “done” means, keep that agreement in the project (not only in chat),
and require visible proof before work is closed.

| Without Retornatus | With Retornatus |
| --- | --- |
| The agent jumps to code and sounds finished | A clear finish line exists before the sprint |
| “Done” is a confident summary | “Done” needs evidence you can inspect |
| Each chat starts from zero | Project memory survives sessions and handoffs |
| Same chaos for a typo and a payment change | Ceremony scales with risk |
| Lessons vanish when the tab closes | The next return can learn from the last |

**Website:** [luizssantiago92.github.io/retornatus](https://luizssantiago92.github.io/retornatus/) · **Docs:** [guide hub](https://luizssantiago92.github.io/retornatus/guide/) · **Quick start:** [HTML](https://luizssantiago92.github.io/retornatus/guide/quick-start.html) · **PyPI:** [`retornatus`](https://pypi.org/project/retornatus/)

Markdown sources for deep guides still live under [docs/guide](docs/guide/README.md).

---

## Why use it

- **Stay in control** — the agent builds; you keep the bar for completion.
- **Stop losing context** — intent and progress live under `.retornatus/` in git.
- **Fewer false finishes** — gates and evidence make optimistic “done” expensive.
- **Specialize on demand** — research a skill for *this* problem instead of relying on stale packs.
- **Works where you already work** — Cursor, Claude Code, Codex, and similar hosts execute; Retornatus governs and records.

---

## Install

```bash
uv tool install retornatus
cd /path/to/your-app
retornatus init
retornatus integrate
retornatus doctor
```

Requires **Python 3.11+**. [`uv`](https://docs.astral.sh/uv/) is the recommended path; the package is also on [PyPI](https://pypi.org/project/retornatus/).

Then open the project in your AI coding agent. The hub skill teaches the loop; start with the [Quick start](https://luizssantiago92.github.io/retornatus/guide/quick-start.html).

---

## How it feels day to day

1. You describe what you want.
2. You agree on a clear finish line for that work.
3. Your AI coding agent builds under that agreement; you can check progress anytime.
4. Work closes when there is **proof you can inspect** — not when the model sounds confident.
5. What you learned stays in the project for the next return.

Deep mechanics (gates, skills lifecycle, policy) live in the [docs hub](https://luizssantiago92.github.io/retornatus/guide/).

---

## What’s new (1.1.x)

- **One-screen progress** — goals, proof, and next steps without digging through chat
- **Health at a glance** — process care vs hard stops
- **Lessons that stick** — failed checks can guide the next return
- **Light hygiene scans** — optional ops loops when you want a checkup
- **Seedcore** — brand mascot on the site and README

---

## Documentation

| Want… | Go here |
| --- | --- |
| Product story & install | [Website](https://luizssantiago92.github.io/retornatus/) |
| First change walkthrough | [Quick start (HTML)](https://luizssantiago92.github.io/retornatus/guide/quick-start.html) |
| Docs hub | [Guide hub](https://luizssantiago92.github.io/retornatus/guide/) |
| Concepts & pillars | [Overview](docs/guide/Overview.md) |
| Full guide index (markdown) | [docs/guide](docs/guide/README.md) |
| Product requirements | [PRD](prd/PRD.md) |
| Credits & lineage | [Credits](https://luizssantiago92.github.io/retornatus/credits.html) |

Technical depth (gates, lanes, skills lifecycle, CI templates, policy) lives in **documentation** — this README stays focused on positioning and getting started.

---

## License

MIT — see [LICENSE](LICENSE).

Brand mascot **Seedcore** is an original illustration for Retornatus. Not affiliated with Pokémon or Nintendo.
