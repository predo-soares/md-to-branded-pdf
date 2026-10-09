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
            for phrase in ("Sample Person", "Application for Sample Role", "Dear Hiring Team,",
                           "My approach begins with the task", "I can help the team document decisions",
                           "I would welcome a conversation", "Sincerely,"):
                self.assertIn(phrase, text)
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

    def test_dense_letter_identifies_body_paragraph_without_pdf(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "long-letter.md"
            body = "Synthetic background detail for overflow testing. " * 280
            source.write_text("Dear Hiring Team,\n\nShort introduction.\n\n" + body +
                              "\n\nSincerely,\n\nSample Person\n")
            result = subprocess.run(
                [sys.executable, str(BUILD), str(source), "--template", "cover-letter",
                 "--html", str(root / "letter.html"), "--pdf", str(root / "letter.pdf")],
                capture_output=True, text=True,
                env={**os.environ, **FIELDS, "XDG_CONFIG_HOME": str(root / "config")},
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("body paragraph on line 5", result.stderr)
            self.assertFalse((root / "letter.pdf").exists())
            self.assertIn('font: 11pt/1.45 "Geist"', (root / "letter.html").read_text())


if __name__ == "__main__":
    unittest.main()
