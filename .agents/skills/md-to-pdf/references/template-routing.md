# Template routing examples

Use the user's stated document purpose first. Read the source when that purpose is missing. Do not infer a Template from its length alone.

| Request | Route |
| --- | --- |
| “Export my CV” | Résumé Template |
| “Make this commercial proposal a PDF” | Proposal Template |
| “Turn these meeting notes into a PDF” | Plain-document Template |
| “Prepare a one-page proposal summary” | Ask whether the user wants a one-pager or the proposal layout |
| “Make this into a PDF” with mixed résumé and portfolio content | Ask which Template to use |
| “Create a PDF invoice” | Ask whether to adapt an existing Template or add a reusable invoice Template |

The CLI cannot infer intent. It uses `--template` or the Markdown's `template` frontmatter. A conflicting pair is an error, even when one is a default suggested by an agent. The agent should resolve ambiguity with the user before invoking the command.
