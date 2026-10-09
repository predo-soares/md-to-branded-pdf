"""Validate the authored sections of a general analytical report."""
from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator
from markdown_it import MarkdownIt


SCHEMA = Path(__file__).resolve().parents[1] / "references/schemas/report-content.schema.json"
SECTIONS = {
    "Thesis": "thesis",
    "Evidence": "evidence",
    "Analysis": "analysis",
    "Risks": "risks",
    "Financial Context": "financial_context",
    "Conclusion": "conclusion",
}


def parse(markdown: str) -> dict[str, str]:
    lines = markdown.splitlines()
    tokens = MarkdownIt("commonmark", {"html": False}).parse(markdown)
    headings: list[tuple[str, int, str]] = []
    for index, token in enumerate(tokens):
        if token.type == "heading_open" and token.tag in {"h1", "h2"}:
            headings.append((token.tag, token.map[0], tokens[index + 1].content.strip()))
    if not headings or headings[0][0] != "h1" or not headings[0][2]:
        raise ValueError("Analytical report must start with a # title")
    content: dict[str, str] = {"title": headings[0][2]}
    order: list[str] = []
    for index, (level, line, name) in enumerate(headings[1:], start=1):
        if level != "h2":
            raise ValueError("Only the first heading may use # in an analytical report")
        key = SECTIONS.get(name)
        if key is None:
            raise ValueError(f"Unsupported analytical report section: {name}")
        if key in content:
            raise ValueError(f"Duplicate analytical report section: {name}")
        end = headings[index + 1][1] if index + 1 < len(headings) else len(lines)
        content[key] = "\n".join(lines[line + 1:end]).strip()
        order.append(key)
    expected = [key for key in ("thesis", "evidence", "analysis", "risks", "financial_context", "conclusion")
                if key in content]
    if order != expected:
        raise ValueError("Analytical report sections must follow Thesis, Evidence, Analysis, Risks, optional Financial Context, Conclusion")
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(content),
                    key=lambda error: list(map(str, error.absolute_path)))
    if errors:
        details = "; ".join(f"{'.'.join(map(str, error.absolute_path)) or '$'}: {error.message}"
                            for error in errors)
        raise ValueError(f"Analytical report validation failed: {details}")
    return content
