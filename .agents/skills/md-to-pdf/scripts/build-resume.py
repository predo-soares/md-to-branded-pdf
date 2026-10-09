#!/usr/bin/env python3
"""Orchestrate Markdown → validated JSON → canonical HTML → PDF."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from parse_resume import parse_markdown, write_json
from render_resume_html import render_document
from render_html_pdf import render_pdf


def main() -> None:
    if len(sys.argv) != 4:
        raise SystemExit("Usage: build-resume.py INPUT.md OUTPUT.html OUTPUT.pdf")
    source, html_output, pdf_output = map(Path, sys.argv[1:])
    json_output = html_output.with_suffix(".content.json")
    try:
        content = parse_markdown(source)
        write_json(content, json_output)
        html_output.parent.mkdir(parents=True, exist_ok=True)
        html_output.write_text(render_document(content), encoding="utf-8")
    except (OSError, ValueError) as error:
        raise SystemExit(str(error)) from error
    render_pdf(html_output, pdf_output)
    print(f"Built {json_output}, {html_output}, and {pdf_output} from the same Markdown source")


if __name__ == "__main__":
    main()
