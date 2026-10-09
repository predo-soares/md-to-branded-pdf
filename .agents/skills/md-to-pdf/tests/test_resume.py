"""Verify the approved résumé through the unified public build command."""
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
FIXTURE = ROOT / "references/examples/resume.en.md"


class ResumeTests(unittest.TestCase):
    def test_validated_json_saved_html_one_page_when_content_fits_and_skills_last(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = root / "config/md-to-pdf/profile.json"
            config.parent.mkdir(parents=True)
            config.write_text(json.dumps({"font": "google:Uncached Font",
                                          "accent": "#ff0000", "paper": "#000000"}))
            html_path, pdf_path = root / "resume.html", root / "resume.pdf"
            result = subprocess.run(
                [sys.executable, str(BUILD), str(FIXTURE), "--html", str(html_path),
                 "--pdf", str(pdf_path)], capture_output=True, text=True,
                env={**os.environ, "XDG_CONFIG_HOME": str(root / "config"),
                     "XDG_CACHE_HOME": str(root / "cache")},
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            content = json.loads((root / "resume.content.json").read_text())
            self.assertEqual([item.get("company") for item in content["experience"] if item["kind"] == "role"],
                             ["Example Company", "Sample Studio", "Fictional Labs", "Demo Collective"])
            self.assertEqual(content["experience"][0]["datesLocation"], "2024 – 2026 · City, Country")
            self.assertEqual(content["experience"][1]["datesLocation"], "2022 – 2024 · Remote")
            html = html_path.read_text()
            self.assertIn('class="job earlier-experience"', html)
            self.assertNotIn("#ff0000", html)
            self.assertNotIn("GoogleSelectedFont", html)
            with fitz.open(pdf_path) as pdf:
                self.assertEqual(len(pdf), 1)
                self.assertTrue(all(abs(page.rect.width - 595.28) < 1 and
                                    abs(page.rect.height - 841.89) < 1 for page in pdf))
                text = "\n".join(page.get_text() for page in pdf)
            self.assertLess(text.index("Sample Studio"), text.index("EARLIER EXPERIENCE"))
            self.assertLess(text.index("LANGUAGES"), text.index("SKILLS"))
            self.assertIn("Example Company", text)
            self.assertIn("Sample Studio", text)

    def test_explicit_style_override_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = subprocess.run(
                [sys.executable, str(BUILD), str(FIXTURE), "--font", "Geist",
                 "--html", str(root / "resume.html"), "--pdf", str(root / "resume.pdf")],
                capture_output=True, text=True,
                env={**os.environ, "XDG_CONFIG_HOME": str(root / "config")},
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("does not accept title or style overrides", result.stderr)

    def test_second_page_appears_only_when_content_requires_it(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "dense-resume.md"
            base = FIXTURE.read_text()
            extra = "".join(
                f"\n### Fictional Team {index} — Interface Engineer\n"
                "**2020 – 2021 · Remote**\n"
                "A synthetic role included to exercise natural pagination.\n"
                "- Built a small interface component from an approved specification.\n"
                "- Reviewed rendered behavior with a sample team.\n"
                for index in range(4)
            )
            source.write_text(base.replace("## Education", extra + "\n## Education"))
            result = subprocess.run(
                [sys.executable, str(BUILD), str(source), "--template", "resume",
                 "--html", str(root / "resume.html"), "--pdf", str(root / "resume.pdf")],
                capture_output=True, text=True,
                env={**os.environ, "XDG_CONFIG_HOME": str(root / "config")},
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            with fitz.open(root / "resume.pdf") as pdf:
                self.assertEqual(len(pdf), 2)
                self.assertIn("SKILLS", pdf[-1].get_text())


if __name__ == "__main__":
    unittest.main()
