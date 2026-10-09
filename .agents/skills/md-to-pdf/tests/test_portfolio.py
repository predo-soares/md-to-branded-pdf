"""Verify validated multi-case portfolios without invented outcomes."""
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
FIXTURE = ROOT / "references/examples/portfolio.en.md"


class PortfolioTests(unittest.TestCase):
    def run_build(self, source: Path, root: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(BUILD), str(source), "--template", "portfolio",
             "--html", str(root / "portfolio.html"), "--pdf", str(root / "portfolio.pdf")],
            capture_output=True, text=True,
            env={**os.environ, "XDG_CONFIG_HOME": str(root / "config")},
        )

    def test_cases_image_optional_outcome_and_pdf_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = self.run_build(FIXTURE, root)
            self.assertEqual(result.returncode, 0, result.stderr)
            content = json.loads((root / "portfolio.content.json").read_text())
            self.assertEqual(len(content["cases"]), 2)
            self.assertIn("outcome", content["cases"][0])
            self.assertNotIn("outcome", content["cases"][1])
            html = (root / "portfolio.html").read_text()
            self.assertIn("<figure>", html)
            self.assertIn("<figcaption>", html)
            with fitz.open(root / "portfolio.pdf") as pdf:
                text = "\n".join(page.get_text() for page in pdf)
                links = [link["uri"] for page in pdf for link in page.get_links()]
            self.assertLess(text.index("Case Study A"), text.index("Case Study B"))
            self.assertIn("questions for a later experiment", text)
            self.assertIn("No outcome section is present", text)
            self.assertIn("https://example.org/methods", links)

    def test_missing_approach_fails_schema_validation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "invalid.md"
            source.write_text("# Portfolio\n\n## Case A\n\n### Context\n\nA context.\n")
            result = self.run_build(source, root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Portfolio content validation failed", result.stderr)
            self.assertFalse((root / "portfolio.pdf").exists())


if __name__ == "__main__":
    unittest.main()
