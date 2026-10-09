#!/usr/bin/env python3
"""Render a numbered Markdown proposal as A4 HTML and PDF."""
from __future__ import annotations

import argparse
import base64
import html
import os
import platform
import re
import tempfile
from pathlib import Path

from markdown_it import MarkdownIt


ROOT = Path(__file__).resolve().parents[1]
TOKENS = ROOT / "assets" / "tokens.css"
TEMPLATE = ROOT / "assets" / "document.html"
MARKDOWN = MarkdownIt("commonmark", {"breaks": True}).enable("table")


def tokens() -> dict[str, str]:
    return dict(re.findall(r"(--[\w-]+)\s*:\s*([^;]+);", TOKENS.read_text()))


def css() -> str:
    values = tokens()
    font_data = base64.b64encode((ROOT / "assets" / "geist-latin.woff2").read_bytes()).decode("ascii")
    style = f'@font-face {{ font-family: "Geist"; src: url(data:font/woff2;base64,{font_data}) format("woff2"); font-weight: 100 900; }}\n' + """
@page { size: A4; margin: var(--page-margin); background: var(--paper); }
* { box-sizing: border-box; }
html, body { margin: 0; color: var(--ink); background: var(--paper); }
body { font-family: var(--font-family); font-size: var(--font-size-body); line-height: var(--line-height-body); }
@media screen { body { max-width: 210mm; margin: auto; padding: var(--page-margin); } }
h1, h2, p { margin: 0; }
h1 { font-size: var(--font-size-title); line-height: 1.12; letter-spacing: var(--cover-title-letter-spacing); font-weight: 600; }
h2 { font-size: var(--font-size-section); line-height: 1.22; font-weight: 600; }
p { margin-bottom: var(--space-paragraph); }
.cover { height: 235mm; position: relative; break-after: page; }
.cover-top, .cover-bottom { display: flex; justify-content: space-between; color: var(--muted); font-size: var(--font-size-small); line-height: 1.5; }
.cover-author { text-align: right; }
.cover-inner { position: absolute; top: 100mm; left: 0; }
.cover-client { color: var(--muted); font-size: var(--font-size-small); margin-bottom: 13pt; }
.cover h1 { width: var(--cover-title-width); }
.cover-bottom { position: absolute; bottom: 0; left: 0; right: 0; }
main { display: block; }
.section { margin-bottom: var(--space-section); break-inside: avoid; }
.section.long { break-inside: auto; }
.internal .section { margin-bottom: 12pt; }
.internal .section-heading { margin-bottom: 7pt; }
.internal th, .internal td { padding-top: 3pt; padding-bottom: 3pt; }
.internal li { margin-bottom: 1pt; }
.section-heading { display: table; width: 100%; margin-bottom: 10pt; break-after: avoid; }
.section-number, .section-heading h2 { display: table-cell; vertical-align: top; }
.section-number { width: 28pt; color: var(--muted); font-size: var(--font-size-small); padding-top: 3pt; }
.section-body > :last-child { margin-bottom: 0; }
ol, ul { margin: 0 0 var(--space-paragraph); padding-left: 19pt; }
li { margin-bottom: 3pt; }
li p { margin-bottom: 0; }
table { width: 100%; border-collapse: collapse; margin-bottom: var(--space-paragraph); font-size: var(--font-size-body); line-height: 1.35; table-layout: fixed; }
th, td { text-align: left; vertical-align: top; padding: 5pt 8pt 5pt 0; }
th:first-child, td:first-child { font-weight: 600; }
.labeled-table th:first-child, .labeled-table td:first-child { width: 34%; }
.labeled-table td:first-child { white-space: nowrap; }
.labeled-table tr { break-inside: avoid; }
.investment-row td:last-child { white-space: nowrap; font-weight: 600; }
tr { break-inside: avoid; }
thead th { font-weight: 600; }
a { color: var(--ink); text-decoration: underline; }
pre { background: var(--soft); padding: 10pt; font-size: 10px; line-height: 1.4; white-space: pre-wrap; overflow-wrap: anywhere; }
code { font-size: 0.9em; overflow-wrap: anywhere; }
.document-intro { margin-bottom: 22pt; }
.investment-total { font-size: 23pt; font-weight: 700; white-space: nowrap; margin-bottom: 12pt; }
.investment-total span { font-size: var(--font-size-body); font-weight: 400; color: var(--muted); margin-left: 12pt; }
"""
    for key, value in sorted(values.items(), key=lambda item: -len(item[0])):
        style = style.replace(f"var({key})", value.strip())
    if "var(--" in style:
        raise ValueError("Token CSS não definido")
    return style


