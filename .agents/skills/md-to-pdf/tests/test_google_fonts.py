"""Verify Google Fonts consent and offline cache without live network calls."""
from __future__ import annotations

import os
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import fitz


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from md_to_pdf.fonts.google_fonts import resolve  # noqa: E402


FONT = Path(__file__).resolve().parents[1] / "assets/geist-latin.woff2"
CSS = b"""/* latin-ext */
@font-face { font-family: 'Example Sans'; font-style: normal; font-weight: 400;
src: url(https://fonts.gstatic.com/example-ext.woff2) format('woff2'); }
/* latin */
@font-face { font-family: 'Example Sans'; font-style: normal; font-weight: 400;
src: url(https://fonts.gstatic.com/example.woff2) format('woff2'); }
"""


class GoogleFontsTests(unittest.TestCase):
    def test_consent_download_and_offline_reuse(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"XDG_CACHE_HOME": directory}):
            calls: list[str] = []

            def fake_fetch(url: str) -> bytes:
                calls.append(url)
                return CSS if "fonts.googleapis.com" in url else FONT.read_bytes()

            with self.assertRaises(PermissionError):
                resolve("Example Sans", allow_download=False, fetcher=fake_fetch)
            self.assertEqual(calls, [])
            first = resolve("Example Sans", allow_download=True, fetcher=fake_fetch)
            self.assertEqual(len(calls), 3)
            self.assertIn("file://", first)
            self.assertIn("GoogleSelectedFont", first)
            second = resolve("Example Sans", allow_download=False,
                             fetcher=lambda _: self.fail("Cache reuse must not fetch"))
            self.assertEqual(first, second)

            spec = importlib.util.spec_from_file_location("plain_builder", SCRIPTS / "md_to_pdf/templates/build-document.py")
            assert spec and spec.loader
            builder = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(builder)
            source = Path(directory) / "example.md"
            source.write_text("# Synthetic Google PDF\n\nA short paragraph.\n")
            pdf_path = Path(directory) / "example.pdf"
            builder.build(source, Path(directory) / "example.html", pdf_path,
                          style_profile={"font": "google:Example Sans", "font_css": first,
                                         "accent": "#111111", "paper": "#ffffff"})
            with fitz.open(pdf_path) as pdf:
                fonts = pdf[0].get_fonts()
            self.assertTrue(any("GoogleSelectedFont" in font[3] for font in fonts), fonts)


if __name__ == "__main__":
    unittest.main()
