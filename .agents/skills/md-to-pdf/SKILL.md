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
| Application cover letter | One-page A4 letter | `python3 .agents/skills/md-to-pdf/scripts/build.py INPUT.md --template cover-letter --html OUTPUT.html --pdf OUTPUT.pdf` |
| Brief with one central message | One-pager A4 | `python3 .agents/skills/md-to-pdf/scripts/build.py INPUT.md --template one-pager --html OUTPUT.html --pdf OUTPUT.pdf` |
| Multi-chapter document or white paper | Long document A4 | `python3 .agents/skills/md-to-pdf/scripts/build.py INPUT.md --template long-document --html OUTPUT.html --pdf OUTPUT.pdf` |
| Portfolio with case studies | Portfolio A4 | `python3 .agents/skills/md-to-pdf/scripts/build.py INPUT.md --template portfolio --html OUTPUT.html --pdf OUTPUT.pdf` |
| Analytical report with a supported conclusion | Analytical report A4 | `python3 .agents/skills/md-to-pdf/scripts/build.py INPUT.md --template analytical-report --html OUTPUT.html --pdf OUTPUT.pdf` |
| Versioned release notes | Changelog A4 | `python3 .agents/skills/md-to-pdf/scripts/build.py INPUT.md --template changelog --html OUTPUT.html --pdf OUTPUT.pdf` |
| Pitch deck for PDF delivery | 16:9 pitch deck | `python3 .agents/skills/md-to-pdf/scripts/build.py INPUT.md --template pitch-deck --html OUTPUT.html --pdf OUTPUT.pdf` |
| Ordinary Markdown document | Plain A4 document | `python3 .agents/skills/md-to-pdf/scripts/build.py INPUT.md --template plain-document --html OUTPUT.html --pdf OUTPUT.pdf` |

The proposal renderer requires at least one `##` section. Its `assets/document.html` and `assets/tokens.css` control the layout. The first unnumbered `##` immediately after the `#` title is a cover subtitle. Later `##` headings become numbered sections. Proposal-specific investment and work-stage tables render when those headings are present. The standalone `build-proposal.py` command still supports `--kind`, `--client`, `--author`, `--date`, `--footer-left`, and `--footer-right`. Do not use this layout as a generic default.

The unified `scripts/build.py` command currently supports `plain-document`, `proposal`, `resume`, `cover-letter`, `one-pager`, `long-document`, `portfolio`, `analytical-report`, `changelog`, and `pitch-deck`; other Templates will join it as they are implemented. Direct builds require `--template` or YAML frontmatter `template`. Matching declarations are accepted; conflicting or unknown selections fail. Use `cheatsheet.md` for user-facing usage and `design.md` for style rules. `assets/plain-document.css` contains the executable plain-document defaults.

One-pagers start with a `#` title followed by a central-message paragraph. Add any supported sections; metrics are optional and must come from the source, never fabricated. The Template is one A4 page. If content overflows, the builder identifies the first block that breaks the page contract and stops without changing typography, spacing, or page geometry.
Long documents use natural A4 pagination for chapters, tables, figures, and links. A standalone Markdown image with an italic caption becomes a figure when rendered. Keep captions and source links factual; the Template prevents heading, row, and figure breaks where WeasyPrint supports them.
Portfolio case studies use `##` headings and require authored `### Context` and `### Approach` sections. `### Outcome` is optional and must contain only supported source claims. The builder validates the case structure, saves generated `.content.json`, and renders the original Markdown with optional images. It does not invent a result or leave an empty outcome block when one is absent.
Analytical reports require nonempty `## Thesis`, `## Evidence`, `## Analysis`, `## Risks`, and `## Conclusion` sections in that order. `## Financial Context` is optional before the conclusion; tables and figures must retain their sourced values. The builder validates the structure, saves generated `.content.json`, and paginates naturally on A4. Keep observations distinct from interpretations and state uncertainty in the authored content.
Changelogs use a `#` title, then `## [version] - YYYY-MM-DD` release headings and `### Category` headings with authored entries. `## Unreleased` is also accepted. Release and category order is preserved; empty categories fail validation. The generated `.content.json` records versions, dates, categories, and their Markdown. The PDF keeps source links and avoids separating release headings from their first entries where WeasyPrint supports it.
Pitch decks are PDF outputs. A line containing only `---` at the top level separates slides; the same line in fenced code stays inside that slide. The first slide is a cover with a `#` title, middle slides are assertion and evidence layouts with title headings, and the last slide is a closing layout. The builder saves `.slides.json` with layout metadata and fails if content produces more than one 16:9 PDF page per slide. Adapt the authored content to fit; never shrink the layout rules automatically.

