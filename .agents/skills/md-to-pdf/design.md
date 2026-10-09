# Design system

The project default is a restrained sans-serif document system on white A4 paper. The plain-document Template uses 20 mm margins, 11 pt body text, dark ink, understated rules, and a quiet code background. Headings are distinct without decorative serif styling. Its executable defaults live in `assets/plain-document.css`.

Each Template owns its layout contract and CSS. The approved résumé remains visually isolated in `assets/templates/resume-ats.html`; do not apply these plain-document defaults to it. Edit content to fit a Template. Change layout rules only when the user explicitly asks to change the Template or this design guide.

The PDF is rendered from saved HTML with WeasyPrint. Keep the generated HTML as the reviewable visual source, and check actual PDF pages before approving a layout.

Global profile choices are limited to font, accent, and paper color. The initial choices are system UI or bundled Geist and six-digit hex colors. Document-level choices override the profile only for that build. The plain-document Template applies those choices through CSS variables; each later Template must define which profile values it accepts without weakening its layout contract.
The proposal Template retains its existing Geist-based cover and numbered-section styling under default settings. A customized profile can change only its font, accent, and paper color; page geometry, section structure, and spacing stay under the proposal Template's control.
The cover-letter Template preserves its name, contact, date, recipient, subject, salutation, body, and closing hierarchy. It uses one A4 page with 18 mm top/bottom and 20 mm side margins. Custom profile choices may change font, accent, and paper without changing this layout.
The one-pager Template uses one A4 page with 20 mm margins, a prominent title, a central-message paragraph, and compact supporting sections. Its executable rules live in `assets/one-pager.css`. Metrics have no reserved space: include a table or list only when the source provides values. An overflow error calls for editorial content changes unless the user explicitly changes the Template or this guide.
