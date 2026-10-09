"""Verify general reports with optional financial context."""
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


class AnalyticalReportTests(unittest.TestCase):
    def build(self, source: Path, root: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(BUILD), str(source), "--template", "analytical-report",
             "--html", str(root / "report.html"), "--pdf", str(root / "report.pdf")],
            capture_output=True, text=True,
            env={**os.environ, "XDG_CONFIG_HOME": str(root / "config")},
        )

    def test_financial_section_is_optional_and_values_survive(self) -> None:
        for filename, financial in (("analytical-report.en.md", False),
                                    ("analytical-report-financial.en.md", True)):
            with self.subTest(filename=filename), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                result = self.build(ROOT / "references/examples" / filename, root)
                self.assertEqual(result.returncode, 0, result.stderr)
                content = json.loads((root / "report.content.json").read_text())
                self.assertEqual("financial_context" in content, financial)
                with fitz.open(root / "report.pdf") as pdf:
                    self.assertGreaterEqual(len(pdf), 1)
                    self.assertTrue(all(abs(page.rect.width - 595.28) < 1 and
                                        abs(page.rect.height - 841.89) < 1 for page in pdf))
                    text = "\n".join(page.get_text() for page in pdf)
                    links = [link["uri"] for page in pdf for link in page.get_links()]
                for heading in ("Thesis", "Evidence", "Analysis", "Risks", "Conclusion"):
                    self.assertIn(heading, text)
                self.assertLess(text.index("Thesis"), text.index("Conclusion"))
                if financial:
                    self.assertIn("$1,200", text)
                    self.assertIn("$450", text)
                    self.assertIn("https://example.org/source", links)
                else:
                    self.assertNotIn("Financial Context", text)
                    self.assertIn("https://example.org/methods", links)

    def test_long_report_paginates_without_losing_sections(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "long-report.md"
            base = (ROOT / "references/examples/analytical-report.en.md").read_text()
            evidence = "A synthetic observation is recorded for pagination testing. " * 32
            source.write_text(base.replace("## Analysis", (evidence + "\n\n") * 12 + "## Analysis"))
            result = self.build(source, root)
            self.assertEqual(result.returncode, 0, result.stderr)
            with fitz.open(root / "report.pdf") as pdf:
                self.assertGreater(len(pdf), 1)
                text = "\n".join(page.get_text() for page in pdf)
            self.assertIn("A synthetic observation", text)
            self.assertIn("Conclusion", text)

    def test_missing_risks_fails_validation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "invalid.md"
            source.write_text("# Report\n\n## Thesis\n\nA.\n\n## Evidence\n\nB.\n\n"
                              "## Analysis\n\nC.\n\n## Conclusion\n\nD.\n")
            result = self.build(source, root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Analytical report validation failed", result.stderr)
            self.assertFalse((root / "report.pdf").exists())


if __name__ == "__main__":
    unittest.main()
