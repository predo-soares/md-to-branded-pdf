---
name: resume-studio
description: "Create, edit, and preview project-local resumes and cover letters from approved Markdown sources. Use for career-document structure, visual layout, HTML previews, and PDF exports."
---

# Resume Studio

Create application-ready resumes and cover letters from the project's approved Markdown files. Source Markdown remains the factual authority; never add metrics, dates, ownership, or credentials that it does not support.

## Working files

- Master sources: approved English and Portuguese résumé files at the workspace root (private inputs; excluded from Git).
- Résumés tailored to a specific role: `resumes/targeted/*.md`.
- Editable résumé template: `assets/templates/resume-ats.html`.
- Cover-letter template: `assets/templates/cover-letter.html`.
- Legacy two-column résumé template: `assets/legacy/resume-two-column.html` (archived; not used for new documents).
- Content contract: `references/schemas/resume-content.schema.json` (JSON Schema Draft 2020-12).
- Python dependencies: `requirements.txt` (`jsonschema` validation and WeasyPrint rendering).
- Output: save preview HTML and exports in `output/resume-studio/`.
- Cover-letter PDF renderer: `scripts/render-cover-letter.py` (ReportLab).
- Résumé pipeline: `scripts/build-resume.py` orchestrates Markdown → validated JSON → canonical HTML → PDF; `scripts/parse_resume.py` parses and validates content; `scripts/render_resume_html.py` presents validated JSON using the canonical template.
- HTML-to-PDF renderer: `scripts/render_html_pdf.py` (WeasyPrint and local Pango libraries on macOS).

## Locked résumé design

The approved two-page layout is the immutable default for every résumé. Keep its exact visual system and page structure: identity with name on the left and title/contact on the right; uppercase section labels; compact single-column experience; each company and role on one line with dates/location aligned right; company description directly below that line; summary, experience, education, languages, and skills last. Change résumé content only. Never alter the layout, typography, spacing, hierarchy, header, or pagination. `assets/templates/resume-ats.html` is the canonical template and must match this approved design. Any local reference PDF is private and excluded from Git.

## Workflow

1. Read the matching master résumé as the factual source. Save each role-tailored résumé as a Markdown file in `resumes/targeted/`, preserving supported facts. For cover letters, preserve the approved letter copy and use the project cover-letter template.
2. Build from `assets/templates/resume-ats.html`, the only canonical résumé visual template. The builder parses the approved Markdown into `OUTPUT.content.json`, validates it against the schema, then saves `OUTPUT.html` and renders `OUTPUT.pdf` from that same HTML. The Markdown remains the factual source; JSON is a generated intermediate, not an editorial source. Preserve the approved design. The template is an ATS-first, single-column résumé with no sidebar, cards, icons, text boxes, or visual-only content.
3. For visual changes, edit the canonical template CSS, rebuild both outputs, and inspect the generated HTML and every PDF page. Never add a second layout implementation for the PDF.
4. Keep the information hierarchy: identity and contact first, summary second, experience in reverse chronology, then education, languages, and finally skills. Group early short roles only when every role, employer, and date stays visible. Never use a two-column layout for résumés unless the user explicitly requests it.
5. When generating or adapting Markdown resumes, always place `Skills` / `Competências` as the final section. The standard order is: identity and contact, summary, professional experience, education, languages, then skills. Do not place skills between the summary and experience unless the user explicitly requests a different order.
6. Export HTML and PDF when asked. Verify that every intended position appears and that no section splits awkwardly across pages. For cover letters, keep the letter to one page and inspect the rendered page image.

## PDF rendering contract

Use project-owned templates and renderers. Do not invoke Kami or use its templates, styling, or scripts. For résumés, run `python3 .agents/skills/resume-studio/scripts/build-resume.py INPUT.md OUTPUT.html OUTPUT.pdf` from the project root. The builder creates `OUTPUT.content.json`, then `OUTPUT.html`, and uses WeasyPrint to print that exact HTML file to `OUTPUT.pdf`; ReportLab is not used for résumés. Install Python packages with `python3 -m pip install -r .agents/skills/resume-studio/requirements.txt`; WeasyPrint's native Pango libraries must also be available on macOS. For cover letters, the current separate workflow still uses `scripts/render-cover-letter.py` (ReportLab). Set `CAREER_NAME`, `CAREER_LOCATION`, `CAREER_EMAIL`, `CAREER_WEBSITE`, `CAREER_RECIPIENT`, and `CAREER_SUBJECT` in the local environment before running it; optionally set `CAREER_DATE` to override today's date. Keep personal values out of scripts and tracked files. Inspect every résumé PDF page as an image, confirm the page count, text, and that company/role/date lines stay on one line, then report the result.

## Markdown-to-content mapping

- `# Name` becomes `identity.name`; the bold line immediately after it becomes `identity.headline`.
- Contact lines below the headline are split on ` · `. Markdown links become contact objects with `text` set to the visible URL (matching the approved résumé) and `href` set to the same URL; plain text remains plain text.
- `## Summary` / `## Resumo` becomes `summary`, preserving the paragraph text.
- Each `### Company — Role` under the professional-experience section becomes an ordered `kind: "role"` entry. Its first following line is `datesLocation`, the next non-bullet line is optional `description`, and `- ` lines become `bullets`.
- `### Earlier Experience` / `### Experiência Anterior` becomes a `kind: "group"` entry; its bullets remain in source order.
- Education, languages, and skills section lines become ordered arrays of strings, preserving inline Markdown such as bold labels for the HTML presenter.
- `language` is selected from the Portuguese section headings; otherwise the parser expects the English heading set. Missing required content or malformed experience entries fail schema validation before HTML is written.

## Preview

Open the generated HTML in a Codex browser panel. The browser preview is the shared visual review surface; do not treat text-only or PDF extraction checks as visual approval.

Legacy previews in `output/resume-studio/` may include custom controls and per-role builders. They are not part of the canonical résumé build. The final HTML and PDF must contain resolved CSS values and no control-panel dependency.
