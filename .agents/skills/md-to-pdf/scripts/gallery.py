#!/usr/bin/env python3
"""Build synthetic evidence for every Template; leave visual review to a person."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import fitz


ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "scripts/build.py"
VERIFY = ROOT / "scripts/verify.py"
EXAMPLES = ROOT / "references/examples"
A4 = (595.28, 841.89)
WIDE = (907.09, 510.24)
CASES = [
    ("plain-document", "plain-document.en.md", 1, A4),
    ("proposal", "proposal.pt-BR.md", 2, A4),
    ("resume", "resume.en.md", 2, A4),
    ("cover-letter", "cover-letter.en.md", 1, A4),
    ("one-pager", "one-pager.en.md", 1, A4),
    ("long-document", "long-document.en.md", 2, A4),
    ("portfolio", "portfolio.en.md", 1, A4),
    ("analytical-report", "analytical-report.en.md", 2, A4),
    ("changelog", "changelog.en.md", 1, A4),
    ("pitch-deck", "pitch-deck.en.md", 3, WIDE),
]
LETTER_FIELDS = {
    "CAREER_NAME": "Sample Person", "CAREER_LOCATION": "City, Country",
    "CAREER_EMAIL": "sample@example.com", "CAREER_WEBSITE": "https://example.com",
    "CAREER_RECIPIENT": "Hiring Team", "CAREER_SUBJECT": "Application for Sample Role",
    "CAREER_DATE": "October 9, 2026",
}


def generate(output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    environment = {**os.environ, **LETTER_FIELDS,
                   "XDG_CONFIG_HOME": str(output / ".gallery-config")}
    entries = []
    for template, fixture, expected_pages, expected_size in CASES:
        folder = output / template
        folder.mkdir(parents=True, exist_ok=True)
        html_path = folder / "document.html"
        pdf_path = folder / "document.pdf"
        review_path = folder / "review"
        entry = {"template": template, "fixture": str((EXAMPLES / fixture).relative_to(ROOT)),
                 "expected": {"pages": expected_pages, "width_pt": expected_size[0],
                              "height_pt": expected_size[1]},
                 "files": {"html": str(html_path.relative_to(output)),
                           "pdf": str(pdf_path.relative_to(output)),
                           "review": str(review_path.relative_to(output))},
                 "status": "pending"}
        entries.append(entry)
        build = subprocess.run(
            [sys.executable, str(BUILD), str(EXAMPLES / fixture), "--template", template,
             "--html", str(html_path), "--pdf", str(pdf_path)],
            capture_output=True, text=True, env=environment,
        )
        if build.returncode:
            entry.update(status="failed", step="build", error=build.stderr.strip())
            continue
        verify = subprocess.run([sys.executable, str(VERIFY), str(pdf_path),
                                 "--output", str(review_path)], capture_output=True, text=True,
                                env=environment)
        if verify.returncode:
            entry.update(status="failed", step="verify", error=verify.stderr.strip())
            continue
        with fitz.open(pdf_path) as pdf:
            actual = {"pages": len(pdf), "width_pt": round(pdf[0].rect.width, 2),
                      "height_pt": round(pdf[0].rect.height, 2)}
        entry["observed"] = actual
        if (actual["pages"] != expected_pages or
                abs(actual["width_pt"] - expected_size[0]) > 1 or
                abs(actual["height_pt"] - expected_size[1]) > 1):
            entry.update(status="failed", step="expected_geometry",
                         error=f"Expected {entry['expected']}, observed {actual}")
            continue
        entry.update(status="generated_for_human_review", visual_approval="pending_human_review")
        entry["files"]["page_images"] = [str((review_path / f"page-{index:03d}.png").relative_to(output))
                                          for index in range(1, actual["pages"] + 1)]
        entry["files"]["verification"] = str((review_path / "verification.json").relative_to(output))
        entry["files"]["checklist"] = str((review_path / "review.md").relative_to(output))
    manifest = {"visual_approval": "pending_human_review", "entries": entries}
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                                         encoding="utf-8")
    lines = ["# Synthetic PDF fixture gallery", "", "Generated evidence only. A person must review every page image and PDF.", ""]
    for entry in entries:
        lines.append(f"## {entry['template']}")
        lines.append("")
        lines.append(f"Fixture: `{entry['fixture']}`. Status: `{entry['status']}`.")
        lines.append("")
        if entry["status"] == "generated_for_human_review":
            files = entry["files"]
            lines.append(f"[HTML]({files['html']}) · [PDF]({files['pdf']}) · "
                         f"[Verification]({files['verification']}) · [Checklist]({files['checklist']})")
            lines.append("")
            lines.extend(f"![{entry['template']} page {index}]({image})" for index, image in
                         enumerate(files["page_images"], start=1))
        else:
            lines.append(f"Failed at `{entry['step']}`: {entry['error']}")
        lines.append("")
    (output / "index.md").write_text("\n".join(lines), encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path, help="Ignored local output directory")
    args = parser.parse_args()
    manifest = generate(args.output.resolve())
    failures = [entry for entry in manifest["entries"] if entry["status"] == "failed"]
    print(f"Generated {len(manifest['entries']) - len(failures)}/{len(manifest['entries'])} fixtures at {args.output.resolve()}")
    for entry in failures:
        print(f"FAILED {entry['template']} at {entry['step']}: {entry['error']}", file=sys.stderr)
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
