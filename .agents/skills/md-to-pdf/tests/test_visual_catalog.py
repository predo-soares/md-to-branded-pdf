"""Verify the expanded structured visual catalog in a real PDF."""
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
sys.path.insert(0, str(ROOT / "scripts"))
from charts import render as render_chart
from diagrams import render as render_diagram


class VisualCatalogTests(unittest.TestCase):
    def test_all_new_types_render_in_pdf(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts/build.py"),
                 str(ROOT / "references/examples/visual-catalog.en.md"),
                 "--template", "long-document", "--html", str(root / "catalog.html"),
                 "--pdf", str(root / "catalog.pdf")], capture_output=True, text=True,
                env={**os.environ, "XDG_CONFIG_HOME": str(root / "config")},
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            with fitz.open(root / "catalog.pdf") as pdf:
                text = "\n".join(page.get_text() for page in pdf)
                fonts = {font[3].split("+")[-1] for page in pdf for font in page.get_fonts()}
                self.assertTrue(all(name.startswith("Geist") for name in fonts), fonts)
            for label in ("Design", "Removed", "Option A", "Interface", "Review", "Approve"):
                self.assertIn(label, text)
            source = (root / "catalog.html").read_text()
            for kind in ("donut-chart", "waterfall-chart", "quadrant-diagram", "layer-stack-diagram", "swimlane-diagram"):
                self.assertIn(kind, source)

    def test_invalid_visual_data_fails(self) -> None:
        cases = (
            (render_chart, {"type": "donut", "title": "Empty total", "data": [{"label": "A", "value": 0}]}, "positive"),
            (render_chart, {"type": "waterfall", "title": "Bad", "data": [{"label": "A", "value": "-2"}]}, "finite"),
            (render_diagram, {"type": "quadrant", "title": "Bad", "x_label": "X", "y_label": "Y", "items": [{"label": "A", "x": 1.2, "y": 0.5}]}, "0 to 1"),
            (render_diagram, {"type": "layer-stack", "title": "Bad", "layers": []}, "2–6"),
            (render_diagram, {"type": "swimlane", "title": "Bad", "lanes": ["A", "B"], "steps": [{"lane": "A", "label": "One"}, {"lane": "C", "label": "Two"}]}, "known lane"),
        )
        for renderer, data, message in cases:
            with self.subTest(data=data):
                with self.assertRaisesRegex(ValueError, message):
                    renderer(json.dumps(data))


if __name__ == "__main__":
    unittest.main()
