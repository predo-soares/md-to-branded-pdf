"""Verify changelog structure, source order, links, and page behavior."""
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


class ChangelogTests(unittest.TestCase):
    def build(self, source: Path, root: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(BUILD), str(source), "--template", "changelog",
             "--html", str(root / "changelog.html"), "--pdf", str(root / "changelog.pdf")],
            capture_output=True, text=True,
            env={**os.environ, "XDG_CONFIG_HOME": str(root / "config")},
        )

    def test_multi_version_source_order_and_links(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = self.build(ROOT / "references/examples/changelog.en.md", root)
            self.assertEqual(result.returncode, 0, result.stderr)
            content = json.loads((root / "changelog.content.json").read_text())
            self.assertEqual([r["version"] for r in content["releases"]],
                             ["1.2.0", "1.1.0", "1.0.0"])
            self.assertEqual([c["name"] for c in content["releases"][0]["categories"]],
                             ["Added", "Changed", "Fixed"])
            with fitz.open(root / "changelog.pdf") as pdf:
                text = "\n".join(page.get_text() for page in pdf)
                links = [link["uri"] for page in pdf for link in page.get_links()]
            self.assertLess(text.index("1.2.0"), text.index("1.1.0"))
            self.assertLess(text.index("1.1.0"), text.index("1.0.0"))
            self.assertIn("status message", text)
            self.assertIn("https://example.org/formats", links)
            self.assertIn("https://example.org/shortcuts", links)

    def test_release_heading_stays_with_an_entry(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "long-changelog.md"
            base = (ROOT / "references/examples/changelog.en.md").read_text()
            expansion = "\n".join(f"- Synthetic improvement number {index}." for index in range(85))
            source.write_text(base.replace("## [1.1.0]", expansion + "\n\n## [1.1.0]"))
            result = self.build(source, root)
            self.assertEqual(result.returncode, 0, result.stderr)
            with fitz.open(root / "changelog.pdf") as pdf:
                self.assertGreater(len(pdf), 1)
                pages = [page.get_text() for page in pdf]
            for index, page in enumerate(pages):
                if "1.1.0" in page:
                    self.assertIn("sample keyboard shortcut", page)
                    break
            else:
                self.fail("Second release heading is absent")

    def test_empty_category_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "invalid.md"
            source.write_text("# Changelog\n\n## [1.0.0] - 2026-07-01\n\n### Added\n")
            result = self.build(source, root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("no entries", result.stderr)


if __name__ == "__main__":
    unittest.main()
