"""Verify slide splitting, page layouts, metadata, and overflow."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import fitz


ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "scripts/build.py"


class PitchDeckTests(unittest.TestCase):
    def build(self, source: Path, root: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(BUILD), str(source), "--template", "pitch-deck",
             "--html", str(root / "deck.html"), "--pdf", str(root / "deck.pdf")],
            capture_output=True, text=True,
            env={**os.environ, "XDG_CONFIG_HOME": str(root / "config")},
        )

    def test_three_slide_deck_and_fenced_separator(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = self.build(ROOT / "references/examples/pitch-deck.en.md", root)
            self.assertEqual(result.returncode, 0, result.stderr)
            metadata = json.loads((root / "deck.slides.json").read_text())
            self.assertEqual([slide["layout"] for slide in metadata],
                             ["cover", "assertion", "closing"])
            with fitz.open(root / "deck.pdf") as pdf:
                self.assertEqual(len(pdf), 3)
                self.assertTrue(all(abs(page.rect.width / page.rect.height - 16 / 9) < 0.01
                                    for page in pdf))
                self.assertIn("Sample Product", pdf[0].get_text())
                self.assertIn("three of five", pdf[1].get_text())
                self.assertIn("Next step", pdf[2].get_text())
                self.assertIn("https://example.org/methods",
                              [link["uri"] for link in pdf[1].get_links()])

    def test_overflow_reports_error_and_leaves_no_pdf(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "long-deck.md"
            source.write_text("# Cover\n\nIntro.\n\n---\n\n## Crowded slide\n\n" +
                              ("A synthetic sentence for a long slide. " * 20 + "\n\n") * 35 +
                              "---\n\n## Closing\n\nDone.\n")
            result = self.build(source, root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Pitch deck overflow", result.stderr)
            self.assertIn("on slide 2 at paragraph on line", result.stderr)
            self.assertFalse((root / "deck.pdf").exists())


if __name__ == "__main__":
    unittest.main()
