#!/usr/bin/env python3
"""Build a PDF from Markdown using an explicitly selected project template."""
from __future__ import annotations

import argparse
import importlib.util
import re
import sys
from pathlib import Path

import yaml
from style_profile import DEFAULT, FONTS, load as load_profile, onboard, validate as validate_profile

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


def read_source(source: Path) -> tuple[str, dict[str, str]]:
    markdown = source.read_text(encoding="utf-8")
    if not markdown.startswith("---\n"):
        return markdown, {}
    lines = markdown.splitlines(keepends=True)
    closing = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if closing is None:
        raise ValueError("YAML frontmatter has no closing --- line")
    frontmatter = yaml.safe_load("".join(lines[1:closing])) or {}
    if not isinstance(frontmatter, dict):
        raise ValueError("YAML frontmatter must be a mapping")
    allowed = {"template", "lang", "title", "font", "accent", "paper"}
    unknown = set(frontmatter) - allowed
    if unknown:
        raise ValueError(f"Unsupported frontmatter fields: {', '.join(sorted(map(str, unknown)))}")
    if any(not isinstance(value, str) or not value.strip() for value in frontmatter.values()):
        raise ValueError("Frontmatter values must be non-empty strings")
    return "".join(lines[closing + 1:]), frontmatter


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("markdown", type=Path, help="Markdown source file")
    parser.add_argument("--template", choices=sorted(TEMPLATES))
    parser.add_argument("--font", help="Document font; overrides global profile")
    parser.add_argument("--accent", help="Document accent color (#RRGGBB)")
    parser.add_argument("--paper", help="Document paper color (#RRGGBB)")
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
    try:
        markdown, metadata = read_source(source)
    except (ValueError, yaml.YAMLError) as error:
        parser.error(str(error))
    metadata_template = metadata.get("template")
    if args.template and metadata_template and args.template != metadata_template:
        parser.error(f"Conflicting Template selections: --template={args.template} and frontmatter={metadata_template}")
    template = args.template or metadata_template
    if not template:
        parser.error("Choose a Template with --template or YAML frontmatter 'template'")
    if template not in TEMPLATES:
        parser.error(f"Unknown or unavailable Template: {template}")
    language = metadata.get("lang", "en")
    if not re.fullmatch(r"[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})*", language):
        parser.error(f"Invalid document language: {language}")
    try:
        style_profile = load_profile()
        if style_profile is None:
            style_profile = onboard() if sys.stdin.isatty() else DEFAULT.copy()
        style_profile.update({key: metadata[key] for key in ("font", "accent", "paper") if key in metadata})
        style_profile.update({key: value for key, value in
                              (("font", args.font), ("accent", args.accent), ("paper", args.paper))
                              if value is not None})
        if style_profile["font"] not in FONTS:
            font_path = Path(style_profile["font"]).expanduser()
            if not font_path.is_absolute():
                font_path = ((Path.cwd() if args.font is not None else source.parent) / font_path).resolve()
            style_profile["font"] = str(font_path)
        validate_profile(style_profile)
    except (ValueError, OSError) as error:
        parser.error(str(error))
    load_builder(template)(source, html_output, pdf_output, markdown=markdown,
                           title_override=metadata.get("title"), language=language,
                           style_profile=style_profile)


if __name__ == "__main__":
    main()