For plain documents, use local images supplied by the user or images from a verified official HTTPS host. Check an official source before passing its exact hostname through `--verified-image-host`; do not infer that a third-party image is official. Every informative Markdown image needs meaningful alt text, and link labels should describe their destination. Raw HTML is escaped so it cannot bypass these checks. The saved HTML uses absolute local image paths and the PDF retains title, language, image, and link metadata.

On first interactive build, offer default or custom style choices; the choice is saved to `~/.config/md-to-pdf/profile.json` (or `$XDG_CONFIG_HOME/md-to-pdf/profile.json`). Non-interactive builds without a saved profile use defaults and do not write a profile. Choose system UI, bundled Geist, or a local `.ttf`, `.otf`, `.woff`, or `.woff2` font file. The CLI resolves relative `--font` paths from the working directory; frontmatter font paths resolve from the Markdown file. Explicit missing or invalid files fail. Per-document `font`, `accent`, and `paper` frontmatter or CLI options override the saved profile for that build. The résumé's approved layout remains isolated from profile styling.
Google Fonts families use `font: 'google:Family Name'` or `--font 'google:Family Name'`. Fontsource families use `font: 'fontsource:family-id'`, optionally with `@major.minor.patch` to select an exact version. A new family requires an interactive download prompt, or an explicit `--allow-font-download` only after the user authorizes the download. Downloaded files are cached outside the skill; later builds use pinned cached files offline. A denied or unavailable download stops the build.

## Résumés

Source résumés are the factual authority. Never invent metrics, dates, responsibilities, ownership, or credentials. Keep master sources at the workspace root and role-tailored Markdown in `resumes/targeted/`; these are private local inputs. The builder parses Markdown into validated `OUTPUT.content.json`, writes canonical HTML from `assets/templates/resume-ats.html`, and renders the PDF from that saved HTML. JSON is generated, not an editorial source. The schema is `references/schemas/resume-content.schema.json`.
The unified résumé build checks the approved two-page A4 contract. A saved global Style profile is ignored, and an explicit title or style override is rejected; change the canonical Template and design guide only when the user requests a layout change.

Preserve the approved two-page design: name left, title and contact right; uppercase section labels; compact single-column experience; company and role on one line with dates and location aligned right; company description below; summary, experience, education, languages, and skills last. Change content only for tailoring. Do not change layout, typography, spacing, hierarchy, header, or pagination without an explicit design request. The canonical `assets/templates/resume-ats.html` is the only résumé layout.

Markdown mapping: `# Name` is the identity; the following bold line is the headline; contact lines use ` · ` separators. `## Summary` / `## Resumo` is the summary. Each `### Company — Role` in experience has a dates/location line, optional description, and bullet lines. Earlier Experience / Experiência Anterior is a group. Preserve education, languages, and skills in source order, with Skills / Competências last. The parser rejects missing or malformed required content.

## Cover letters

The cover-letter workflow uses `assets/templates/cover-letter.html` as its canonical visual source, saves HTML, and renders that HTML with WeasyPrint. It expects Markdown beginning with `Dear `, body paragraphs, a sign-off, and a signature. Set `CAREER_NAME`, `CAREER_LOCATION`, `CAREER_EMAIL`, `CAREER_WEBSITE`, `CAREER_RECIPIENT`, and `CAREER_SUBJECT` locally; `CAREER_DATE` is optional. Keep personal values out of tracked files. The one-page A4 contract is enforced. The standalone `scripts/render-cover-letter.py` remains a compatibility command and now saves sibling HTML.

## Dependencies and review

Install packages from `requirements.txt`. WeasyPrint needs native Pango libraries on macOS. Use only project-owned renderers and templates, never Kami.

Save outputs in ignored local output directories. Inspect every PDF page as an image and check page count, text, links, clipping, and awkward page breaks. For résumés, verify every role and company/date line; for letters, verify one page. HTML is the visual review surface for templates that generate it. For visual changes, edit the canonical HTML/CSS, rebuild, and inspect the result.
