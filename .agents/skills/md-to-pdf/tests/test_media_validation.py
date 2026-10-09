"""Exercise images, links, metadata, and reading order in a generated PDF."""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from md_to_pdf.rendering.media_validation import _image_url  # noqa: E402


BUILD = Path(__file__).resolve().parents[1] / "scripts/build.py"


class MediaValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        image = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 100, 40), False)
        image.clear_with(0x0055AA)
        image.save(self.root / "chart.png")

    def build(self, markdown: str, *options: str) -> subprocess.CompletedProcess[str]:
        source = self.root / "source.md"
        source.write_text(markdown, encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(BUILD), str(source),
             "--html", str(self.root / "output.html"), "--pdf", str(self.root / "output.pdf"),
             *options], capture_output=True, text=True,
            env={**os.environ, "XDG_CONFIG_HOME": str(self.root / "config")},
        )

    def test_image_link_title_language_and_order(self) -> None:
        result = self.build("""---
template: plain-document
lang: pt-BR
title: Relatório de teste
---
# Relatório

Texto inicial.

![Barra azul do projeto](chart.png)

Veja [a documentação do projeto](https://example.org).

## Conclusão

Texto final.
""")
        self.assertEqual(result.returncode, 0, result.stderr)
        html = (self.root / "output.html").read_text(encoding="utf-8")
        self.assertIn((self.root / "chart.png").resolve().as_uri(), html)
        self.assertIn('alt="Barra azul do projeto"', html)
        with fitz.open(self.root / "output.pdf") as pdf:
            self.assertEqual(pdf.metadata["title"], "Relatório de teste")
            self.assertEqual(pdf.xref_get_key(pdf.pdf_catalog(), "Lang"), ("string", "pt-BR"))
            self.assertEqual(len(pdf[0].get_images()), 1)
            self.assertEqual(pdf[0].get_links()[0]["uri"], "https://example.org")
            text = pdf[0].get_text()
        self.assertLess(text.index("Texto inicial"), text.index("a documentação do projeto"))
        self.assertLess(text.index("a documentação do projeto"), text.index("Conclusão"))

    def test_missing_alt_and_generic_link_are_reported(self) -> None:
        missing_alt = self.build("# Document\n\n![](chart.png)\n", "--template", "plain-document")
        self.assertNotEqual(missing_alt.returncode, 0)
        self.assertIn("meaningful alternative text", missing_alt.stderr)
        generic_link = self.build("# Document\n\n[click here](https://example.org)\n", "--template", "plain-document")
        self.assertNotEqual(generic_link.returncode, 0)
        self.assertIn("descriptive visible text", generic_link.stderr)

    def test_remote_image_requires_verified_https_host(self) -> None:
        result = self.build("# Document\n\n![Official chart](https://example.org/chart.png)\n",
                            "--template", "plain-document")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Remote image host is not verified", result.stderr)
        self.assertEqual(
            _image_url("https://official.example.org/chart.png", self.root / "source.md",
                       {"official.example.org"}),
            "https://official.example.org/chart.png",
        )
        with self.assertRaisesRegex(ValueError, "not verified"):
            _image_url("http://official.example.org/chart.png", self.root / "source.md",
                       {"official.example.org"})


if __name__ == "__main__":
    unittest.main()
