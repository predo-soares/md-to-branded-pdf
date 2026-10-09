#!/usr/bin/env python3
"""Render a flexible Markdown one-pager without changing layout to force fit."""
from __future__ import annotations

import html
from pathlib import Path

from markdown_it import MarkdownIt
from markdown_it.token import Token

from md_to_pdf.rendering.media_validation import guarded_fetcher, validate_and_rewrite
from md_to_pdf.rendering.render_html_pdf import _load_weasyprint


CSS = Path(__file__).resolve().parents[3] / "assets/one-pager.css"
GEIST = Path(__file__).resolve().parents[3] / "assets/geist-latin.woff2"


def _groups(tokens: list[Token]) -> list[list[Token]]:
    groups: list[list[Token]] = []
    current: list[Token] = []
    for token in tokens:
        current.append(token)
        if token.level == 0 and token.nesting <= 0:
            groups.append(current)
            current = []
    if current:
        groups.append(current)
    return groups


def _description(group: list[Token], markdown: str) -> str:
    first = group[0]
    line_number = first.map[0] + 1 if first.map else "unknown"
    excerpt = (markdown.splitlines()[line_number - 1] if isinstance(line_number, int) else "")[:70]
    kind = "heading" if first.type == "heading_open" else first.type.removesuffix("_open")
    return f"{kind} on line {line_number}: {excerpt}"


def _styles(profile: dict[str, str] | None) -> str:
    styles = CSS.read_text(encoding="utf-8")
    if not profile:
        return styles
    font = profile["font"]
    if font == "Geist":
        styles += f'\n@font-face {{ font-family: "Geist"; src: url("{GEIST.as_uri()}") format("woff2"); }}'
    elif font.startswith("google:"):
        font = "GoogleSelectedFont"
        styles += "\n" + profile["font_css"]
    elif font.startswith("fontsource:"):
        font = "FontsourceSelectedFont"
        styles += "\n" + profile["font_css"]
    elif font != "system-ui":
        path = Path(font)
        font = "UserSelectedFont"
        styles += f'\n@font-face {{ font-family: "{font}"; src: url("{path.as_uri()}"); }}'
    styles += (f'\n:root {{ --font-body: "{font}", Arial, sans-serif; '
               f'--accent: {profile["accent"]}; --paper: {profile["paper"]}; }}')
    return styles


def build(source: Path, html_output: Path, pdf_output: Path, *, markdown: str | None = None,
          title_override: str | None = None, language: str = "en",
          style_profile: dict[str, str] | None = None, style_override: bool = False,
          verified_image_hosts: set[str] | None = None) -> None:
    markdown = markdown if markdown is not None else source.read_text(encoding="utf-8")
    parser = MarkdownIt("commonmark", {"breaks": True, "html": False}).enable("table")
    tokens = parser.parse(markdown)
    groups = _groups(tokens)
    if not groups or groups[0][0].type != "heading_open" or groups[0][0].tag != "h1":
        raise ValueError("One-pager must start with a # title")
    if len(groups) < 2 or groups[1][0].type != "paragraph_open":
        raise ValueError("One-pager needs a central message paragraph immediately after the title")
    hosts = verified_image_hosts or set()
    validate_and_rewrite(tokens, source, hosts)
    styles = _styles(style_profile)
    title = title_override or groups[0][1].content
    def document(body: str) -> str:
        return (f'<!doctype html><html lang="{html.escape(language, quote=True)}"><head>'
                f'<meta charset="utf-8"><title>{html.escape(title)}</title><style>{styles}</style>'
                f'</head><body><main>{body}</main></body></html>')
    body = parser.renderer.render(tokens, parser.options, {})
    html_output.parent.mkdir(parents=True, exist_ok=True)
    pdf_output.parent.mkdir(parents=True, exist_ok=True)
    html_output.write_text(document(body), encoding="utf-8")
    HTML = _load_weasyprint()
    pdf = HTML(filename=str(html_output), base_url=str(source.parent.resolve()),
               url_fetcher=guarded_fetcher(hosts)).render()
    if len(pdf.pages) != 1:
        prefix: list[Token] = []
        for group in groups:
            prefix.extend(group)
            partial = parser.renderer.render(prefix, parser.options, {})
            pages = HTML(string=document(partial), base_url=str(source.parent.resolve()),
                         url_fetcher=guarded_fetcher(hosts)).render().pages
            if len(pages) > 1:
                raise ValueError(f"One-pager content overflows A4 at {_description(group, markdown)}")
        raise ValueError("One-pager content overflows A4")
    pdf.write_pdf(str(pdf_output))
