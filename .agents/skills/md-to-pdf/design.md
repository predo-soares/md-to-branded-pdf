# Design system

The project default is a restrained sans-serif document system on white A4 paper. The plain-document Template uses 20 mm margins, 11 pt body text, dark ink, understated rules, and a quiet code background. Headings are distinct without decorative serif styling. Its executable defaults live in `assets/plain-document.css`.

Each Template owns its layout contract and CSS. The approved résumé remains visually isolated in `assets/templates/resume-ats.html`; do not apply these plain-document defaults to it. Edit content to fit a Template. Change layout rules only when the user explicitly asks to change the Template or this design guide.

The PDF is rendered from saved HTML with WeasyPrint. Keep the generated HTML as the reviewable visual source, and check actual PDF pages before approving a layout.

Global profile choices are limited to font, accent, and paper color. The initial choices are system UI or bundled Geist and six-digit hex colors. Document-level choices override the profile only for that build. The plain-document Template applies those choices through CSS variables; each later Template must define which profile values it accepts without weakening its layout contract.
The proposal Template retains its existing Geist-based cover and numbered-section styling under default settings. A customized profile can change only its font, accent, and paper color; page geometry, section structure, and spacing stay under the proposal Template's control.
