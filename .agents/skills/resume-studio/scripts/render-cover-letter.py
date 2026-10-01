#!/usr/bin/env python3
"""Render the project's Markdown cover-letter format to a one-page A4 PDF."""
from __future__ import annotations

import os
import sys
from datetime import date
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


def read_letter(path: Path) -> tuple[str, list[str], str, str]:
    blocks = [part.strip() for part in path.read_text(encoding="utf-8").split("\n\n") if part.strip()]
    if not blocks or not blocks[0].lower().startswith("dear "):
        raise ValueError("Expected a cover letter beginning with a Dear salutation.")
    salutation = blocks[0]
    if len(blocks) < 4:
        raise ValueError("Cover letter is missing body or sign-off content.")
    if blocks[-1].lower().startswith("portfolio:"):
        blocks.pop()
    if len(blocks) < 4:
        raise ValueError("Cover letter is missing body paragraphs.")
    signoff = blocks[-2]
    signature = blocks[-1]
    body = blocks[1:-2]
    return salutation, body, signoff, signature


def paragraph(text: str, style: ParagraphStyle) -> Paragraph:
    safe = escape(text).replace("\n", "<br/>")
    return Paragraph(safe, style)


def render(source: Path, destination: Path) -> None:
    salutation, body, signoff, signature = read_letter(source)
    name = os.environ.get("CAREER_NAME", "").strip()
    location = os.environ.get("CAREER_LOCATION", "").strip()
    email = os.environ.get("CAREER_EMAIL", "").strip()
    website = os.environ.get("CAREER_WEBSITE", "").strip()
    recipient = os.environ.get("CAREER_RECIPIENT", "").strip()
    subject = os.environ.get("CAREER_SUBJECT", "").strip()
    if not all((name, location, email, website, recipient, subject)):
        raise ValueError("Set CAREER_NAME, CAREER_LOCATION, CAREER_EMAIL, CAREER_WEBSITE, CAREER_RECIPIENT, and CAREER_SUBJECT before rendering.")
    application_date = os.environ.get("CAREER_DATE", date.today().strftime("%B %d, %Y"))
    destination.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(destination), pagesize=A4,
        leftMargin=20 * mm, rightMargin=20 * mm,
        topMargin=18 * mm, bottomMargin=18 * mm,
        title="Cover Letter",
        author=name,
    )
    base = getSampleStyleSheet()
    name_style = ParagraphStyle("Name", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=24, leading=28, textColor="#1c1c1c", spaceAfter=4)
    contact_style = ParagraphStyle("Contact", parent=base["Normal"], fontName="Helvetica", fontSize=9.5, leading=13, textColor="#444444", spaceAfter=0)
    date_style = ParagraphStyle("Date", parent=contact_style, alignment=TA_RIGHT, spaceBefore=14, spaceAfter=14)
    meta_style = ParagraphStyle("Meta", parent=contact_style, alignment=TA_LEFT, spaceAfter=12)
    subject_style = ParagraphStyle("Subject", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=10.5, leading=14, spaceAfter=12)
    body_style = ParagraphStyle("Body", parent=base["Normal"], fontName="Helvetica", fontSize=11, leading=16, textColor="#1c1c1c", spaceAfter=9, alignment=TA_LEFT, allowWidows=0, allowOrphans=0)
    closing_style = ParagraphStyle("Closing", parent=body_style, spaceBefore=5, spaceAfter=9)
    signature_style = ParagraphStyle("Signature", parent=body_style, fontName="Helvetica-Bold", spaceAfter=0)

    story = [
        Paragraph(escape(name), name_style),
        Paragraph(f'{escape(location)} · <link href="mailto:{escape(email)}" color="#444444">{escape(email)}</link> · <link href="{escape(website)}" color="#444444">{escape(website)}</link>', contact_style),
        Paragraph(escape(application_date), date_style),
        Paragraph(escape(recipient).replace("\n", "<br/>"), meta_style),
        Paragraph(escape(subject), subject_style),
        paragraph(salutation, body_style),
    ]
    story.extend(paragraph(text, body_style) for text in body)
    story.extend([paragraph(signoff, closing_style), paragraph(signature, signature_style)])
    doc.build(story)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: render-cover-letter.py INPUT.md OUTPUT.pdf")
    render(Path(sys.argv[1]), Path(sys.argv[2]))
