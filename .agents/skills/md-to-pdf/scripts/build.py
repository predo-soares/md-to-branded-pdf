#!/usr/bin/env python3
"""Build a PDF from Markdown using an explicitly selected project template."""
from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
TEMPLATES = {"plain-document": "build-document.py"}


def load_builder(template: str):
    module_path = SCRIPTS / TEMPLATES[template]
    spec = importlib.util.spec_from_file_location("md_to_pdf_plain_document", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load Template builder: {template}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.build


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("markdown", type=Path, help="Markdown source file")
    parser.add_argument("--template", required=True, choices=sorted(TEMPLATES))
    parser.add_argument("--html", required=True, type=Path, help="Saved HTML output")
    parser.add_argument("--pdf", required=True, type=Path, help="PDF output")
    args = parser.parse_args()

    source = args.markdown.resolve()
    html_output = args.html.resolve()
    pdf_output = args.pdf.resolve()
    if not source.is_file():
        parser.error(f"Markdown source does not exist: {source}")
    if html_output == pdf_output or source in (html_output, pdf_output):
        parser.error("Source, HTML output, and PDF output must be distinct files")
    load_builder(args.template)(source, html_output, pdf_output)


if __name__ == "__main__":
    main()
