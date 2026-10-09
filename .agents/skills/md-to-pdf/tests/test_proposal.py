"""Exercise proposal migration through the public Markdown-to-PDF command."""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from md_to_pdf.rendering.render_html_pdf import _load_weasyprint  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "scripts/build.py"
FIXTURE = ROOT / "references/examples/proposal.pt-BR.md"


class ProposalTests(unittest.TestCase):
    def test_cover_sections_table_link_and_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            html_path, pdf_path = root / "proposal.html", root / "proposal.pdf"
            result = subprocess.run(
                [sys.executable, str(BUILD), str(FIXTURE), "--html", str(html_path),
                 "--pdf", str(pdf_path)], capture_output=True, text=True,
                env={**os.environ, "XDG_CONFIG_HOME": str(root / "config")},
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            html = html_path.read_text(encoding="utf-8")
            self.assertIn('class="cover"', html)
            self.assertIn('class="section-number">01', html)
            self.assertIn('class="labeled-table"', html)
            self.assertIn('lang="pt-BR"', html)
            with fitz.open(pdf_path) as pdf:
                self.assertEqual(pdf.metadata["title"], "Projeto Atlas")
                self.assertEqual(pdf.xref_get_key(pdf.pdf_catalog(), "Lang"), ("string", "pt-BR"))
                text = "\n".join(page.get_text() for page in pdf)
                links = [link["uri"] for page in pdf for link in page.get_links()]
            for expected in ("Organização Exemplo", "Equipe Exemplo", "Diagnóstico",
                             "R$ 1.000", "Objetivo", "Investimento total"):
                self.assertIn(expected, text)
            self.assertLess(text.index("Objetivo"), text.index("Investimento total"))
            self.assertIn("https://example.org/escopo", links)

            rerendered = root / "from-saved-html.pdf"
            _load_weasyprint()(filename=str(html_path)).write_pdf(str(rerendered))
            with fitz.open(rerendered) as pdf:
                self.assertEqual(text, "\n".join(page.get_text() for page in pdf))

    def test_explicit_profile_changes_style_without_changing_layout_values(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            html_path, pdf_path = root / "proposal.html", root / "proposal.pdf"
            result = subprocess.run(
                [sys.executable, str(BUILD), str(FIXTURE), "--font", "system-ui",
                 "--accent", "#0055aa", "--paper", "#ffffee",
                 "--html", str(html_path), "--pdf", str(pdf_path)],
                capture_output=True, text=True,
                env={**os.environ, "XDG_CONFIG_HOME": str(root / "config")},
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            html = html_path.read_text(encoding="utf-8")
            self.assertIn("background: #ffffee", html)
            self.assertIn("color: #0055aa", html)
            self.assertIn("font-family: \"system-ui\"", html)
            self.assertIn("height: 235mm", html)


if __name__ == "__main__":
    unittest.main()
