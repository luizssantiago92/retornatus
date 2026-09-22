---
name: modern-web-methods
id: S-0003
status: draft
description: >-
  Modern static-web polish for the Retornatus landing — performance, motion
  (opt-in), accessibility, progressive enhancement. No SPA framework required.
---

# Modern web methods

Specialize when polishing motion, a11y, and performance on the static landing
without adding a heavy frontend toolchain.

## RESEARCH

- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@media/prefers-reduced-motion — system motion preference
- https://www.smashingmagazine.com/2021/10/respecting-users-motion-preferences/ — reduced-motion as default-safe practice
- https://www.cssshowcase.com/snippets/a11y/motion-safe-animation — prefer `@media (prefers-reduced-motion: no-preference)` so motion is opt-in
- https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Media_queries/Using_for_accessibility — a11y media queries
- https://web.dev/articles/optimize-lcp — holistic LCP (discovery, priority, render)
- https://web.dev/articles/serve-responsive-images — srcset/sizes when multiple assets exist

### Patterns for this site

1. **Motion opt-in** — put float/pulse animations inside `prefers-reduced-motion: no-preference`; leave opacity/color alone if useful.
2. **Progressive enhancement** — page fully readable with CSS disabled or no animation.
3. **Performance** — static HTML first paint; fonts with `preconnect`; avoid render-blocking JS; hero image prioritized.
4. **Mascot float** — CSS drop-shadow / soft glow behind the transparent PNG; page `.atmosphere` is the background, not a baked vignette.
5. **Focus** — visible `:focus-visible` on links/buttons; do not remove outlines without a replacement.

## PROCEDURE

1. Audit animations: spatial motion (translate/scale) gated; keep essential opacity fades optional.
2. Ensure contrast of body text and CTAs on the dark atmosphere (teal primary on dark ink).
3. Soften scroll (`scroll-behavior`) only when motion is allowed, or leave and accept OS preference via media query if needed.
4. Prefer CSS for mascot energy (glow layers) over animated GIFs.
5. Do not introduce a SPA, bundler, or client router for marketing pages unless a Contract explicitly requires it.
6. After changes: keyboard-tab through nav/CTAs; check with reduced-motion simulation if available.
7. Evidence: note a11y/perf checks run (manual is fine for this static page).

## Checks

- [ ] Animations disabled or minimal under `prefers-reduced-motion: reduce`
- [ ] No `loading="lazy"` on LCP/hero image
- [ ] Focus styles visible
- [ ] Page usable without JavaScript