def parse(source: str) -> tuple[str, str, dict[str, str], str, list[tuple[int, str, str]]]:
    lines = source.splitlines()
    title = next((line[2:].strip() for line in lines if line.startswith("# ")), "Documento")
    first_heading = next((index for index, line in enumerate(lines) if line.startswith("# ")), -1)
    first_section = next((index for index, line in enumerate(lines) if line.startswith("## ")), len(lines))
    first_is_subtitle = (
        first_section < len(lines)
        and not re.match(r"^## \d+\.", lines[first_section])
        and not any(line.strip() for line in lines[first_heading + 1:first_section])
    )
    subtitle = lines[first_section][3:].strip() if first_is_subtitle else title
    meta: dict[str, str] = {}
    section_start = first_section + 1 if first_is_subtitle else first_section
    section_start = next((index for index in range(section_start, len(lines)) if lines[index].startswith("## ")), len(lines)) if first_is_subtitle else section_start
    preamble_lines = lines[first_heading + 1:section_start]
    if first_is_subtitle:
        preamble_lines = lines[first_section + 1:section_start]
    for line in preamble_lines:
        match = re.match(r"\*\*(.+?):\*\*\s*(.+?)\s*$", line)
        if match:
            meta[match.group(1)] = match.group(2)
    preamble = "\n".join(line for line in preamble_lines if not re.match(r"\*\*(.+?):\*\*", line)).strip()
    sections: list[tuple[int, str, str]] = []
    heading = None
    body: list[str] = []
    for line in lines[section_start:]:
        match = re.match(r"^## (?:(\d+)\.\s+)?(.+)$", line)
        if match:
            if heading:
                sections.append((*heading, "\n".join(body).strip()))
            heading = (int(match.group(1)) if match.group(1) else len(sections) + 1, match.group(2))
            body = []
        elif heading:
            body.append(line)
    if heading:
        sections.append((*heading, "\n".join(body).strip()))
    return title, subtitle, meta, preamble, sections


def labeled_table(headers: tuple[str, str], rows: list[tuple[str, str, str]]) -> str:
    head = ''.join(f'<th>{html.escape(label)}</th>' for label in headers)
    body = ''.join(
        f'<tr class="{row_class}"><td>{html.escape(label)}</td><td>{html.escape(description)}</td></tr>'
        for label, description, row_class in rows
    )
    return f'<table class="labeled-table"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>'


def render_section(number: int, title: str, body: str) -> str:
    if title == "Etapas de trabalho":
        rows = []
        for line in body.splitlines():
            match = re.match(r'^(\d+)\.\s+\*\*(.+?):\*\*\s*(.+)$', line)
            if match:
                rows.append((f'{match.group(1)}. {match.group(2)}', match.group(3), ''))
        content = labeled_table(('Etapa', 'Descrição'), rows) if rows else MARKDOWN.render(body)
    elif title == "Investimento e condições comerciais":
        rows = []
        for line in body.splitlines():
            match = re.match(r'^\*\*(.+?):\*\*\s*(.+?)\s*$', line)
            if match:
                label, description = match.groups()
                rows.append((label, description, 'investment-row' if label == 'Investimento total' else ''))
        content = labeled_table(('Condição', 'Descrição'), rows) if rows else MARKDOWN.render(body)
    else:
        content = MARKDOWN.render(body)
    kind = " long" if "<table" in content or "<pre" in content or len(body) > 1300 else ""
    return (f'<section class="section{kind}"><div class="section-heading">'
            f'<span class="section-number">{number:02d}</span><h2>{html.escape(title)}</h2></div>'
            f'<div class="section-body">{content}</div></section>')


