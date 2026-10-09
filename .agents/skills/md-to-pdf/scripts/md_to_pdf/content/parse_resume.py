#!/usr/bin/env python3
"""Normalize an approved Resume Studio Markdown source into validated JSON."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Callable, Optional, Tuple, Union

from jsonschema import Draft202012Validator, FormatChecker


SKILL_DIR = Path(__file__).resolve().parents[3]
SCHEMA_PATH = SKILL_DIR / "references/schemas/resume-content.schema.json"
HEADINGS = {
    "pt-BR": ("Resumo", "Experiência Profissional", "Experiência Anterior", "Formação", "Idiomas", "Competências"),
    "en": ("Summary", "Professional Experience", "Earlier Experience", "Education", "Languages", "Skills"),
}


def _required_line(lines: list[str], predicate: Callable[[str], bool], label: str) -> Tuple[int, str]:
    for index, line in enumerate(lines):
        if predicate(line):
            return index, line
    raise ValueError(f"Markdown missing required {label}")


def _parse_contacts(lines: list[str]) -> list[dict[str, str]]:
    contacts: list[dict[str, str]] = []
    for line in lines:
        for segment in line.split(" · "):
            segment = segment.strip()
            if not segment:
                continue
            match = re.fullmatch(r"\[([^\]]+)\]\((https?://[^)]+)\)", segment)
            if match:
                # Resume design prints the URL itself, preserving the current approved output.
                contacts.append({"text": match.group(2), "href": match.group(2)})
            else:
                contacts.append({"text": segment})
    return contacts


def parse_markdown(source: Path, markdown: str | None = None) -> dict[str, Any]:
    lines = (markdown if markdown is not None else source.read_text(encoding="utf-8")).splitlines()
    _, name_line = _required_line(lines, lambda line: line.startswith("# "), "name (# Name)")
    name = name_line[2:].strip()
    headline_index, headline_line = _required_line(
        lines, lambda line: line.startswith("**") and line.count("**") >= 2, "bold headline"
    )
    headline = headline_line.strip().strip("*").strip()
    sections: dict[str, list[Union[str, Tuple[str, list[str]]]]] = {}
    section = ""
    job_title: Optional[str] = None
    job_lines: list[str] = []

    def flush_job() -> None:
        nonlocal job_title, job_lines
        if job_title is not None:
            sections.setdefault(section, []).append((job_title, job_lines))
        job_title, job_lines = None, []

    for line in lines:
        if line.startswith("## "):
            flush_job()
            section = line[3:].strip()
            sections.setdefault(section, [])
        elif line.startswith("### "):
            flush_job()
            job_title = line[4:].strip()
        elif job_title is not None and line.strip():
            job_lines.append(line.strip())
        elif section and line.strip() and line.strip() != "---":
            sections[section].append(line.strip())
    flush_job()

    language = "pt-BR" if "Resumo" in sections else "en"
    summary_key, experience_key, earlier_key, education_key, languages_key, skills_key = HEADINGS[language]
    contact_lines: list[str] = []
    for line in lines[headline_index + 1:]:
        if line.startswith("## "):
            break
        if line.strip():
            contact_lines.append(line.strip())
    experience: list[dict[str, Any]] = []
    for title, content in sections.get(experience_key, []):
        if not isinstance(title, str):
            continue
        bullets = [line[2:].strip() for line in content if line.startswith("- ")]
        if title == earlier_key:
            experience.append({"kind": "group", "title": title, "bullets": bullets})
            continue
        company, role = (title.split(" — ", 1) + [""])[:2]
        dates_location = content[0].strip().strip("*").strip() if content else ""
        description = content[1] if len(content) > 1 and not content[1].startswith("- ") else None
        item: dict[str, Any] = {
            "kind": "role", "company": company, "role": role,
            "datesLocation": dates_location, "bullets": bullets,
        }
        if description:
            item["description"] = description
        experience.append(item)

    content: dict[str, Any] = {
        "schemaVersion": 1,
        "language": language,
        "identity": {"name": name, "headline": headline, "contacts": _parse_contacts(contact_lines)},
        "summary": " ".join(str(item) for item in sections.get(summary_key, [])),
        "experience": experience,
        "education": [str(item) for item in sections.get(education_key, [])],
        "languages": [str(item) for item in sections.get(languages_key, [])],
        "skills": [str(item) for item in sections.get(skills_key, [])],
    }
    validate_content(content)
    return content


def validate_content(content: dict[str, Any]) -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(content), key=lambda error: list(map(str, error.absolute_path)))
    if errors:
        details = "; ".join(
            f"{'.'.join(map(str, error.absolute_path)) or '$'}: {error.message}" for error in errors
        )
        raise ValueError(f"Resume content validation failed: {details}")


def write_json(content: dict[str, Any], destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(content, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("Usage: parse_resume.py INPUT.md OUTPUT.content.json")
    source, destination = map(Path, sys.argv[1:])
    try:
        content = parse_markdown(source)
        write_json(content, destination)
    except (OSError, ValueError) as error:
        raise SystemExit(str(error)) from error
    print(f"Parsed and validated {source} → {destination}")


if __name__ == "__main__":
    main()
