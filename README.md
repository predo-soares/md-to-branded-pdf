# Career Tools

A home for reusable skills and tools that support job research, company research, role-fit evaluation, and application preparation.

## What belongs in this repository

- Authored Codex skills in `.agents/skills/`.
- Reusable tools in `tools/`, organized by purpose as they are added.
- Reusable schemas, documentation, and benchmarks in `docs/`.
- Synthetic examples and fixtures that contain no personal information or real application data.

## What stays local

Master résumés, vacancy-specific versions, application letters, PDFs, HTML previews, raw page captures, and experiments with vacancy data stay in the local checkout and are ignored by Git. The repository stores the workflow and tools, not a private application archive.

The local copy of the Kami skill is also ignored. Kami was an architectural reference while this project's document workflow was developed; the repository runs and maintains its own implementation.

## Current structure

```text
.agents/skills/md-to-pdf/      Markdown-to-PDF skill
docs/                          Plans and reusable documentation
tools/                         Reserved for reusable project tools
```

Tool directories are added when they contain real content. The repository is licensed under MIT; see `LICENSE`. Third-party materials retain their own notices and terms.

## Markdown to PDF

The `.agents/skills/md-to-pdf/SKILL.md` skill selects a PDF template from context for résumés, cover letters, proposals, pitch decks, and other document types. When the right template is unclear, the agent asks the user. Résumés follow Markdown → validated JSON → canonical HTML → PDF. Personal source documents and generated outputs are not committed. Dependencies are listed in `.agents/skills/md-to-pdf/requirements.txt`.
