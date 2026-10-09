#!/usr/bin/env python3
"""Render ordinary Markdown to a simple A4 HTML document and PDF."""
from __future__ import annotations

import argparse
import html
from pathlib import Path

from markdown_it import MarkdownIt

from render_html_pdf import _load_weasyprint


CSS = Path(__file__).resolve().parents[1] / "assets/plain-document.css"


def build(source: Path, html_output: Path, pdf_output: Path, *, markdown: str | None = None,
          title_override: str | None = None, language: str = "en") -> None:
    markdown = markdown if markdown is not None else source.read_text(encoding="utf-8")
    if not markdown.strip():
        raise ValueError("Markdown source is empty")
    title = title_override or next((line[2:].strip() for line in markdown.splitlines() if line.startswith("# ")), source.stem)
    body = MarkdownIt("commonmark", {"breaks": True}).enable("table").render(markdown)
    styles = CSS.read_text(encoding="utf-8")
    document = f'''<!doctype html>
<html lang="{html.escape(language, quote=True)}"><head><meta charset="utf-8"><title>{html.escape(title)}</title>
<style>{styles}</style></head><body>{body}</body></html>'''
    html_output.parent.mkdir(parents=True, exist_ok=True)
    pdf_output.parent.mkdir(parents=True, exist_ok=True)
    html_output.write_text(document, encoding="utf-8")
    HTML = _load_weasyprint()
    HTML(filename=str(html_output), base_url=str(source.parent.resolve())).write_pdf(str(pdf_output))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("markdown", type=Path)
    parser.add_argument("--html", required=True, type=Path)
    parser.add_argument("--pdf", required=True, type=Path)
    args = parser.parse_args()
    build(args.markdown.resolve(), args.html.resolve(), args.pdf.resolve())