def build(markdown_path: Path, html_path: Path, pdf_path: Path, *, kind: str | None = None,
          client: str | None = None, author: str | None = None, date: str | None = None,
          footer_left: str | None = None, footer_right: str | None = None) -> None:
    title, subtitle, meta, preamble, sections = parse(markdown_path.read_text(encoding="utf-8"))
    if not sections:
        raise ValueError("Nenhuma seção numerada encontrada")
    rendered_sections = "\n".join(render_section(*section) for section in sections)
    investment = re.search(r"\*\*Investimento total:\*\*\s*(R\$\s*[\d.,]+)", markdown_path.read_text(encoding="utf-8"))
    fields = {
        "body_class": "internal" if kind else "proposal",
        "document_kind": html.escape(kind or title),
        "document_title": html.escape(subtitle),
        "author": html.escape(author or meta.get("Proposta por", "")),
        "date": html.escape(date or meta.get("Data", "")),
        "client": html.escape(client or meta.get("Cliente", "")),
        "footer_left": html.escape(footer_left if footer_left is not None else ("Investimento: " + investment.group(1) if investment else "")),
        "footer_right": html.escape(footer_right if footer_right is not None else ("Validade: " + meta["Validade"] if "Validade" in meta else "")),
        "preamble": f'<div class="document-intro">{MARKDOWN.render(preamble)}</div>' if preamble else "",
        "styles": css(),
        "sections": rendered_sections,
    }
    document = TEMPLATE.read_text(encoding="utf-8")
    for key, value in fields.items():
        document = document.replace("{{" + key + "}}", value)
    html_path.parent.mkdir(parents=True, exist_ok=True)
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.write_text(document, encoding="utf-8")
    if platform.system() == "Darwin":
        import cffi
        os.environ.setdefault("XDG_CACHE_HOME", str(Path(tempfile.gettempdir()) / "md-to-pdf-font-cache"))
        names = {
            "libgobject-2.0-0": "libgobject-2.0.dylib",
            "libpango-1.0-0": "libpango-1.0.dylib",
            "libharfbuzz-0": "libharfbuzz.dylib",
            "libharfbuzz-subset-0": "libharfbuzz-subset.dylib",
            "libfontconfig-1": "libfontconfig.dylib",
            "libpangoft2-1.0-0": "libpangoft2-1.0.dylib",
        }
        original_dlopen = cffi.FFI.dlopen

        def homebrew_dlopen(self, name, flags=0):
            if name in names:
                for directory in (Path("/opt/homebrew/lib"), Path("/usr/local/lib")):
                    candidate = directory / names[name]
                    if candidate.exists():
                        return original_dlopen(self, str(candidate), flags)
            return original_dlopen(self, name, flags)

        cffi.FFI.dlopen = homebrew_dlopen
    from weasyprint import HTML
    HTML(string=document, base_url=str(markdown_path.parent)).write_pdf(str(pdf_path))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("markdown", type=Path)
    parser.add_argument("--html", required=True, type=Path)
    parser.add_argument("--pdf", required=True, type=Path)
    parser.add_argument("--kind")
    parser.add_argument("--client")
    parser.add_argument("--author")
    parser.add_argument("--date")
    parser.add_argument("--footer-left")
    parser.add_argument("--footer-right")
    args = parser.parse_args()
    build(args.markdown.resolve(), args.html.resolve(), args.pdf.resolve(), kind=args.kind,
          client=args.client, author=args.author, date=args.date,
          footer_left=args.footer_left, footer_right=args.footer_right)
