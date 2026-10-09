# Markdown-to-PDF cheatsheet

To build an ordinary A4 document:

```sh
python3 .agents/skills/md-to-pdf/scripts/build.py input.md --template plain-document --html output.html --pdf output.pdf
```

To build a numbered proposal with its cover, sections, and tables, use `--template proposal` with the same command. The proposal keeps its existing Geist-based visual defaults unless you explicitly customize the global profile or this document's `font`, `accent`, or `paper` values.
To build a résumé with the approved A4 layout, use `--template resume`. A second page appears only when the content needs it; more than two pages fail. This saves validated `.content.json` next to the HTML. The résumé uses Geist and ignores your global Style profile and document style overrides.
To build a cover letter, use `--template cover-letter`. The Markdown starts with `Dear ` and ends with a sign-off and signature. Set the `CAREER_NAME`, `CAREER_LOCATION`, `CAREER_EMAIL`, `CAREER_WEBSITE`, `CAREER_RECIPIENT`, and `CAREER_SUBJECT` environment variables locally; `CAREER_DATE` is optional. The saved HTML is the PDF's visual source.
To build a one-pager, use `--template one-pager`. Start with `# Title`, then a short paragraph stating the central message. Add sections and only the metrics you actually have. The builder reports the first overflowing block when content does not fit one A4 page.
To build a multi-chapter document, use `--template long-document`. It paginates naturally on A4. Put an italic caption immediately after a standalone Markdown image to keep them together as a figure; headings and table rows avoid awkward splits where possible.
To build a portfolio, use `--template portfolio`. Each `## Case Study` needs `### Context` and `### Approach`; add `### Outcome` only when you have a supported result. Images are optional and need descriptive alt text. The generated `.content.json` records the validated case structure.
To build an analytical report, use `--template analytical-report`. Write `## Thesis`, `## Evidence`, `## Analysis`, `## Risks`, and `## Conclusion` in that order. Add `## Financial Context` before the conclusion only when the source contains relevant financial evidence. The generated `.content.json` records the validated sections; tables and source links remain in the PDF.
To build release notes, use `--template changelog`. Start with `# Changelog`, then add releases such as `## [1.2.0] - 2026-09-15` and categories such as `### Added` with at least one entry. `## Unreleased` is supported. The generated `.content.json` records release order and dates.
To build a PDF pitch deck, use `--template pitch-deck`. Write a `#` cover title, then separate slides with a top-level `---` line. Give each slide a heading; middle slides state an assertion and supporting evidence, and the final slide gives a next step. The output is 16:9, one PDF page per slide. An overfull slide stops the build, so edit its content and rebuild. The generated `.slides.json` lists slide layouts and titles.
Overflow errors for letters, one-pagers, and slides identify the block and source line that first fails to fit. Edit that content and rebuild. The builder keeps the saved HTML for diagnosis and does not shrink text, alter page dimensions, or add ellipses.
For a comparison slide, use a `## Comparison: ...` heading followed by a three-column Markdown table. For a metrics slide, use `## Metrics: ...` and a two-column label/value table. See `references/examples/pitch-deck-comparison.en.md` for synthetic examples.
To add a chart to an analytical report or pitch deck, use a fenced `chart` block with JSON, for example `{"type":"bar","title":"Sample tasks","data":[{"label":"A","value":3}]}`. `line`, `metric`, `donut`, and `waterfall` use the same data shape; waterfall values can be negative. An optional `unit` appears next to values. See `references/examples/analytical-report-charts.en.md`, `references/examples/pitch-deck-charts.en.md`, and `references/examples/visual-catalog.en.md`. Keep each chart to 12 items or fewer.
To add a timeline, flowchart, quadrant, layer stack, or swimlane to a long document or deck, use a fenced `diagram` JSON block. See `references/examples/long-document-diagrams.en.md`, `references/examples/pitch-deck-diagrams.en.md`, and `references/examples/visual-catalog.en.md` for data shapes. The renderer positions them automatically. Review the resulting PDF visually before sharing it.

Choose the Template explicitly with `--template` or YAML frontmatter:

```yaml
---
template: plain-document
lang: en
title: Example title
font: Geist
accent: '#0055aa'
paper: '#ffffff'
---
```

If both sources name a Template, they must agree. If the intended document type is unclear, ask the user to choose before running the command. The output paths must differ from the Markdown source and from each other. Generated files belong in an ignored local output directory.
Each successful build also saves a validated `.content.json` beside its HTML. The Markdown remains the file to edit; see `references/schemas/README.md` for the ten Template contracts.

The first interactive build offers default Geist styling or customization. Choose `system-ui`, a local `.ttf`, `.otf`, `.woff`, or `.woff2` file, or another supported family, plus hex accent and paper colors. The choice is reused globally; `--font`, `--accent`, and `--paper` override it for one eligible build. A relative CLI font path starts at the working directory; a relative frontmatter font path starts at the Markdown file. Non-interactive builds without a saved profile use Geist defaults.

For a Google Fonts family, use `--font 'google:Family Name'`. A new family requires permission before download; an interactive build prompts. In non-interactive use, pass `--allow-font-download` only after the user has authorized that specific download. Cached families rebuild offline without that flag.

For Fontsource, use `--font 'fontsource:family-id'` or pin a version with `--font 'fontsource:family-id@5.2.7'`. The first approved download resolves and caches an exact version and its regular and bold Latin files. Later builds use that cache offline. The same download permission rule applies.

Use standard Markdown headings, paragraphs, lists, links, fenced code, and tables. Start with a `#` heading to set the PDF title. See `references/design.md` for style rules; this cheatsheet is the short usage reference.
To edit a layout or generated component, use the file map in `references/template-editing.md`, then rebuild the fixture gallery and review the affected pages.

Add a local image with descriptive alt text, such as `![Revenue by quarter](figures/revenue.png)`. Use meaningful link labels, such as `[Project documentation](https://example.org/docs)`. For a remote image from an official source you have verified, pass its exact HTTPS hostname with `--verified-image-host example.org`. Other remote image hosts are rejected.

For an optional PDF inspection, run `python3 .agents/skills/md-to-pdf/scripts/verify.py output.pdf --output review/`. It writes a JSON report, a checklist, and `page-001.png`, `page-002.png`, and so on. Inspect every page image and approve the visuals yourself; the report does not approve them automatically.
To generate the synthetic gallery for all ten Templates, run `python3 .agents/skills/md-to-pdf/scripts/gallery.py --output output/fixture-gallery`. Open `output/fixture-gallery/index.md` for links to HTML, PDF, page images, and verification reports. Run the separate business-rule suite with `python3 -m unittest discover -s .agents/skills/md-to-pdf/tests -q`. The gallery never grants visual approval.
Record acceptance or defects for every Template in the generated `output/fixture-gallery/human-review.md`. Public release remains pending until the owner completes that review and explicitly approves it.
