#!/usr/bin/env python3
"""Build styled HTML pages from docs markdown for GitHub Pages (stdlib only)."""

from __future__ import annotations

import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

PAGES: list[tuple[str, str]] = [
    ("guide/Overview.md", "guide/overview.html"),
    ("guide/Quick-start.md", "guide/quick-start.html"),
    ("guide/How-it-works.md", "guide/how-it-works.html"),
    ("guide/Concepts.md", "guide/concepts.html"),
    ("guide/Glossary.md", "guide/glossary.html"),
    ("guide/FAQ.md", "guide/faq.html"),
    ("guide/Skills.md", "guide/skills.html"),
    ("guide/Memory.md", "guide/memory.html"),
    ("guide/Governance.md", "guide/governance.html"),
    ("guide/Git-governance.md", "guide/git-governance.html"),
    ("guide/Gates.md", "guide/gates.html"),
    ("guide/CLI.md", "guide/cli.html"),
    ("guide/Architecture.md", "guide/architecture.html"),
    ("guide/Environments.md", "guide/environments.html"),
    ("guide/Non-goals.md", "guide/non-goals.html"),
    ("guide/From-spec-guardrails.md", "guide/from-spec-guardrails.html"),
    ("guide/Landscape.md", "guide/landscape.html"),
    ("guide/tutorials/README.md", "guide/tutorials/index.html"),
    ("guide/tutorials/01-first-change.md", "guide/tutorials/01-first-change.html"),
    ("guide/tutorials/02-brownfield-wake.md", "guide/tutorials/02-brownfield-wake.html"),
    ("credits-and-lineage.md", "credits.html"),
]

STEM_MAP = {
    "Overview": "overview.html",
    "Quick-start": "quick-start.html",
    "How-it-works": "how-it-works.html",
    "Concepts": "concepts.html",
    "Glossary": "glossary.html",
    "FAQ": "faq.html",
    "Skills": "skills.html",
    "Memory": "memory.html",
    "Governance": "governance.html",
    "Git-governance": "git-governance.html",
    "Gates": "gates.html",
    "CLI": "cli.html",
    "Architecture": "architecture.html",
    "Environments": "environments.html",
    "Non-goals": "non-goals.html",
    "From-spec-guardrails": "from-spec-guardrails.html",
    "Landscape": "landscape.html",
    "01-first-change": "01-first-change.html",
    "02-brownfield-wake": "02-brownfield-wake.html",
    "credits-and-lineage": "../credits.html",
    "README": "index.html",
}


def md_href_to_html(href: str, current_out: str) -> str:
    if href.startswith(("http://", "https://", "mailto:", "#")):
        return href
    if "prd/" in href or href.startswith("../../"):
        clean = re.sub(r"^(\.\./)+", "", href)
        return f"https://github.com/luizssantiago92/retornatus/blob/main/{clean}"
    frag = ""
    if "#" in href:
        href, frag = href.split("#", 1)
        frag = "#" + frag
    path = Path(href)
    stem = path.stem
    name = STEM_MAP.get(stem, stem.lower().replace("_", "-") + ".html")
    in_tutorials = "/tutorials/" in current_out.replace("\\", "/")
    at_root_docs = current_out.count("/") == 0  # e.g. credits.html

    if stem.startswith("0") or stem in ("01-first-change", "02-brownfield-wake"):
        target = STEM_MAP.get(stem, name)
        if at_root_docs:
            return f"guide/tutorials/{target}" + frag
        return (("" if in_tutorials else "tutorials/") + target) + frag
    if stem == "README" and "tutorial" in href.lower():
        if at_root_docs:
            return "guide/tutorials/" + frag
        return ("index.html" if in_tutorials else "tutorials/index.html") + frag
    if name.startswith("../"):
        return name + frag
    if at_root_docs and stem != "credits-and-lineage":
        return f"guide/{name}" + frag
    if in_tutorials and stem not in ("01-first-change", "02-brownfield-wake", "README"):
        return f"../{name}" + frag
    return name + frag


def rewrite_md_links(text: str, current_out: str) -> str:
    def repl(m: re.Match[str]) -> str:
        return f"]({md_href_to_html(m.group(1), current_out)})"

    return re.sub(r"\]\(([^)]+)\)", repl, text)


def inline_format(text: str) -> str:
    text = html.escape(text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", text)
    text = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        r'<a href="\2">\1</a>',
        text,
    )
    return text


def split_table_row(line: str) -> list[str]:
    """Split a markdown table row on |, ignoring pipes inside `code` and \\| escapes."""
    body = line.strip()
    if body.startswith("|"):
        body = body[1:]
    if body.endswith("|"):
        body = body[:-1]
    cells: list[str] = []
    buf: list[str] = []
    in_code = False
    i = 0
    while i < len(body):
        ch = body[i]
        if ch == "`":
            in_code = not in_code
            buf.append(ch)
            i += 1
            continue
        if not in_code and ch == "\\" and i + 1 < len(body) and body[i + 1] == "|":
            buf.append("|")
            i += 2
            continue
        if not in_code and ch == "|":
            cells.append("".join(buf).strip())
            buf = []
            i += 1
            continue
        buf.append(ch)
        i += 1
    cells.append("".join(buf).strip())
    return cells


