# Content contracts

Each public Template has one `*-content.schema.json` file. The unified builder parses authored Markdown into a small generated content projection, validates that projection, saves it beside the HTML as `.content.json`, and then renders the PDF. These JSON files are outputs, not alternate editorial sources.

The contracts reflect different document structures. A résumé has identity, experience, and skills; a cover letter has salutation, body, and closing; a deck has ordered slides. Plain documents have a deliberately broad contract because arbitrary Markdown is their purpose. Shared `chart` and `diagram` fences have additional data validation in their own renderers. A schema file without a build-time validator would not protect users, so the gallery and contract tests exercise every public Template.
