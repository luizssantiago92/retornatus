"""Path glob matching for gates and structured policy.

``**`` crosses directories. A pattern without ``**`` still matches only the
path shape it spells (``*.pem`` matches ``a.pem``, not ``dir/a.pem``).
"""

from __future__ import annotations

import re


def normalize_repo_path(path: str) -> str:
    """Forward-slash path without a leading ``./``."""
    text = path.replace("\\", "/").strip()
    while text.startswith("./"):
        text = text[2:]
    return text


def glob_match(path: str, pattern: str) -> bool:
    """Return True when ``path`` matches ``pattern`` (both repo-relative)."""
    path_norm = normalize_repo_path(path)
    pattern_norm = normalize_repo_path(pattern)
    if not path_norm or not pattern_norm:
        return False
    return _compile(pattern_norm).fullmatch(path_norm) is not None


def _compile(pattern: str) -> re.Pattern[str]:
    parts: list[str] = ["^"]
    index = 0
    while index < len(pattern):
        if pattern.startswith("**/", index):
            parts.append("(?:.*/)?")
            index += 3
            continue
        if pattern.startswith("**", index):
            parts.append(".*")
            index += 2
            continue
        char = pattern[index]
        if char == "*":
            parts.append("[^/]*")
        elif char == "?":
            parts.append("[^/]")
        else:
            parts.append(re.escape(char))
        index += 1
    parts.append("$")
    return re.compile("".join(parts))
