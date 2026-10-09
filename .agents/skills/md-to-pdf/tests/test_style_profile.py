"""Check profile precedence and first-use behavior through a real PDF build."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import fitz


BUILD = Path(__file__).resolve().parents[1] / "scripts/build.py"
GEIST = Path(__file__).resolve().parents[1] / "assets/geist-latin.woff2"


class StyleProfileTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source.md"
        self.source.write_text("# Synthetic PDF\n\nA [link](https://example.org).\n", encoding="utf-8")
        self.config = self.root / "config"

    def build(self, *extra: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(BUILD), str(self.source), "--template", "plain-document",
             "--html", str(self.root / "output.html"), "--pdf", str(self.root / "output.pdf"), *extra],
            capture_output=True, text=True, env={**os.environ, "XDG_CONFIG_HOME": str(self.config)},
        )

    def test_noninteractive_first_use_uses_defaults_without_saving(self) -> None:
        result = self.build()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.config / "md-to-pdf/profile.json").exists())
        self.assertIn("--paper: #ffffff", (self.root / "output.html").read_text())

    def test_saved_profile_and_document_override(self) -> None:
        path = self.config / "md-to-pdf/profile.json"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps({"font": "Geist", "accent": "#0055aa", "paper": "#ffffee"}))
        result = self.build("--accent", "#aa5500")
        self.assertEqual(result.returncode, 0, result.stderr)
        html = (self.root / "output.html").read_text()
        self.assertIn('font-family: "Geist"', html)
        self.assertIn("--accent: #aa5500", html)
        self.assertIn("--paper: #ffffee", html)
        self.assertGreater((self.root / "output.pdf").stat().st_size, 0)

    def test_invalid_override_is_rejected(self) -> None:
        result = self.build("--paper", "red; color: blue")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Invalid paper color", result.stderr)

    def test_selected_local_font_is_embedded(self) -> None:
        local_font = self.root / "selected.woff2"
        local_font.write_bytes(GEIST.read_bytes())
        result = self.build("--font", str(local_font))
        self.assertEqual(result.returncode, 0, result.stderr)
        with fitz.open(self.root / "output.pdf") as pdf:
            fonts = pdf[0].get_fonts()
        self.assertTrue(any("UserSelectedFont" in font[3] for font in fonts), fonts)

    def test_missing_or_invalid_local_font_fails(self) -> None:
        missing = self.build("--font", str(self.root / "missing.ttf"))
        self.assertIn("Selected font file is unavailable", missing.stderr)
        invalid_file = self.root / "invalid.ttf"
        invalid_file.write_text("not a font")
        invalid = self.build("--font", str(invalid_file))
        self.assertIn("Selected font file is invalid", invalid.stderr)


if __name__ == "__main__":
    unittest.main()
