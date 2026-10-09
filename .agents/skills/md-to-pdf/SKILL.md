---
name: md-to-pdf
description: Create PDFs from Markdown using a context-appropriate project template. Use for résumés, cover letters, proposals, and other Markdown documents requiring PDF output.
---

# Markdown to PDF

Choose the template from the user's request, source content, and project context. An explicit user choice takes precedence over inference. When multiple templates plausibly fit and the user has not chosen, ask the user which one to use before rendering. If no template fits, ask whether to adapt one or create a reusable new template. Do not silently force an ambiguous document into the proposal layout. See `references/template-routing.md` for selection examples.

## Template routing

| Context | Template | Command |
| --- | --- | --- |
| Résumé or CV | Approved ATS résumé | `python3 .agents/skills/md-to-pdf/scripts/build.py INPUT.md --template resume --html OUTPUT.html --pdf OUTPUT.pdf` |
| Commercial proposal or similar numbered document | Proposal cover and sections | `python3 .agents/skills/md-to-pdf/scripts/build.py INPUT.md --template proposal --html OUTPUT.html --pdf OUTPUT.pdf` |
| Application cover letter | Current letter renderer | `python3 .agents/skills/md-to-pdf/scripts/render-cover-letter.py INPUT.md OUTPUT.pdf` |
| Ordinary Markdown document | Plain A4 document | `python3 .agents/skills/md-to-pdf/scripts/build.py INPUT.md --template plain-document --html OUTPUT.html --pdf OUTPUT.pdf` |

The proposal renderer requires at least one `##` section. Its `assets/document.html` and `assets/tokens.css` control the layout. The first unnumbered `##` immediately after the `#` title is a cover subtitle. Later `##` headings become numbered sections. Proposal-specific investment and work-stage tables render when those headings are present. The standalone `build-proposal.py` command still supports `--kind`, `--client`, `--author`, `--date`, `--footer-left`, and `--footer-right`. Do not use this layout as a generic default.

The unified `scripts/build.py` command currently supports `plain-document`, `proposal`, and `resume`; other existing renderers will join it as their Templates are migrated. Direct builds require `--template` or YAML frontmatter `template`. Matching declarations are accepted; conflicting or unknown selections fail. Use `cheatsheet.md` for user-facing usage and `design.md` for style rules. `assets/plain-document.css` contains the executable plain-document defaults.

For plain documents, use local images supplied by the user or images from a verified official HTTPS host. Check an official source before passing its exact hostname through `--verified-image-host`; do not infer that a third-party image is official. Every informative Markdown image needs meaningful alt text, and link labels should describe their destination. Raw HTML is escaped so it cannot bypass these checks. The saved HTML uses absolute local image paths and the PDF retains title, language, image, and link metadata.

On first interactive build, offer default or custom style choices; the choice is saved to `~/.config/md-to-pdf/profile.json` (or `$XDG_CONFIG_HOME/md-to-pdf/profile.json`). Non-interactive builds without a saved profile use defaults and do not write a profile. Choose system UI, bundled Geist, or a local `.ttf`, `.otf`, `.woff`, or `.woff2` font file. The CLI resolves relative `--font` paths from the working directory; frontmatter font paths resolve from the Markdown file. Explicit missing or invalid files fail. Per-document `font`, `accent`, and `paper` frontmatter or CLI options override the saved profile for that build. The résumé's approved layout remains isolated from profile styling.
Google Fonts families use `font: 'google:Family Name'` or `--font 'google:Family Name'`. Fontsource families use `font: 'fontsource:family-id'`, optionally with `@major.minor.patch` to select an exact version. A new family requires an interactive download prompt, or an explicit `--allow-font-download` only after the user authorizes the download. Downloaded files are cached outside the skill; later builds use pinned cached files offline. A denied or unavailable download stops the build.

## Résumés

Source résumés are the factual authority. Never invent metrics, dates, responsibilities, ownership, or credentials. Keep master sources at the workspace root and role-tailored Markdown in `resumes/targeted/`; these are private local inputs. The builder parses Markdown into validated `OUTPUT.content.json`, writes canonical HTML from `assets/templates/resume-ats.html`, and renders the PDF from that saved HTML. JSON is generated, not an editorial source. The schema is `references/schemas/resume-content.schema.json`.
The unified résumé build checks the approved two-page A4 contract. A saved global Style profile is ignored, and an explicit title or style override is rejected; change the canonical Template and design guide only when the user requests a layout change.

Preserve the approved two-page design: name left, title and contact right; uppercase section labels; compact single-column experience; company and role on one line with dates and location aligned right; company description below; summary, experience, education, languages, and skills last. Change content only for tailoring. Do not change layout, typography, spacing, hierarchy, header, or pagination without an explicit design request. The canonical `assets/templates/resume-ats.html` is the only résumé layout.

Markdown mapping: `# Name` is the identity; the following bold line is the headline; contact lines use ` · ` separators. `## Summary` / `## Resumo` is the summary. Each `### Company — Role` in experience has a dates/location line, optional description, and bullet lines. Earlier Experience / Experiência Anterior is a group. Preserve education, languages, and skills in source order, with Skills / Competências last. The parser rejects missing or malformed required content.

## Cover letters

The current cover-letter workflow uses `scripts/render-cover-letter.py` and ReportLab. It expects Markdown beginning with `Dear `, body paragraphs, and sign-off. Set `CAREER_NAME`, `CAREER_LOCATION`, `CAREER_EMAIL`, `CAREER_WEBSITE`, `CAREER_RECIPIENT`, and `CAREER_SUBJECT` locally; `CAREER_DATE` is optional. Keep personal values out of tracked files. `assets/templates/cover-letter.html` is a legacy reference; the current renderer does not consume it.

## Dependencies and review

Install packages from `requirements.txt`. WeasyPrint needs native Pango libraries on macOS. Use only project-owned renderers and templates, never Kami.

Save outputs in ignored local output directories. Inspect every PDF page as an image and check page count, text, links, clipping, and awkward page breaks. For résumés, verify every role and company/date line; for letters, verify one page. HTML is the visual review surface for templates that generate it. For visual changes, edit the canonical HTML/CSS, rebuild, and inspect the result.
