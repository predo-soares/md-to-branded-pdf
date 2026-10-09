"""Verify PDF inspection reports for synthetic good and defective files."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import fitz


ROOT = Path(__file__).resolve().parents[1]
VERIFY = ROOT / "scripts/verify.py"


class VerifyTests(unittest.TestCase):
    def run_verify(self, pdf: Path, output: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, str(VERIFY), str(pdf), "--output", str(output)],
                              capture_output=True, text=True)

    def test_good_pdf_reports_pages_fonts_links_and_images(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pdf_path = root / "good.pdf"
            pdf = fitz.open()
            page = pdf.new_page(width=595.28, height=841.89)
            page.insert_text((72, 72), "Synthetic finished document")
            page.insert_link({"kind": fitz.LINK_URI, "from": fitz.Rect(72, 62, 250, 80),
                              "uri": "https://example.org/source"})
            pdf.save(pdf_path)
            pdf.close()
            output = root / "review"
            result = self.run_verify(pdf_path, output)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads((output / "verification.json").read_text())
            self.assertEqual(report["page_count"], 1)
            self.assertEqual(report["text_coverage_ratio"], 1)
            self.assertTrue(report["fonts"])
            self.assertEqual(report["links"][0]["uri"], "https://example.org/source")
            self.assertEqual(report["findings"], [])
            self.assertEqual(report["visual_approval"], "pending_human_review")
            self.assertTrue((output / "page-001.png").is_file())
            self.assertIn("Inspect every", (output / "review.md").read_text())

    def test_defective_pdf_reports_placeholders_and_empty_page(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pdf_path = root / "defective.pdf"
            pdf = fitz.open()
            page = pdf.new_page()
            page.insert_text((72, 72), "TODO {{Client name}}")
            pdf.new_page()
            pdf.save(pdf_path)
            pdf.close()
            output = root / "review"
            result = self.run_verify(pdf_path, output)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads((output / "verification.json").read_text())
            self.assertEqual(report["page_count"], 2)
            self.assertEqual(report["pages_with_text"], 1)
            self.assertIn("Placeholder-like text found", report["findings"])
            self.assertIn("At least one page has no extractable text", report["findings"])
            self.assertEqual({item["text"] for item in report["placeholders"]}, {"TODO", "{{Client name}}"})
            self.assertTrue((output / "page-002.png").is_file())


if __name__ == "__main__":
    unittest.main()
