"""Verify structured comparison and metrics deck slides."""
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


class StructuredDeckTests(unittest.TestCase):
    def build(self, source: Path, root: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(BUILD), str(source), "--template", "pitch-deck",
             "--html", str(root / "deck.html"), "--pdf", str(root / "deck.pdf")],
            capture_output=True, text=True,
            env={**os.environ, "XDG_CONFIG_HOME": str(root / "config")},
        )

    def test_comparison_and_metrics_preserve_values(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = self.build(ROOT / "references/examples/pitch-deck-comparison.en.md", root)
            self.assertEqual(result.returncode, 0, result.stderr)
            layouts = [slide["layout"] for slide in json.loads((root / "deck.slides.json").read_text())]
            self.assertEqual(layouts, ["cover", "comparison", "metrics", "closing"])
            with fitz.open(root / "deck.pdf") as pdf:
                self.assertEqual(len(pdf), 4)
                comparison = pdf[1].get_text()
                metrics = pdf[2].get_text()
            self.assertLess(comparison.index("First action"), comparison.index("Help text"))
            self.assertLess(metrics.index("Sample sessions"), metrics.index("Pauses at label"))
            self.assertIn("Guided setup", comparison)
            self.assertIn("Sessions without pause", metrics)

    def test_wrong_table_width_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "invalid.md"
            source.write_text("# Cover\n\nIntro.\n\n---\n\n## Metrics: values\n\n"
                              "| A | B | C |\n| --- | --- | --- |\n| One | Two | Three |\n\n"
                              "---\n\n## Close\n\nDone.\n")
            result = self.build(source, root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("needs 2 columns", result.stderr)

    def test_dense_table_reports_overflow(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "dense.md"
            rows = "\n".join(f"| Synthetic measure {i} | {i} |" for i in range(42))
            source.write_text("# Cover\n\nIntro.\n\n---\n\n## Metrics: many values\n\n"
                              "| Measure | Value |\n| --- | --- |\n" + rows +
                              "\n\n---\n\n## Close\n\nDone.\n")
            result = self.build(source, root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Pitch deck overflow", result.stderr)
            self.assertIn("on slide 2 at table on line", result.stderr)
            self.assertFalse((root / "deck.pdf").exists())


if __name__ == "__main__":
    unittest.main()
