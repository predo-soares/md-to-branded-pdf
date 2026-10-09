# Script layout

Run `build.py` to generate a PDF, `build_review_gallery.py` to generate all synthetic review fixtures, and `verify.py` to inspect a generated PDF. These are the primary commands.

The `md_to_pdf/` package contains implementation modules:

- `templates/`: template-specific Markdown-to-HTML/PDF builders
- `content/`: Markdown projections and validation
- `visuals/`: generated charts and diagrams
- `fonts/`: font resolution and style profile
- `rendering/`: WeasyPrint and media helpers

`build-resume.py` and `render-cover-letter.py` remain compatibility commands. Edit their implementations under `md_to_pdf/templates/`.
