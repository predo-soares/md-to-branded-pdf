"""Split top-level Markdown deck separators without splitting fenced code."""
from __future__ import annotations

from markdown_it import MarkdownIt


def split_slides(markdown: str) -> list[str]:
    parser = MarkdownIt("commonmark", {"html": False})
    lines = markdown.splitlines(keepends=True)
    boundaries = [token.map for token in parser.parse(markdown)
                  if token.type == "hr" and token.level == 0 and
                  "".join(lines[token.map[0]:token.map[1]]).strip() == "---"]
    slides = []
    start = 0
    for first, last in boundaries:
        slides.append("".join(lines[start:first]).strip())
        start = last
    slides.append("".join(lines[start:]).strip())
    if any(not slide for slide in slides):
        raise ValueError("Pitch deck has an empty slide around a --- separator")
    return slides
