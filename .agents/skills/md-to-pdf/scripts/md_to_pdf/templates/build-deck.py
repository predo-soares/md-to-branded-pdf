"""Render a Markdown pitch deck as fixed-size 16:9 PDF slides."""
from __future__ import annotations

import html
import json
from pathlib import Path

from markdown_it import MarkdownIt

from md_to_pdf.visuals.charts import replace_chart_fences
from md_to_pdf.content.deck_content import split_slides
from md_to_pdf.visuals.diagrams import replace_diagram_fences
from md_to_pdf.rendering.media_validation import guarded_fetcher, validate_and_rewrite
from md_to_pdf.rendering.render_html_pdf import _load_weasyprint


CSS = Path(__file__).resolve().parents[3] / "assets/deck.css"
GEIST = Path(__file__).resolve().parents[3] / "assets/geist-latin.woff2"


def validate_structured_slide(tokens: list, layout: str, number: int) -> None:
    tables = [token for token in tokens if token.type == "table_open"]
    if len(tables) != 1:
        raise ValueError(f"Pitch deck slide {number} {layout} layout needs exactly one Markdown table")
    widths = []
    inside = False
    columns = 0
    for token in tokens:
        if token.type == "tr_open":
            inside = True
            columns = 0
        elif token.type in {"th_open", "td_open"} and inside:
            columns += 1
        elif token.type == "tr_close":
            widths.append(columns)
            inside = False
    expected = 3 if layout == "comparison" else 2
    if len(widths) < 2 or any(width != expected for width in widths):
        raise ValueError(f"Pitch deck slide {number} {layout} table needs {expected} columns and at least one data row")


def _groups(tokens: list) -> list[list]:
    groups = []
    current = []
    for token in tokens:
        current.append(token)
        if token.level == 0 and token.nesting <= 0:
            groups.append(current)
            current = []
    if current:
        groups.append(current)
    return groups


def build(source: Path, html_output: Path, pdf_output: Path, *, markdown: str | None = None,
          title_override: str | None = None, language: str = "en",
          style_profile: dict[str, str] | None = None, style_override: bool = False,
          verified_image_hosts: set[str] | None = None) -> None:
    markdown = markdown if markdown is not None else source.read_text(encoding="utf-8")
    slides = split_slides(markdown)
    parser = MarkdownIt("commonmark", {"breaks": True, "html": False}).enable("table")
    rendered = []
    metadata = []
    slide_tokens = []
    selected = (style_profile or {}).get("font", "Geist")
    svg_font = ("SelectedFont" if selected.startswith(("google:", "fontsource:")) else
                "UserSelectedFont" if selected not in {"Geist", "system-ui"} else selected)
    for index, slide in enumerate(slides):
        tokens = parser.parse(slide)
        headings = [tokens[position + 1].content.strip() for position, token in enumerate(tokens)
                    if token.type == "heading_open" and token.tag in {"h1", "h2"}]
        if not headings or not headings[0]:
            raise ValueError(f"Pitch deck slide {index + 1} needs a title heading")
        layout = "cover" if index == 0 else "closing" if index == len(slides) - 1 else "assertion"
        if layout == "assertion" and headings[0].lower().startswith("comparison:"):
            layout = "comparison"
        elif layout == "assertion" and headings[0].lower().startswith("metrics:"):
            layout = "metrics"
        if (layout == "cover" and not any(token.type == "heading_open" and token.tag == "h1"
                                          for token in tokens)):
            raise ValueError("Pitch deck cover needs a # title")
        if layout in {"comparison", "metrics"}:
            validate_structured_slide(tokens, layout, index + 1)
        validate_and_rewrite(tokens, source, verified_image_hosts or set())
        replace_chart_fences(tokens, svg_font)
        replace_diagram_fences(tokens, svg_font)
        slide_tokens.append(tokens)
        content = parser.renderer.render(tokens, parser.options, {})
        rendered.append(f'<section class="slide {layout}" data-slide="{index + 1}" data-layout="{layout}">{content}</section>')
        metadata.append({"number": index + 1, "layout": layout, "title": headings[0]})
    styles = CSS.read_text(encoding="utf-8")
    if style_profile:
        font = style_profile["font"]
        if font == "Geist":
            styles += f'\n@font-face {{ font-family: "Geist"; src: url("{GEIST.as_uri()}") format("woff2"); }}'
        elif font.startswith(("google:", "fontsource:")):
            font = "SelectedFont"
            styles += "\n" + style_profile["font_css"].replace("GoogleSelectedFont", font).replace("FontsourceSelectedFont", font)
        elif font != "system-ui":
            font_file = Path(font)
            font = "UserSelectedFont"
            styles += f'\n@font-face {{ font-family: "{font}"; src: url("{font_file.as_uri()}"); }}'
        styles += (f'\n:root {{ --font-body: "{font}", sans-serif; '
                   f'--accent: {style_profile["accent"]}; --paper: {style_profile["paper"]}; }}')
    title = title_override or metadata[0]["title"]
    def document_for(slide_html: str) -> str:
        return (f'<!doctype html><html lang="{html.escape(language, quote=True)}"><head>'
                f'<meta charset="utf-8"><title>{html.escape(title)}</title><style>{styles}</style>'
                f'</head><body>{slide_html}</body></html>')
    document = document_for("".join(rendered))
    html_output.parent.mkdir(parents=True, exist_ok=True)
    pdf_output.parent.mkdir(parents=True, exist_ok=True)
    html_output.write_text(document, encoding="utf-8")
    HTML = _load_weasyprint()
    result = HTML(filename=str(html_output), base_url=str(source.parent.resolve()),
                  url_fetcher=guarded_fetcher(verified_image_hosts or set())).render()
    if len(result.pages) != len(slides):
        pdf_output.unlink(missing_ok=True)
        cursor = 0
        for index, (slide, tokens) in enumerate(zip(slides, slide_tokens)):
            start = markdown.find(slide, cursor)
            cursor = start + len(slide)
            line_offset = markdown[:start].count("\n") if start >= 0 else 0
            layout = metadata[index]["layout"]
            prefix = []
            for group in _groups(tokens):
                prefix.extend(group)
                content = parser.renderer.render(prefix, parser.options, {})
                partial = document_for(f'<section class="slide {layout}">{content}</section>')
                pages = HTML(string=partial, base_url=str(source.parent.resolve()),
                             url_fetcher=guarded_fetcher(verified_image_hosts or set())).render().pages
                if len(pages) > 1:
                    first = group[0]
                    kind = first.type.removesuffix("_open")
                    line = line_offset + first.map[0] + 1 if first.map else "unknown"
                    excerpt = slide.splitlines()[first.map[0]][:70] if first.map else ""
                    raise ValueError(f"Pitch deck overflow on slide {index + 1} at {kind} on line {line}: {excerpt}")
        raise ValueError(f"Pitch deck overflow: {len(slides)} slides produced {len(result.pages)} pages")
    result.write_pdf(str(pdf_output))
    html_output.with_suffix(".slides.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
                                                     encoding="utf-8")
