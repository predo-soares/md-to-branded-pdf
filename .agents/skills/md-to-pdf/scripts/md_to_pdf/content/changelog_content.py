"""Validate versioned changelog structure while retaining authored order."""
from __future__ import annotations

import json
import re
from pathlib import Path

from jsonschema import Draft202012Validator
from markdown_it import MarkdownIt


SCHEMA = Path(__file__).resolve().parents[3] / "references/schemas/changelog-content.schema.json"
RELEASE = re.compile(r"^\[?(?P<version>(?:\d+\.\d+\.\d+|Unreleased))\]?\s*(?:[-—]\s*(?P<date>\d{4}-\d{2}-\d{2}))?$", re.I)


def parse(markdown: str) -> dict:
    lines = markdown.splitlines()
    tokens = MarkdownIt("commonmark", {"html": False}).parse(markdown)
    headings = [(token.tag, token.map[0], tokens[index + 1].content.strip())
                for index, token in enumerate(tokens)
                if token.type == "heading_open" and token.tag in {"h1", "h2", "h3"}]
    if not headings or headings[0][0] != "h1" or not headings[0][2]:
        raise ValueError("Changelog must start with a # title")
    content = {"title": headings[0][2], "releases": []}
    current = None
    for index, (level, line, name) in enumerate(headings[1:], start=1):
        end = headings[index + 1][1] if index + 1 < len(headings) else len(lines)
        body = "\n".join(lines[line + 1:end]).strip()
        if level == "h2":
            match = RELEASE.fullmatch(name)
            if not match:
                raise ValueError(f"Invalid changelog release heading: {name}")
            current = {"version": match.group("version"), "date": match.group("date"), "categories": []}
            content["releases"].append(current)
            if body:
                current["intro"] = body
        elif level == "h3":
            if current is None:
                raise ValueError("Changelog category must follow a release heading")
            if not body:
                raise ValueError(f"Changelog category has no entries: {name}")
            current["categories"].append({"name": name, "markdown": body})
        else:
            raise ValueError("Only the first heading may use # in a changelog")
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(content),
                    key=lambda error: list(map(str, error.absolute_path)))
    if errors:
        details = "; ".join(f"{'.'.join(map(str, error.absolute_path)) or '$'}: {error.message}"
                            for error in errors)
        raise ValueError(f"Changelog validation failed: {details}")
    return content
