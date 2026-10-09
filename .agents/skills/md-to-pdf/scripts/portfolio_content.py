"""Extract and validate authored case-study sections without inventing outcomes."""
from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator
from markdown_it import MarkdownIt


SCHEMA = Path(__file__).resolve().parents[1] / "references/schemas/portfolio-content.schema.json"
SECTION_NAMES = {"Context": "context", "Approach": "approach", "Outcome": "outcome"}


def parse(markdown: str) -> dict:
    lines = markdown.splitlines()
    tokens = MarkdownIt("commonmark", {"html": False}).parse(markdown)
    headings: list[tuple[int, int, str]] = []
    for index, token in enumerate(tokens):
        if token.type == "heading_open" and token.tag in {"h1", "h2", "h3"}:
            headings.append((int(token.tag[1]), token.map[0], tokens[index + 1].content.strip()))
    if not headings or headings[0][0] != 1 or not headings[0][2]:
        raise ValueError("Portfolio must start with a # title")
    title = headings[0][2]
    cases: list[dict[str, str]] = []
    for position, (level, line, name) in enumerate(headings):
        if level != 2:
            continue
        next_case = next((candidate[1] for candidate in headings[position + 1:] if candidate[0] <= 2), len(lines))
        child_headings = [(child_line, child_name) for child_level, child_line, child_name
                          in headings[position + 1:] if level < child_level and line < child_line < next_case]
        case: dict[str, str] = {"name": name}
        for child_index, (child_line, child_name) in enumerate(child_headings):
            key = SECTION_NAMES.get(child_name)
            if key is None:
                raise ValueError(f"Unsupported case-study section: {child_name}")
            if key in case:
                raise ValueError(f"Duplicate case-study section: {child_name}")
            end = child_headings[child_index + 1][0] if child_index + 1 < len(child_headings) else next_case
            case[key] = "\n".join(lines[child_line + 1:end]).strip()
        cases.append(case)
    content = {"title": title, "cases": cases}
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(content),
                    key=lambda error: list(map(str, error.absolute_path)))
    if errors:
        details = "; ".join(f"{'.'.join(map(str, error.absolute_path)) or '$'}: {error.message}"
                            for error in errors)
        raise ValueError(f"Portfolio content validation failed: {details}")
    return content
