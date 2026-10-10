"""Read the generated-visual color palette from the human-owned design guide."""
from __future__ import annotations

import re
from pathlib import Path

import yaml


DESIGN_GUIDE = Path(__file__).resolve().parents[3] / "references/design.md"
REQUIRED = {"paper", "ink", "muted", "accent", "accent_light", "surface", "line",
            "line_light", "positive", "negative", "chart_series"}


def load() -> dict[str, str | list[str]]:
    text = DESIGN_GUIDE.read_text(encoding="utf-8")
    match = re.search(r"```yaml\s*\n(.*?)\n```", text, flags=re.DOTALL)
    if not match:
        raise ValueError(f"Design guide has no YAML visual color palette: {DESIGN_GUIDE}")
    document = yaml.safe_load(match.group(1))
    colors = document.get("visual_colors") if isinstance(document, dict) else None
    if not isinstance(colors, dict) or set(colors) != REQUIRED:
        raise ValueError("Design guide visual_colors must define the supported color tokens")
    for name, value in colors.items():
        values = value if name == "chart_series" else [value]
        if (not isinstance(values, list) or (name == "chart_series" and len(values) != 12)
                or any(not isinstance(color, str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", color)
                       for color in values)):
            raise ValueError(f"Invalid color value in design guide: visual_colors.{name}")
    return colors


COLORS = load()
