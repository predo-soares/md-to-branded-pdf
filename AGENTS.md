# Career Tools repository

This repository collects skills and small tools I create to research vacancies, evaluate fit, tailor application materials, and manage the job-search workflow. Keep changes focused on reusable instructions, source code, schemas, and documentation.

## Repository boundaries

- Personal résumé sources, vacancy-specific application documents, generated previews/PDFs, raw page captures, caches, and credentials are local inputs or outputs; do not add them to Git.
- Keep fixtures synthetic or scrubbed of personal data. Never copy private application content into examples, tests, or documentation.
- Add a directory only when it has real content. Put authored Codex skills in `.agents/skills/`, reusable tooling in `tools/`, and reusable research/benchmark documentation in `docs/`.
- Do not add a repository license until I choose one.

## Career-document workflow

- For résumé and cover-letter work, use the project-owned `.agents/skills/resume-studio/SKILL.md` and its templates, scripts, and renderers.
- Do not invoke the Kami skill or use its templates, styling, or scripts. Kami was a reference when creating our own workflow; it is not a dependency or execution tool for this repository.
- Treat source résumés as the factual authority. Do not invent metrics, dates, responsibilities, ownership, or credentials.
- Keep master résumés at the workspace root and vacancy-tailored Markdown in `resumes/targeted/`; these are private local inputs and are intentionally excluded from Git.
- The approved résumé design is documented in the Resume Studio skill. Keep its canonical HTML template as the sole visual source and render PDFs from the saved HTML.
