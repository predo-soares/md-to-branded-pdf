"""Verify shared chart data in reports and pitch decks."""
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


class ChartTests(unittest.TestCase):
    def build(self, source: Path, root: Path, template: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(BUILD), str(source), "--template", template,
             "--html", str(root / "output.html"), "--pdf", str(root / "output.pdf")],
            capture_output=True, text=True,
            env={**os.environ, "XDG_CONFIG_HOME": str(root / "config")},
        )

    def test_same_chart_values_render_in_report_and_deck(self) -> None:
        for template, fixture, expected_pages in (
            ("analytical-report", "analytical-report-charts.en.md", 1),
            ("pitch-deck", "pitch-deck-charts.en.md", 5),
        ):
            with self.subTest(template=template), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                result = self.build(ROOT / "references/examples" / fixture, root, template)
                self.assertEqual(result.returncode, 0, result.stderr)
                with fitz.open(root / "output.pdf") as pdf:
                    self.assertGreaterEqual(len(pdf), expected_pages)
                    text = "\n".join(page.get_text() for page in pdf)
                for label in ("Alpha", "Beta", "Gamma", "Week 1", "Week 2", "Week 3", "Sessions", "Completed"):
                    self.assertIn(label, text)
                for value in ("3 tasks", "5 tasks", "4 tasks", "2", "4", "3"):
                    self.assertIn(value, text)
                html = (root / "output.html").read_text()
                self.assertIn("<svg", html)
                self.assertIn('class="metric"', html)

    def test_empty_malformed_and_dense_data_fail(self) -> None:
        base = (ROOT / "references/examples/analytical-report-charts.en.md").read_text()
        original = '{"type":"bar","title":"Sample tasks by group","unit":" tasks","data":[{"label":"Alpha","value":3},{"label":"Beta","value":5},{"label":"Gamma","value":4}]}'
        cases = [('{"type":"bar","title":"Empty","data":[]}', "at least one"),
                 ('{"type":"bar","title":"Bad","data":[{"label":"A","value":"x"}]}', "finite non-negative"),
                 ('{"type":"line","title":"Dense","data":[' +
                  ','.join('{"label":"Item %s","value":%s}' % (i, i) for i in range(13)) + ']}', "too dense")]
        for replacement, message in cases:
            with self.subTest(message=message), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                source = root / "bad.md"
                source.write_text(base.replace(original, replacement))
                result = self.build(source, root, "analytical-report")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(message, result.stderr)
                self.assertFalse((root / "output.pdf").exists())


if __name__ == "__main__":
    unittest.main()
