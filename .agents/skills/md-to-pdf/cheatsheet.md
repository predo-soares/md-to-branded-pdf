# Markdown-to-PDF cheatsheet

To build an ordinary A4 document:

```sh
python3 .agents/skills/md-to-pdf/scripts/build.py input.md --template plain-document --html output.html --pdf output.pdf
```

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

The first interactive build offers default or custom styling. Choose `system-ui` or bundled `Geist`, plus hex accent and paper colors. The choice is reused globally; `--font`, `--accent`, and `--paper` override it for one build. Non-interactive builds without a saved profile use defaults.

Use standard Markdown headings, paragraphs, lists, links, fenced code, and tables. Start with a `#` heading to set the PDF title. See `design.md` for style rules; this cheatsheet is the short usage reference.
