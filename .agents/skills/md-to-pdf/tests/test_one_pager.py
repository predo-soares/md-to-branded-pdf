"""Test one-page contracts with and without optional metrics."""
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


class OnePagerTests(unittest.TestCase):
    def build(self, source: Path, directory: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(BUILD), str(source), "--template", "one-pager",
             "--html", str(directory / "output.html"),
             "--pdf", str(directory / "output.pdf")], capture_output=True, text=True,
            env={**os.environ, "XDG_CONFIG_HOME": str(directory / "config")},
        )

    def test_optional_metrics_do_not_create_empty_content(self) -> None:
        for filename, expected, absent in (
            ("one-pager.en.md", "Approve a two-week discovery sprint", "First-task completion"),
            ("one-pager-metrics.en.md", "First-task completion", "Approve a two-week discovery sprint"),
        ):
            with self.subTest(filename=filename), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                result = self.build(ROOT / "references/examples" / filename, root)
                self.assertEqual(result.returncode, 0, result.stderr)
                with fitz.open(root / "output.pdf") as pdf:
                    self.assertEqual(len(pdf), 1)
                    self.assertAlmostEqual(pdf[0].rect.width, 595.28, delta=1)
                    self.assertAlmostEqual(pdf[0].rect.height, 841.89, delta=1)
                    text = pdf[0].get_text()
                self.assertIn(expected, text)
                self.assertNotIn(absent, text)
                self.assertIn("@page { size: A4; margin: 20mm; }", (root / "output.html").read_text())

    def test_overflow_identifies_content_block_without_layout_change(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "long.md"
            source.write_text("# Project Atlas\n\nA central message.\n\n## Details\n\n" +
                              " ".join(["This synthetic sentence tests the fixed page layout."] * 140))
            result = self.build(source, root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("overflows A4 at paragraph on line 7", result.stderr)
            self.assertFalse((root / "output.pdf").exists())
            self.assertIn("@page { size: A4; margin: 20mm; }", (root / "output.html").read_text())


if __name__ == "__main__":
    unittest.main()
