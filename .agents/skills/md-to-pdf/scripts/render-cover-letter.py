#!/usr/bin/env python3
"""Compatibility command for the standalone cover-letter renderer."""
from pathlib import Path
from runpy import run_path

run_path(str(Path(__file__).resolve().parent / "md_to_pdf/templates/render-cover-letter.py"), run_name="__main__")
