"""Exercise the full synthetic gallery through public build and verify commands."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import fitz


ROOT = Path(__file__).resolve().parents[1]
GALLERY = ROOT / "scripts/gallery.py"


class GalleryTests(unittest.TestCase):
    def test_all_templates_generate_reviewable_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "gallery"
            result = subprocess.run([sys.executable, str(GALLERY), "--output", str(output)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            manifest = json.loads((output / "manifest.json").read_text())
            self.assertEqual(len(manifest["entries"]), 10)
            self.assertEqual(manifest["visual_approval"], "pending_human_review")
            for entry in manifest["entries"]:
                self.assertEqual(entry["status"], "generated_for_human_review")
                self.assertEqual(entry["expected"], entry["observed"])
                for path in (entry["files"]["html"], entry["files"]["pdf"],
                             entry["files"]["verification"], entry["files"]["checklist"],
                             *entry["files"]["page_images"]):
                    self.assertTrue((output / path).is_file(), path)
                with fitz.open(output / entry["files"]["pdf"]) as pdf:
                    fonts = {font[3].split("+")[-1] for page in pdf for font in page.get_fonts()}
                    self.assertTrue(fonts)
                    self.assertTrue(all(name.startswith("Geist") for name in fonts),
                                    f"{entry['template']}: {fonts}")
            self.assertIn("[PDF]", (output / "index.md").read_text())
            review = (output / "human-review.md").read_text()
            self.assertEqual(review.count("| Pending |"), 10)
            self.assertIn("Public release is explicitly approved", review)
            edited = review.replace("| plain-document | 2 | Pending | |",
                                    "| plain-document | 2 | Accepted | Reviewed all pages |")
            (output / "human-review.md").write_text(edited)
            rerun = subprocess.run([sys.executable, str(GALLERY), "--output", str(output)],
                                   capture_output=True, text=True)
            self.assertEqual(rerun.returncode, 0, rerun.stderr)
            self.assertEqual((output / "human-review.md").read_text(), edited)


if __name__ == "__main__":
    unittest.main()
