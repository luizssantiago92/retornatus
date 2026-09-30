"""README links must resolve on PyPI, where relative paths do not."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"

_FENCE = re.compile(r"^```.*?^```", re.DOTALL | re.MULTILINE)
_INLINE_CODE = re.compile(r"`[^`\n]+`")
_HTML_REF = re.compile(r"""(?:href|src)\s*=\s*["']([^"']+)["']""", re.IGNORECASE)
_REF_DEF = re.compile(r"^\s*\[[^\]]+\]:\s+(\S+)", re.MULTILINE)
_BLOB = "https://github.com/luizssantiago92/retornatus/blob/main/"
_RAW = "https://raw.githubusercontent.com/luizssantiago92/retornatus/main/"


def _destination(raw: str) -> str:
    target = raw.strip()
    if target.startswith("<") and ">" in target:
        target = target[1 : target.index(">")]
    return target.split()[0] if target else target


def _allowed(url: str) -> bool:
    return url.startswith(("#", "https://", "http://", "mailto:"))


def _markdown_destinations(text: str) -> list[str]:
    """Link and image destinations, including nested badge links."""
    found: list[str] = []
    index = 0
    while True:
        start = text.find("](", index)
        if start < 0:
            break
        cursor = start + 2
        if cursor < len(text) and text[cursor] == "<":
            end = text.find(">", cursor)
            if end < 0:
                break
            found.append(text[cursor : end + 1])
            close = text.find(")", end)
            index = close + 1 if close >= 0 else end + 1
            continue
        end = text.find(")", cursor)
        if end < 0:
            break
        found.append(text[cursor:end])
        index = end + 1
    return found


def relative_non_anchor_links(markdown: str) -> list[str]:
    """Return README destinations that are neither absolute nor in-page anchors."""
    visible = _INLINE_CODE.sub("", _FENCE.sub("", markdown))
    raw_urls = (
        _markdown_destinations(visible)
        + [match.group(1) for match in _HTML_REF.finditer(visible)]
        + [match.group(1) for match in _REF_DEF.finditer(visible)]
    )
    relative: list[str] = []
    for raw in raw_urls:
        url = _destination(raw)
        if url and not _allowed(url):
            relative.append(url)
    return relative


def test_readme_has_no_relative_non_anchor_links() -> None:
    text = README.read_text(encoding="utf-8")
    assert relative_non_anchor_links(text) == []
    assert f'src="{_RAW}docs/assets/retornatus-mascot-readme.webp"' in text
    assert f"]({_BLOB}LICENSE)" in text
    assert f"]({_BLOB}CONTRIBUTING.md#releases)" in text
    assert f"]({_BLOB}templates/ci/retornatus-pr.yml)" in text
    assert f"]({_BLOB}docs/guide/Presets.md)" in text
    assert "](#what-it-is)" in text


def test_relative_non_anchor_link_is_detected() -> None:
    sample = "\n".join(
        [
            "[section](#install)",
            "[site](https://example.com/docs)",
            "[mail](mailto:hi@example.com)",
            "[license](LICENSE)",
            "[guide](docs/guide/Presets.md)",
            '<img src="docs/assets/mascot.webp" />',
            "```",
            "[ignored](relative/inside/fence.md)",
            "```",
            "Inline `[code](not-a-link.md)` stays ignored.",
        ]
    )
    assert relative_non_anchor_links(sample) == [
        "LICENSE",
        "docs/guide/Presets.md",
        "docs/assets/mascot.webp",
    ]
