"""Compare the migrated HTML cover letter with the prior one-page content contract."""
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
FIXTURE = ROOT / "references/examples/cover-letter.en.md"
FIELDS = {
    "CAREER_NAME": "Sample Person",
    "CAREER_LOCATION": "City, Country",
    "CAREER_EMAIL": "sample@example.com",
    "CAREER_WEBSITE": "https://example.com",
    "CAREER_RECIPIENT": "Hiring Team",
    "CAREER_SUBJECT": "Application for Sample Role",
    "CAREER_DATE": "October 9, 2026",
}


class CoverLetterTests(unittest.TestCase):
    def test_saved_html_weasyprint_and_prior_visible_content(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            html_path, pdf_path = root / "letter.html", root / "letter.pdf"
            result = subprocess.run(
                [sys.executable, str(BUILD), str(FIXTURE), "--html", str(html_path),
                 "--pdf", str(pdf_path)], capture_output=True, text=True,
                env={**os.environ, **FIELDS, "XDG_CONFIG_HOME": str(root / "config")},
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            html = html_path.read_text()
            for label in ("Sample Person", "Hiring Team", "Application for Sample Role",
                          "Dear Hiring Team,", "Sincerely,"):
                self.assertIn(label, html)
            self.assertIn('class="signature">Sample Person', html)
            with fitz.open(pdf_path) as pdf:
                self.assertEqual(len(pdf), 1)
                page = pdf[0]
                self.assertAlmostEqual(page.rect.width, 595.28, delta=1)
                self.assertAlmostEqual(page.rect.height, 841.89, delta=1)
                text = page.get_text()
                links = [link["uri"] for link in page.get_links()]
            baseline = (
                "Sample Person\nCity, Country · sample@example.com · https://example.com\n"
                "October 9, 2026\nHiring Team\nApplication for Sample Role\n"
                "Dear Hiring Team,\nI am applying for the sample role. My background includes product design and frontend\n"
                "development.\nI can help the team document decisions, test interfaces, and deliver accessible workflows.\n"
                "Sincerely,\nSample Person\n"
            )
            self.assertEqual(text, baseline)
            self.assertIn("mailto:sample@example.com", links)
            self.assertIn("https://example.com", links)

    def test_missing_recipient_metadata_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            env = {**os.environ, **FIELDS, "CAREER_RECIPIENT": "",
                   "XDG_CONFIG_HOME": str(root / "config")}
            result = subprocess.run(
                [sys.executable, str(BUILD), str(FIXTURE), "--html", str(root / "letter.html"),
                 "--pdf", str(root / "letter.pdf")], capture_output=True, text=True, env=env,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Set CAREER_NAME", result.stderr)


if __name__ == "__main__":
    unittest.main()
