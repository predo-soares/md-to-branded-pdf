#!/usr/bin/env python3
"""Present validated normalized resume JSON with the canonical HTML template."""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path
from typing import Any

from md_to_pdf.content.parse_resume import validate_content


SKILL_DIR = Path(__file__).resolve().parents[3]
TEMPLATE = SKILL_DIR / "assets/templates/resume-ats.html"
GEIST = SKILL_DIR / "assets/geist-latin.woff2"
HEADINGS = {
    "pt-BR": ("Resumo", "Experiência Profissional", "Experiência Anterior", "Formação", "Idiomas", "Competências"),
    "en": ("Summary", "Professional Experience", "Earlier Experience", "Education", "Languages", "Skills"),
}


def inline_html(value: str) -> str:
    escaped = html.escape(value.strip(), quote=False)
    escaped = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r'<a href="\2">\1</a>', escaped)
    return re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)


def contact_html(contacts: list[dict[str, str]]) -> str:
    rendered = []
    for contact in contacts:
        text = html.escape(contact["text"], quote=False)
        href = contact.get("href")
        rendered.append(f'<a href="{html.escape(href, quote=True)}">{text}</a>' if href else text)
    return " · ".join(rendered)


def render_document(content: dict[str, Any]) -> str:
    validate_content(content)
    language = content["language"]
    summary_key, experience_key, earlier_key, education_key, languages_key, skills_key = HEADINGS[language]
    experience_html: list[str] = []
    for item in content["experience"]:
        bullets = "".join(f"<li>{inline_html(line)}</li>" for line in item["bullets"])
        if item["kind"] == "group":
            experience_html.append(
                f'<article class="job earlier-experience"><h3>{inline_html(item["title"])}</h3><ul>{bullets}</ul></article>'
            )
            continue
        description = item.get("description", "")
        description_html = f'<p class="company-description">{inline_html(description)}</p>' if description else ""
        title = f'{inline_html(item["company"])} — {inline_html(item["role"])}'
        experience_html.append(
            f'<article class="job"><div class="head"><h3>{title}</h3>'
            f'<p class="meta">{inline_html(item["datesLocation"])}</p></div>'
            f'{description_html}<ul>{bullets}</ul></article>'
        )
    identity = content["identity"]
    education = " ".join(inline_html(item) for item in content["education"])
    languages = " ".join(inline_html(item) for item in content["languages"])
    skills = "".join(f"<p>{inline_html(item)}</p>" for item in content["skills"])
    body = (
        f'<main class="page"><header class="identity"><h1>{inline_html(identity["name"])}</h1><div class="identity-details">'
        f'<p class="headline">{inline_html(identity["headline"])}</p><p class="contact">{contact_html(identity["contacts"])}</p></div></header>'
        f'<section class="summary-section"><h2>{summary_key}</h2><p class="summary">{inline_html(content["summary"])}</p></section>'
        f'<section class="experience-section"><h2>{experience_key}</h2>{"".join(experience_html)}</section>'
        f'<section><h2>{education_key}</h2><p>{education}</p></section>'
        f'<section><h2>{languages_key}</h2><p>{languages}</p></section>'
        f'<section><h2>{skills_key}</h2><div class="skills">{skills}</div></section></main>'
    )
    document = TEMPLATE.read_text(encoding="utf-8")
    substitutions = {
        "FONT_FACE": f'@font-face {{ font-family: "Geist"; src: url("{GEIST.as_uri()}") format("woff2"); font-weight: 100 900; }}',
        "LANG": html.escape(language, quote=True),
        "AUTHOR": html.escape(identity["name"], quote=True),
        "TITLE": html.escape(f'{identity["name"]} — {identity["headline"]}', quote=True),
        "BODY": body,
    }
    for key, value in substitutions.items():
        document = document.replace("{{" + key + "}}", value)
    return document


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("Usage: render_resume_html.py INPUT.content.json OUTPUT.html")
    source, destination = map(Path, sys.argv[1:])
    try:
        content = json.loads(source.read_text(encoding="utf-8"))
        document = render_document(content)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        raise SystemExit(str(error)) from error
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(document, encoding="utf-8")
    print(f"Rendered {destination} from validated {source}")


if __name__ == "__main__":
    main()
