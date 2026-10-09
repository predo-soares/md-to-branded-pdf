"""Test Fontsource consent, version pinning, cache reuse, and PDF embedding."""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import fitz


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from md_to_pdf.fonts.fontsource_fonts import resolve  # noqa: E402


FONT = Path(__file__).resolve().parents[1] / "assets/geist-latin.woff2"


class FontsourceTests(unittest.TestCase):
    def test_consent_version_cache_and_render(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"XDG_CACHE_HOME": directory}):
            calls: list[str] = []

            def fake_fetch(url: str) -> bytes:
                calls.append(url)
                if "api.fontsource.org" in url:
                    return b'{"latest":"5.2.7"}'
                return FONT.read_bytes()

            with self.assertRaises(PermissionError):
                resolve("example-sans", allow_download=False, fetcher=fake_fetch)
            self.assertEqual(calls, [])
            css = resolve("example-sans", allow_download=True, fetcher=fake_fetch)
            self.assertEqual(len(calls), 3)
            self.assertIn("example-sans@5.2.7/latin-400-normal.woff2", calls[1])
            self.assertIn("example-sans@5.2.7/latin-700-normal.woff2", calls[2])
            self.assertIn("FontsourceSelectedFont", css)
            self.assertEqual(css, resolve("example-sans", allow_download=False,
                                          fetcher=lambda _: self.fail("Cache must be offline")))
            manifest = Path(directory) / "md-to-pdf/fontsource/example-sans/5.2.7/manifest.json"
            self.assertEqual(json.loads(manifest.read_text())["version"], "5.2.7")

            command_source = Path(directory) / "command.md"
            command_source.write_text("# Command build\n\nLatin text.\n")
            command_pdf = Path(directory) / "command.pdf"
            result = subprocess.run(
                [sys.executable, str(SCRIPTS / "build.py"), str(command_source),
                 "--template", "plain-document", "--font", "fontsource:example-sans",
                 "--html", str(Path(directory) / "command.html"), "--pdf", str(command_pdf)],
                capture_output=True, text=True,
                env={**os.environ, "XDG_CACHE_HOME": directory,
                     "XDG_CONFIG_HOME": str(Path(directory) / "config")},
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertGreater(command_pdf.stat().st_size, 0)

            module_spec = importlib.util.spec_from_file_location("plain_builder", SCRIPTS / "md_to_pdf/templates/build-document.py")
            assert module_spec and module_spec.loader
            builder = importlib.util.module_from_spec(module_spec)
            module_spec.loader.exec_module(builder)
            source = Path(directory) / "example.md"
            source.write_text("# Synthetic Fontsource PDF\n\nA paragraph.\n")
            pdf_path = Path(directory) / "example.pdf"
            builder.build(source, Path(directory) / "example.html", pdf_path,
                          style_profile={"font": "fontsource:example-sans", "font_css": css,
                                         "accent": "#111111", "paper": "#ffffff"})
            with fitz.open(pdf_path) as pdf:
                fonts = pdf[0].get_fonts()
            self.assertTrue(any("FontsourceSelectedFont" in font[3] for font in fonts), fonts)

    def test_missing_or_invalid_asset_does_not_create_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"XDG_CACHE_HOME": directory}):
            def fake_fetch(url: str) -> bytes:
                return b"not a font" if "700-normal" in url else FONT.read_bytes()

            with self.assertRaisesRegex(ValueError, "missing or invalid"):
                resolve("example-sans@5.2.7", allow_download=True, fetcher=fake_fetch)
            manifest = Path(directory) / "md-to-pdf/fontsource/example-sans/5.2.7/manifest.json"
            self.assertFalse(manifest.exists())


if __name__ == "__main__":
    unittest.main()
