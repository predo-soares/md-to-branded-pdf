"""Ensure every public Template has an active content schema."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build import TEMPLATES, read_source  # noqa: E402
from template_content import parse  # noqa: E402


FIXTURES = {
    "plain-document": "plain-document.en.md",
    "proposal": "proposal.pt-BR.md",
    "resume": "resume.en.md",
    "cover-letter": "cover-letter.en.md",
    "one-pager": "one-pager.en.md",
    "long-document": "long-document.en.md",
    "portfolio": "portfolio.en.md",
    "analytical-report": "analytical-report.en.md",
    "changelog": "changelog.en.md",
    "pitch-deck": "pitch-deck.en.md",
}


class TemplateContractTests(unittest.TestCase):
    def test_every_template_has_a_valid_schema_and_fixture(self) -> None:
        self.assertEqual(set(TEMPLATES), set(FIXTURES))
        for template, filename in FIXTURES.items():
            with self.subTest(template=template):
                schema_path = ROOT / "references/schemas" / f"{template}-content.schema.json"
                self.assertTrue(schema_path.is_file())
                schema = json.loads(schema_path.read_text())
                Draft202012Validator.check_schema(schema)
                source = ROOT / "references/examples" / filename
                markdown, _ = read_source(source)
                content = parse(template, markdown, source.stem)
                self.assertEqual(list(Draft202012Validator(schema).iter_errors(content)), [])

    def test_missing_required_structure_fails_before_pdf_generation(self) -> None:
        cases = {
            "plain-document": "",
            "proposal": "# Sample\n\n## 1. Scope\n",
            "cover-letter": "Dear Team,\n\nOnly one body paragraph.\n",
            "one-pager": "# Sample\n\n## Details\n\nToo late for a central message.\n",
            "long-document": "# Sample\n\nNo chapter.\n",
            "pitch-deck": "# Cover\n\nOnly one slide.\n",
        }
        for template, markdown in cases.items():
            with self.subTest(template=template), self.assertRaises(ValueError):
                parse(template, markdown)


if __name__ == "__main__":
    unittest.main()
