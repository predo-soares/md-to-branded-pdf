#!/usr/bin/env python3
"""Compatibility command for the approved résumé builder."""
from pathlib import Path
from runpy import run_path

run_path(str(Path(__file__).resolve().parent / "md_to_pdf/templates/build-resume.py"), run_name="__main__")