def convert_markdown(md: str) -> str:
    lines = md.replace("\r\n", "\n").split("\n")
    out: list[str] = []
    i = 0
    in_code = False
    code_lang = ""
    code_buf: list[str] = []
    list_type: str | None = None

    def close_list() -> None:
        nonlocal list_type
        if list_type:
            out.append(f"</{list_type}>")
            list_type = None

    while i < len(lines):
        line = lines[i]
        if line.startswith("```"):
            if not in_code:
                close_list()
                in_code = True
                code_lang = line[3:].strip()
                code_buf = []
            else:
                lang_attr = f' class="language-{html.escape(code_lang)}"' if code_lang else ""
                body = html.escape("\n".join(code_buf))
                out.append(f'<pre class="code"><code{lang_attr}>{body}</code></pre>')
                in_code = False
            i += 1
            continue
        if in_code:
            code_buf.append(line)
            i += 1
            continue

        if line.strip() == "---":
            close_list()
            out.append("<hr />")
            i += 1
            continue

        # table
        if "|" in line and i + 1 < len(lines) and re.match(r"^\s*\|?\s*[-:| ]+\s*\|?\s*$", lines[i + 1]):
            close_list()
            rows = []
            while i < len(lines) and "|" in lines[i]:
                if re.match(r"^\s*\|?\s*[-:| ]+\s*\|?\s*$", lines[i]):
                    i += 1
                    continue
                cells = split_table_row(lines[i])
                rows.append(cells)
                i += 1
            if rows:
                out.append('<div class="doc-table-wrap"><table>')
                out.append("<thead><tr>" + "".join(f"<th>{inline_format(c)}</th>" for c in rows[0]) + "</tr></thead>")
                out.append("<tbody>")
                for row in rows[1:]:
                    out.append("<tr>" + "".join(f"<td>{inline_format(c)}</td>" for c in row) + "</tr>")
                out.append("</tbody></table></div>")
            continue

        m = re.match(r"^(#{1,4})\s+(.*)$", line)
        if m:
            close_list()
            level = len(m.group(1))
            out.append(f"<h{level}>{inline_format(m.group(2))}</h{level}>")
            i += 1
            continue

        m = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)$", line)
        if m:
            ordered = m.group(2)[-1] == "."
            tag = "ol" if ordered else "ul"
            if list_type != tag:
                close_list()
                list_type = tag
                out.append(f"<{tag}>")
            out.append(f"<li>{inline_format(m.group(3))}</li>")
            i += 1
            continue

        if not line.strip():
            close_list()
            i += 1
            continue

        close_list()
        out.append(f"<p>{inline_format(line)}</p>")
        i += 1

    close_list()
    return "\n".join(out)


def render_page(title: str, body_html: str, out_rel: str) -> str:
    depth = out_rel.count("/")
    prefix = "../" * depth
    css = f"{prefix}site.css"
    icon = f"{prefix}assets/retornatus-mascot.png"
    home = prefix if depth else "./"
    if out_rel.startswith("guide/tutorials/"):
        docs, qs = "../", "../quick-start.html"
    elif out_rel.startswith("guide/"):
        docs, qs = "./", "quick-start.html"
    else:
        docs, qs = "guide/", "guide/quick-start.html"

    safe_title = html.escape(title)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{safe_title} — Retornatus</title>
  <link rel="icon" type="image/png" href="{icon}" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="{css}" />
</head>
<body class="doc-page">
  <div class="atmosphere" aria-hidden="true"></div>
  <header class="top">
    <a class="brand" href="{home}">Retornatus</a>
    <nav>
      <a href="{home}">Site</a>
      <a href="{docs}">Docs</a>
      <a href="{qs}">Quick start</a>
      <a href="https://github.com/luizssantiago92/retornatus">GitHub</a>
    </nav>
  </header>
  <main class="doc-prose">
{body_html}
    <div class="doc-nav-secondary">
      <a class="btn ghost" href="{docs}">← Docs hub</a>
      <a class="btn primary" href="{home}">Product site →</a>
    </div>
  </main>
  <footer>
    <p>
      <strong>Retornatus</strong> —
      MIT ·
      <a href="https://github.com/luizssantiago92/retornatus">GitHub</a> ·
      <a href="{home}">Site</a> ·
      <a href="{docs}">Docs</a>
    </p>
  </footer>
</body>
</html>
"""


def extract_title(md: str, fallback: str) -> str:
    for line in md.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def render_one(src_rel: str, out_rel: str) -> str:
    src = DOCS / src_rel
    raw = src.read_text(encoding="utf-8")
    raw = rewrite_md_links(raw, out_rel)
    title = extract_title(raw, Path(out_rel).stem)
    body = convert_markdown(raw)
    return render_page(title, body, out_rel)


def build(*, check: bool = False) -> int:
    """Write HTML pages, or exit 1 when check=True and committed HTML is stale."""
    drift: list[str] = []
    for src_rel, out_rel in PAGES:
        src = DOCS / src_rel
        if not src.exists():
            print("skip missing", src)
            continue
        page = render_one(src_rel, out_rel)
        out = DOCS / out_rel
        if check:
            if not out.exists():
                drift.append(f"missing {out.relative_to(ROOT)}")
                continue
            current = out.read_text(encoding="utf-8")
            if current != page:
                drift.append(f"stale {out.relative_to(ROOT)}")
            else:
                print("ok", out.relative_to(ROOT))
            continue
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(page, encoding="utf-8", newline="\n")
        print("wrote", out.relative_to(ROOT))
    if check and drift:
        print("HTML out of sync with markdown sources:")
        for item in drift:
            print(" ", item)
        print("Fix: uv run python scripts/build_docs_html.py")
        return 1
    return 0


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit non-zero if generated HTML would differ from files on disk.",
    )
    args = parser.parse_args()
    sys.exit(build(check=args.check))
