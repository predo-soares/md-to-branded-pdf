#!/usr/bin/env python3
"""Build a PDF from Markdown using an explicitly selected project template."""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

import yaml
from google_fonts import resolve as resolve_google_font
from fontsource_fonts import resolve as resolve_fontsource_font
from style_profile import DEFAULT, FONTS, load as load_profile, onboard, validate as validate_profile

SCRIPTS = Path(__file__).resolve().parent
TEMPLATES = {"plain-document": "build-document.py", "proposal": "build-proposal.py",
             "resume": "build-resume.py", "cover-letter": "render-cover-letter.py",
             "one-pager": "build-one-pager.py", "long-document": "build-document.py",
             "portfolio": "build-document.py", "analytical-report": "build-document.py",
             "changelog": "build-document.py"}
LONG_DOCUMENT_CSS = SCRIPTS.parent / "assets/long-document.css"
PORTFOLIO_CSS = SCRIPTS.parent / "assets/portfolio.css"
REPORT_CSS = SCRIPTS.parent / "assets/report.css"
CHANGELOG_CSS = SCRIPTS.parent / "assets/changelog.css"


def load_builder(template: str):
    module_path = SCRIPTS / TEMPLATES[template]
    spec = importlib.util.spec_from_file_location(f"md_to_pdf_{template.replace('-', '_')}", module_path)
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
    parser.add_argument("--allow-font-download", action="store_true",
                        help="Explicitly allow a new Google Fonts or Fontsource download")
    parser.add_argument("--accent", help="Document accent color (#RRGGBB)")
    parser.add_argument("--paper", help="Document paper color (#RRGGBB)")
    parser.add_argument("--verified-image-host", action="append", default=[], metavar="HOST",
                        help="Official HTTPS host verified for remote Markdown images")
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
    language = metadata.get("lang", None if template == "resume" else
                            ("pt-BR" if template == "proposal" else "en"))
    if language is not None and not re.fullmatch(r"[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})*", language):
        parser.error(f"Invalid document language: {language}")
    hosts = {host.lower() for host in args.verified_image_host}
    if any(not re.fullmatch(r"[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+", host) for host in hosts):
        parser.error("--verified-image-host requires a hostname without a URL scheme or path")
    if template == "resume":
        if any(key in metadata for key in ("title", "font", "accent", "paper")) or any(
            value is not None for value in (args.font, args.accent, args.paper)
        ):
            parser.error("The approved résumé Template does not accept title or style overrides")
        try:
            load_builder(template)(source, html_output, pdf_output, markdown=markdown, language=language)
        except (ValueError, OSError) as error:
            parser.error(str(error))
        return
    try:
        style_profile = load_profile()
        saved_custom_profile = style_profile is not None and style_profile != DEFAULT
        if style_profile is None:
            style_profile = onboard() if sys.stdin.isatty() else DEFAULT.copy()
            saved_custom_profile = style_profile != DEFAULT
        style_profile.update({key: metadata[key] for key in ("font", "accent", "paper") if key in metadata})
        style_profile.update({key: value for key, value in
                              (("font", args.font), ("accent", args.accent), ("paper", args.paper))
                              if value is not None})
        if style_profile["font"] not in FONTS and not style_profile["font"].startswith(("google:", "fontsource:")):
            font_path = Path(style_profile["font"]).expanduser()
            if not font_path.is_absolute():
                font_path = ((Path.cwd() if args.font is not None else source.parent) / font_path).resolve()
            style_profile["font"] = str(font_path)
        validate_profile(style_profile)
        if style_profile["font"].startswith("google:"):
            family = style_profile["font"][7:]
            allow = args.allow_font_download
            from google_fonts import cache_root
            if not allow and sys.stdin.isatty():
                key = __import__("hashlib").sha256(family.casefold().encode()).hexdigest()[:16]
                if not (cache_root() / key / "manifest.json").exists():
                    allow = input(f"Download Google Fonts family '{family}' for this PDF? [y/N]: ").strip().lower() in {"y", "yes"}
            style_profile["font_css"] = resolve_google_font(family, allow_download=allow)
        elif style_profile["font"].startswith("fontsource:"):
            specifier = style_profile["font"][11:]
            try:
                style_profile["font_css"] = resolve_fontsource_font(specifier, allow_download=False)
            except PermissionError:
                allow = args.allow_font_download
                if not allow and sys.stdin.isatty():
                    allow = input(f"Download Fontsource family '{specifier}' for this PDF? [y/N]: ").strip().lower() in {"y", "yes"}
                style_profile["font_css"] = resolve_fontsource_font(specifier, allow_download=allow)
    except (ValueError, OSError, PermissionError) as error:
        parser.error(str(error))
    style_override = (saved_custom_profile or
                      any(key in metadata for key in ("font", "accent", "paper")) or
                      any(value is not None for value in (args.font, args.accent, args.paper)))
    try:
        options = ({"css_path": LONG_DOCUMENT_CSS, "figure_images": True} if template == "long-document" else
                   {"css_path": PORTFOLIO_CSS, "figure_images": True} if template == "portfolio" else
                   {"css_path": REPORT_CSS, "figure_images": True} if template == "analytical-report" else
                   {"css_path": CHANGELOG_CSS} if template == "changelog" else {})
        if template == "portfolio":
            from portfolio_content import parse as parse_portfolio
            content = parse_portfolio(markdown)
        elif template == "analytical-report":
            from report_content import parse as parse_report
            content = parse_report(markdown)
        elif template == "changelog":
            from changelog_content import parse as parse_changelog
            content = parse_changelog(markdown)
        load_builder(template)(source, html_output, pdf_output, markdown=markdown,
                               title_override=metadata.get("title"), language=language,
                               style_profile=style_profile, style_override=style_override,
                               verified_image_hosts=hosts, **options)
        if template in {"portfolio", "analytical-report", "changelog"}:
            json_output = html_output.with_suffix(".content.json")
            json_output.write_text(json.dumps(content, ensure_ascii=False, indent=2) + "\n",
                                   encoding="utf-8")
    except (ValueError, OSError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
