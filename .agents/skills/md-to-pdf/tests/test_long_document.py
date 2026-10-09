"""Check natural A4 pagination, figure, table, links, and chapter order."""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import fitz


ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "scripts/build.py"
FIXTURE = ROOT / "references/examples/long-document.en.md"


class LongDocumentTests(unittest.TestCase):
    def test_chapters_figure_table_and_link_paginate_naturally(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            html_path, pdf_path = root / "document.html", root / "document.pdf"
            result = subprocess.run(
                [sys.executable, str(BUILD), str(FIXTURE), "--html", str(html_path),
                 "--pdf", str(pdf_path)], capture_output=True, text=True,
                env={**os.environ, "XDG_CONFIG_HOME": str(root / "config")},
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            html = html_path.read_text(encoding="utf-8")
            self.assertIn("<figure>", html)
            self.assertIn("<figcaption>", html)
            self.assertIn("<table>", html)
            self.assertIn("break-after: avoid", html)
            self.assertIn("break-inside: avoid", html)
            with fitz.open(pdf_path) as pdf:
                self.assertGreater(len(pdf), 1)
                self.assertTrue(all(abs(page.rect.width - 595.28) < 1 and
                                    abs(page.rect.height - 841.89) < 1 for page in pdf))
                text = "\n".join(page.get_text() for page in pdf)
                links = [link["uri"] for page in pdf for link in page.get_links()]
                self.assertTrue(any(page.get_drawings() for page in pdf))
            for heading in ("1. Context", "2. Method", "3. Synthesis and next steps"):
                self.assertIn(heading, text)
            self.assertLess(text.index("1. Context"), text.index("2. Method"))
            self.assertLess(text.index("2. Method"), text.index("3. Synthesis and next steps"))
            self.assertIn("Goal statement", text)
            self.assertIn("Questions for design", text)
            self.assertIn("https://example.org/methods", links)


if __name__ == "__main__":
    unittest.main()
