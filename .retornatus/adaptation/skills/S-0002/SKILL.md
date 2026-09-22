---
name: website-development
id: S-0002
status: draft
description: >-
  Static product website for Retornatus (GitHub Pages under docs/). Structure,
  HTML/CSS, assets, and Pages workflow — not framework SPA work.
---

# Website development

Specialize when editing `docs/index.html`, `docs/site.css`, `docs/assets/`, or
GitHub Pages configuration for the product site.

## RESEARCH

- https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site — publish from `/docs` or Actions
- https://web.dev/articles/optimize-lcp — LCP image discoverable in HTML; avoid JS-only heroes
- https://web.dev/learn/performance/image-performance — size, format, width/height; do not lazy-load LCP
- https://web.dev/articles/fetch-priority — `fetchpriority="high"` on hero image
- https://developer.mozilla.org/en-US/docs/Web/HTML/Element/meta — description / OG basics for sharing

### Repo conventions

| Path | Role |
| --- | --- |
| `docs/index.html` | Landing (product story) |
| `docs/site.css` | Site styles |
| `docs/assets/` | Mascot and site images |
| `docs/guide/` | Technical documentation |
| `.github/workflows/pages.yml` | Pages deploy (if present) |

## PROCEDURE

1. Prefer **static HTML + one CSS file** — no build step unless already introduced.
2. Hero composition: brand, one headline, one lede, one CTA group, one mascot figure — no card clutter in the first viewport.
3. Mascot: PNG with **alpha**; page atmosphere provides the background; do not bake a solid plate into the asset.
4. Set explicit `width`/`height` on images; hero gets `fetchpriority="high"` and is **not** `loading="lazy"`.
5. Semantic landmarks: `header`, `main`, `section` with ids, `footer`; usable without JS.
6. Keep copy in English for shipped artifacts; match positioning from S-0001 when both apply (load only one skill per turn — prefer marketing for copy-only, this skill for structure/CSS/assets).
7. After visual changes: check ~360px and ~1100px widths; fix overlap and nav wrap.
8. Do not enable Pages publish as the agent (Tier 2 / owner) — prepare files; owner turns on Pages.
9. Evidence: local open of `docs/index.html` or Pages URL after owner deploy.

## Checks

- [ ] Valid HTML structure; relative links work on GitHub Pages base path
- [ ] Hero image has alpha; no white box against dark atmosphere
- [ ] CSS variables keep brand teal/amber consistent
- [ ] Guide links resolve under `docs/guide/`
