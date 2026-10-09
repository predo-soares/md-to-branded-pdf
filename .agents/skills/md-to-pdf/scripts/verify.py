#!/usr/bin/env python3
"""Inspect a PDF on demand and prepare every page for human visual review."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import fitz


PLACEHOLDER = re.compile(r"\{\{[^{}]{1,120}\}\}|\b(?:TODO|FIXME|TBD)\b", re.I)
CHECKLIST = """# PDF visual review checklist

Automated findings are in `verification.json`. They are diagnostic signals, not visual approval.

- [ ] Inspect every `page-NNN.png` in page order.
- [ ] Check title, headings, paragraphs, tables, figures, charts, and diagrams for clipping or overlap.
- [ ] Check page breaks, whitespace, margins, and reading order.
- [ ] Confirm that names, dates, claims, values, labels, and source links match the Markdown.
- [ ] Confirm that fonts, colors, and emphasis match the selected Template and design guide.
- [ ] Open the PDF and verify clickable links and any images at final viewing size.
- [ ] Record human approval or requested changes separately from this automated report.
"""


def inspect(pdf_path: Path, output_dir: Path, *, scale: float = 1.5) -> dict:
    if scale <= 0 or scale > 4:
        raise ValueError("Raster scale must be greater than 0 and at most 4")
    if not pdf_path.is_file():
        raise ValueError(f"PDF does not exist: {pdf_path}")
    output_dir.mkdir(parents=True, exist_ok=True)
    pages = []
    fonts = set()
    links = []
    placeholders = []
    geometry = []
    with fitz.open(pdf_path) as pdf:
        if len(pdf) == 0:
            raise ValueError("PDF has no pages")
        for index, page in enumerate(pdf, start=1):
            page_text = page.get_text()
            page_fonts = sorted({font[3] for font in page.get_fonts() if len(font) > 3})
            fonts.update(page_fonts)
            page_links = sorted({link["uri"] for link in page.get_links() if link.get("uri")})
            links.extend({"page": index, "uri": uri} for uri in page_links)
            for match in PLACEHOLDER.finditer(page_text):
                placeholders.append({"page": index, "text": match.group(0)})
            for block in page.get_text("blocks"):
                if len(block) > 6 and block[6] != 0:
                    continue
                rect = fitz.Rect(block[:4])
                if rect.is_empty:
                    continue
                if not page.rect.contains(rect):
                    geometry.append({"page": index, "type": "text_outside_page",
                                     "bbox": [round(v, 2) for v in rect]})
            image_name = f"page-{index:03d}.png"
            page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False).save(output_dir / image_name)
            pages.append({"number": index, "width_pt": round(page.rect.width, 2),
                          "height_pt": round(page.rect.height, 2),
                          "text_characters": len(page_text.strip()),
                          "has_text": bool(page_text.strip()),
                          "fonts": page_fonts, "links": page_links, "image": image_name})
    findings = []
    if any(not page["has_text"] for page in pages):
        findings.append("At least one page has no extractable text")
    if placeholders:
        findings.append("Placeholder-like text found")
    if geometry:
        findings.append("Text extends beyond a page boundary")
    report = {"pdf": str(pdf_path.resolve()), "page_count": len(pages),
              "pages_with_text": sum(page["has_text"] for page in pages),
              "text_coverage_ratio": round(sum(page["has_text"] for page in pages) / len(pages), 3),
              "pages": pages, "fonts": sorted(fonts), "links": links,
              "placeholders": placeholders, "geometry": geometry, "findings": findings,
              "visual_approval": "pending_human_review"}
    (output_dir / "verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                                                   encoding="utf-8")
    (output_dir / "review.md").write_text(CHECKLIST, encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--output", type=Path, required=True, help="Directory for JSON, page images, and review checklist")
    parser.add_argument("--scale", type=float, default=1.5, help="Page raster scale; default 1.5")
    args = parser.parse_args()
    try:
        report = inspect(args.pdf.resolve(), args.output.resolve(), scale=args.scale)
    except (ValueError, OSError, fitz.FileDataError) as error:
        parser.error(str(error))
    print(json.dumps({"page_count": report["page_count"], "pages_with_text": report["pages_with_text"],
                      "findings": report["findings"], "output": str(args.output.resolve())}, ensure_ascii=False))


if __name__ == "__main__":
    main()
