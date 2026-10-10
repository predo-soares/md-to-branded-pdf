#!/usr/bin/env python3
"""Render a Markdown cover letter through saved HTML and WeasyPrint."""
from __future__ import annotations

import html
import os
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

import fitz

from md_to_pdf.rendering.render_html_pdf import _load_weasyprint
from md_to_pdf.visuals.palette import css_variables


TEMPLATE = Path(__file__).resolve().parents[3] / "assets/templates/cover-letter.html"


def read_letter(markdown: str) -> tuple[str, list[str], str, str]:
    blocks = [part.strip() for part in markdown.split("\n\n") if part.strip()]
    if not blocks or not blocks[0].lower().startswith("dear "):
        raise ValueError("Expected a cover letter beginning with a Dear salutation")
    if blocks[-1].lower().startswith("portfolio:"):
        blocks.pop()
    if len(blocks) < 4:
        raise ValueError("Cover letter is missing body or sign-off content")
    return blocks[0], blocks[1:-2], blocks[-2], blocks[-1]


def _paragraph(value: str) -> str:
    return html.escape(value).replace("\n", "<br>")


def _metadata() -> dict[str, str]:
    names = ("NAME", "LOCATION", "EMAIL", "WEBSITE", "RECIPIENT", "SUBJECT")
    values = {name: os.environ.get("CAREER_" + name, "").strip() for name in names}
    if not all(values.values()):
        raise ValueError("Set CAREER_NAME, CAREER_LOCATION, CAREER_EMAIL, CAREER_WEBSITE, CAREER_RECIPIENT, and CAREER_SUBJECT")
    if urlparse(values["WEBSITE"]).scheme not in {"http", "https"}:
        raise ValueError("CAREER_WEBSITE must be an HTTP or HTTPS URL")
    values["DATE"] = os.environ.get("CAREER_DATE", date.today().strftime("%B %d, %Y"))
    return values


def build(source: Path, html_output: Path, pdf_output: Path, *, markdown: str | None = None,
          title_override: str | None = None, language: str = "en",
          style_profile: dict[str, str] | None = None, style_override: bool = False,
          verified_image_hosts: set[str] | None = None) -> None:
    markdown = markdown if markdown is not None else source.read_text(encoding="utf-8")
    salutation, body, signoff, signature = read_letter(markdown)
    values = _metadata()
    email = html.escape(values["EMAIL"], quote=True)
    website = html.escape(values["WEBSITE"], quote=True)
    contact = (f'{html.escape(values["LOCATION"])} · <a href="mailto:{email}">{email}</a> · '
               f'<a href="{website}">{website}</a>')
    document = TEMPLATE.read_text(encoding="utf-8")
    body_markup = [f"<p>{_paragraph(paragraph)}</p>" for paragraph in body]
    fields = {
        "FONT_FACE": (f'@font-face {{ font-family: "Geist"; src: url("{(TEMPLATE.parent.parent / "geist-latin.woff2").as_uri()}") '
                      'format("woff2"); font-weight: 100 900; }'),
        "DESIGN_COLORS": css_variables(),
        "LANG": html.escape(language, quote=True),
        "TITLE": html.escape(title_override or f'Cover Letter — {values["SUBJECT"]}'),
        "NAME": html.escape(values["NAME"]),
        "CONTACT": contact,
        "DATE": html.escape(values["DATE"]),
        "RECIPIENT": _paragraph(values["RECIPIENT"]),
        "SUBJECT": html.escape(values["SUBJECT"]),
        "SALUTATION": _paragraph(salutation),
        "BODY": "".join(body_markup),
        "SIGNOFF": _paragraph(signoff),
        "SIGNATURE": _paragraph(signature),
    }
    for key, value in fields.items():
        document = document.replace("{{" + key + "}}", value)
    if style_override and style_profile:
        font = style_profile["font"]
        extra_css = ""
        if font.startswith("google:"):
            font = "GoogleSelectedFont"
            extra_css = style_profile["font_css"]
        elif font.startswith("fontsource:"):
            font = "FontsourceSelectedFont"
            extra_css = style_profile["font_css"]
        elif font not in {"system-ui", "Geist"}:
            path = Path(font)
            font = "UserSelectedFont"
            extra_css = f'@font-face {{ font-family: "{font}"; src: url("{path.as_uri()}"); }}'
        elif font == "Geist":
            path = Path(__file__).resolve().parents[3] / "assets/geist-latin.woff2"
            extra_css = f'@font-face {{ font-family: "Geist"; src: url("{path.as_uri()}") format("woff2"); }}'
        extra_css += (f'\n@page {{ background: {style_profile["paper"]}; }} '
                      f'body, main {{ background: {style_profile["paper"]}; }} '
                      f'body {{ font-family: "{font}", Arial, sans-serif; }} '
                      f'a {{ color: {style_profile["accent"]}; }}')
        document = document.replace("</style>", extra_css + "\n</style>")
    html_output.parent.mkdir(parents=True, exist_ok=True)
    html_output.write_text(document, encoding="utf-8")
    HTML = _load_weasyprint()
    rendered = HTML(filename=str(html_output), base_url=html_output.resolve().parent.as_uri()).render()
    if len(rendered.pages) != 1:
        marker = fields["BODY"]
        for index, paragraph in enumerate(body_markup):
            partial = document.replace(marker, "".join(body_markup[:index + 1]))
            if len(HTML(string=partial, base_url=html_output.resolve().parent.as_uri()).render().pages) > 1:
                offset = markdown.find(body[index])
                line = markdown[:offset].count("\n") + 1 if offset >= 0 else "unknown"
                raise ValueError(f"Cover-letter content overflows A4 at body paragraph on line {line}: {body[index][:70]}")
        raise ValueError("Cover-letter content overflows A4 at the closing block")
    pdf_output.parent.mkdir(parents=True, exist_ok=True)
    rendered.write_pdf(str(pdf_output))
    with fitz.open(pdf_output) as pdf:
        if abs(pdf[0].rect.width - 595.28) > 1 or abs(pdf[0].rect.height - 841.89) > 1:
            pdf_output.unlink(missing_ok=True)
            raise ValueError("Cover-letter content does not fit its one-page A4 layout")


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("Usage: render-cover-letter.py INPUT.md OUTPUT.pdf")
    source, pdf_output = map(Path, sys.argv[1:])
    try:
        build(source, pdf_output.with_suffix(".html"), pdf_output)
    except (OSError, ValueError) as error:
        raise SystemExit(str(error)) from error


if __name__ == "__main__":
    main()
