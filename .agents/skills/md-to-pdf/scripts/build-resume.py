#!/usr/bin/env python3
"""Orchestrate Markdown → validated JSON → canonical HTML → PDF."""
from __future__ import annotations

import sys
from pathlib import Path

import fitz

from parse_resume import parse_markdown, write_json
from render_resume_html import render_document
from render_html_pdf import render_pdf


def build(source: Path, html_output: Path, pdf_output: Path, *, markdown: str | None = None,
          title_override: str | None = None, language: str | None = None,
          style_profile: dict[str, str] | None = None, style_override: bool = False,
          verified_image_hosts: set[str] | None = None) -> None:
    if title_override or style_override:
        raise ValueError("The approved résumé design does not accept title or style overrides")
    content = parse_markdown(source, markdown=markdown)
    if language and content["language"] != language:
        raise ValueError(f"Résumé language {content['language']} conflicts with frontmatter {language}")
    json_output = html_output.with_suffix(".content.json")
    write_json(content, json_output)
    html_output.parent.mkdir(parents=True, exist_ok=True)
    html_output.write_text(render_document(content), encoding="utf-8")
    render_pdf(html_output, pdf_output)
    with fitz.open(pdf_output) as pdf:
        if len(pdf) != 2 or any(abs(page.rect.width - 595.28) > 1 or
                                abs(page.rect.height - 841.89) > 1 for page in pdf):
            raise ValueError("Résumé content does not fit the approved two-page A4 layout")


def main() -> None:
    if len(sys.argv) != 4:
        raise SystemExit("Usage: build-resume.py INPUT.md OUTPUT.html OUTPUT.pdf")
    source, html_output, pdf_output = map(Path, sys.argv[1:])
    try:
        build(source, html_output, pdf_output)
    except (OSError, ValueError) as error:
        raise SystemExit(str(error)) from error
    json_output = html_output.with_suffix(".content.json")
    print(f"Built {json_output}, {html_output}, and {pdf_output} from the same Markdown source")


if __name__ == "__main__":
    main()
