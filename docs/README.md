# Documentation

**Website:** [luizssantiago92.github.io/retornatus](https://luizssantiago92.github.io/retornatus/)

| Path | Audience |
| --- | --- |
| [`index.html`](index.html) | Public landing |
| [`guide/`](guide/index.html) | Docs hub (all pages on the site) |
| [`guide/*.html`](guide/index.html) | Full technical guides (built from markdown) |
| [`credits.html`](credits.html) | Credits & lineage (generated on Pages; not committed) |
| [guide/*.md](guide/README.md) | Markdown sources (edit these) |
| [`archive/PRD.md`](archive/PRD.md) | Product requirements |

GitHub Pages generates HTML from the markdown. To preview locally:

```bash
python scripts/build_docs_html.py
```

Do not commit that HTML.

Local preview: open [`index.html`](index.html) in a browser.
