# Documentation

**Website:** [luizssantiago92.github.io/retornatus](https://luizssantiago92.github.io/retornatus/)

| Path | Audience |
| --- | --- |
| [`index.html`](index.html) | Public landing |
| [`guide/`](guide/index.html) | Docs hub (all pages on the site) |
| [`guide/*.html`](guide/index.html) | Full technical guides (built from markdown) |
| [`credits.html`](credits.html) | Credits & lineage |
| [guide/*.md](guide/README.md) | Markdown sources (edit these, then rebuild) |
| [`prd/PRD.md`](../prd/PRD.md) | Product requirements |

After editing any `docs/**/*.md` guide, regenerate HTML:

```bash
python scripts/build_docs_html.py
```

Local preview: open [`index.html`](index.html) in a browser.
