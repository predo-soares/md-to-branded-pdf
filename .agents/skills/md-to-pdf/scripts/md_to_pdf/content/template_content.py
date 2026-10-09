"""Validate the content contract for every public PDF Template."""
from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator
from markdown_it import MarkdownIt


SCHEMAS = Path(__file__).resolve().parents[3] / "references/schemas"


def _headings(markdown: str) -> list[tuple[str, int, str]]:
    tokens = MarkdownIt("commonmark", {"html": False}).parse(markdown)
    return [(token.tag, token.map[0], tokens[index + 1].content.strip())
            for index, token in enumerate(tokens) if token.type == "heading_open"]


def _title(markdown: str, fallback: str | None = None,
           levels: tuple[str, ...] = ("h1",)) -> str:
    headings = _headings(markdown)
    if headings and headings[0][0] in levels and headings[0][2]:
        return headings[0][2]
    if fallback:
        return fallback
    raise ValueError("Template content must start with a # title")


def _sections(markdown: str, *, heading: str = "h2") -> list[dict[str, str]]:
    lines = markdown.splitlines()
    items = [item for item in _headings(markdown) if item[0] == heading]
    result = []
    for index, (_, start, name) in enumerate(items):
        end = items[index + 1][1] if index + 1 < len(items) else len(lines)
        result.append({"heading": name, "markdown": "\n".join(lines[start + 1:end]).strip()})
    return result


def _plain(markdown: str, fallback: str) -> dict:
    return {"title": _title(markdown, fallback), "markdown": markdown.strip()}


def _proposal(markdown: str) -> dict:
    sections = _sections(markdown)
    subtitle = None
    if sections and not sections[0]["heading"][:1].isdigit():
        subtitle = sections.pop(0)["heading"]
    content = {"title": _title(markdown), "sections": sections}
    if subtitle:
        content["subtitle"] = subtitle
    return content


def _cover_letter(markdown: str) -> dict:
    blocks = [part.strip() for part in markdown.split("\n\n") if part.strip()]
    if blocks and blocks[-1].lower().startswith("portfolio:"):
        blocks.pop()
    if len(blocks) < 4:
        raise ValueError("Cover-letter content needs a salutation, body, sign-off, and signature")
    return {"salutation": blocks[0], "paragraphs": blocks[1:-2],
            "signoff": blocks[-2], "signature": blocks[-1]}


def _one_pager(markdown: str) -> dict:
    tokens = MarkdownIt("commonmark", {"html": False}).parse(markdown)
    if len(tokens) < 4 or tokens[0].type != "heading_open" or tokens[0].tag != "h1" or tokens[3].type != "paragraph_open":
        raise ValueError("One-pager content needs a central-message paragraph immediately after its # title")
    first_paragraph = tokens[3]
    lines = markdown.splitlines()
    message = "\n".join(lines[first_paragraph.map[0]:first_paragraph.map[1]]).strip()
    return {"title": _title(markdown), "central_message": message, "sections": _sections(markdown)}


def _long_document(markdown: str) -> dict:
    return {"title": _title(markdown), "chapters": _sections(markdown)}


def _pitch_deck(markdown: str) -> dict:
    from md_to_pdf.content.deck_content import split_slides
    slides = split_slides(markdown)
    content = []
    for index, slide in enumerate(slides):
        title = _title(slide, levels=("h1", "h2"))
        layout = "cover" if index == 0 else "closing" if index == len(slides) - 1 else "assertion"
        if layout == "assertion" and title.lower().startswith("comparison:"):
            layout = "comparison"
        elif layout == "assertion" and title.lower().startswith("metrics:"):
            layout = "metrics"
        content.append({"layout": layout, "title": title, "markdown": slide})
    return {"slides": content}


def parse(template: str, markdown: str, fallback_title: str = "Document") -> dict:
    if template == "resume":
        from md_to_pdf.content.parse_resume import parse_markdown
        return parse_markdown(Path(fallback_title), markdown=markdown)
    if template == "portfolio":
        from md_to_pdf.content.portfolio_content import parse as parse_portfolio
        return parse_portfolio(markdown)
    if template == "analytical-report":
        from md_to_pdf.content.report_content import parse as parse_report
        return parse_report(markdown)
    if template == "changelog":
        from md_to_pdf.content.changelog_content import parse as parse_changelog
        return parse_changelog(markdown)
    parsers = {"plain-document": lambda: _plain(markdown, fallback_title),
               "proposal": lambda: _proposal(markdown),
               "cover-letter": lambda: _cover_letter(markdown),
               "one-pager": lambda: _one_pager(markdown),
               "long-document": lambda: _long_document(markdown),
               "pitch-deck": lambda: _pitch_deck(markdown)}
    if template not in parsers:
        raise ValueError(f"No content contract for Template: {template}")
    content = parsers[template]()
    schema = json.loads((SCHEMAS / f"{template}-content.schema.json").read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(content),
                    key=lambda error: list(map(str, error.absolute_path)))
    if errors:
        details = "; ".join(f"{'.'.join(map(str, error.absolute_path)) or '$'}: {error.message}"
                            for error in errors)
        raise ValueError(f"{template} validation failed: {details}")
    return content
