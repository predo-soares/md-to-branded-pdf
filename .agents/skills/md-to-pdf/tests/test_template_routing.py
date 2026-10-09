"""Exercise Template selection through the public command."""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
import os
from pathlib import Path


BUILD = Path(__file__).resolve().parents[1] / "scripts/build.py"


class TemplateRoutingTests(unittest.TestCase):
    def run_build(self, content: str, *options: str) -> tuple[subprocess.CompletedProcess[str], Path]:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        directory = Path(temp.name)
        source = directory / "source.md"
        source.write_text(content, encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(BUILD), str(source), *options,
             "--html", str(directory / "output.html"), "--pdf", str(directory / "output.pdf")],
            text=True, capture_output=True, env={**os.environ, "XDG_CONFIG_HOME": str(directory / "config")},
        )
        return result, directory

    def test_frontmatter_selects_template_and_is_not_rendered(self) -> None:
        result, directory = self.run_build(
            "---\ntemplate: plain-document\nlang: pt-BR\ntitle: Título explícito\n---\n# Título do corpo\n\nConteúdo.\n"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        html = (directory / "output.html").read_text(encoding="utf-8")
        self.assertIn('<html lang="pt-BR">', html)
        self.assertIn("<title>Título explícito</title>", html)
        self.assertNotIn("template: plain-document", html)
        self.assertTrue((directory / "output.pdf").stat().st_size > 0)

    def test_matching_explicit_and_frontmatter_template(self) -> None:
        result, _ = self.run_build("---\ntemplate: plain-document\n---\n# Example\n", "--template", "plain-document")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_conflicting_template_is_an_error(self) -> None:
        result, _ = self.run_build("---\ntemplate: proposal\n---\n# Example\n", "--template", "plain-document")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Conflicting Template selections", result.stderr)

    def test_unknown_template_is_an_error(self) -> None:
        result, _ = self.run_build("---\ntemplate: invoice\n---\n# Example\n")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Unknown or unavailable Template", result.stderr)

    def test_missing_template_is_an_error(self) -> None:
        result, _ = self.run_build("# Example\n")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Choose a Template", result.stderr)


if __name__ == "__main__":
    unittest.main()
