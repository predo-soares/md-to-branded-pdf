"""Verify structured diagrams render in long documents and PDF decks."""
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


class DiagramTests(unittest.TestCase):
    def build(self, source: Path, root: Path, template: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(BUILD), str(source), "--template", template,
             "--html", str(root / "output.html"), "--pdf", str(root / "output.pdf")],
            capture_output=True, text=True,
            env={**os.environ, "XDG_CONFIG_HOME": str(root / "config")},
        )

    def test_timeline_and_flowchart_in_document_and_deck(self) -> None:
        for template, fixture in (("long-document", "long-document-diagrams.en.md"),
                                  ("pitch-deck", "pitch-deck-diagrams.en.md")):
            with self.subTest(template=template), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                result = self.build(ROOT / "references/examples" / fixture, root, template)
                self.assertEqual(result.returncode, 0, result.stderr)
                with fitz.open(root / "output.pdf") as pdf:
                    if template == "pitch-deck":
                        self.assertEqual(len(pdf), 4)
                    text = "\n".join(page.get_text() for page in pdf)
                    fonts = {font[3].split("+")[-1] for page in pdf for font in page.get_fonts()}
                    self.assertTrue(all(name.startswith("Geist") for name in fonts), fonts)
                for label in ("Draft", "Review", "Trial", "Decision", "Receive draft",
                              "Review evidence", "Revise", "Approve", "Needs work", "Ready"):
                    self.assertIn(label, text)
                html = (root / "output.html").read_text()
                self.assertIn('class="generated-diagram timeline-diagram"', html)
                self.assertIn('class="generated-diagram flowchart-diagram"', html)
                self.assertIn('marker-end="url(#diagram-arrow)"', html)

    def test_bad_connection_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "invalid.md"
            source.write_text("# Invalid\n\n```diagram\n"
                              '{"type":"flowchart","title":"Bad","nodes":[{"id":"a","label":"A"},{"id":"b","label":"B"}],"edges":[{"from":"a","to":"missing"}]}\n'
                              "```\n")
            result = self.build(source, root, "long-document")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("known nodes", result.stderr)
            self.assertFalse((root / "output.pdf").exists())


if __name__ == "__main__":
    unittest.main()
