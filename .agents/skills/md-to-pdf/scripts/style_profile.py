"""Persist and resolve the user's global PDF style choices."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path


DEFAULT = {"font": "Geist", "accent": "#1c1c1c", "paper": "#ffffff"}
FONTS = {"system-ui", "Geist"}
FONT_EXTENSIONS = {".ttf", ".otf", ".woff", ".woff2"}


def profile_path() -> Path:
    root = Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config")))
    return root / "md-to-pdf/profile.json"


def validate(profile: dict[str, str]) -> dict[str, str]:
    if set(profile) != set(DEFAULT):
        raise ValueError("Style profile must define font, accent, and paper")
    if profile["font"].startswith("google:"):
        from google_fonts import FAMILY
        if not FAMILY.fullmatch(profile["font"][7:]):
            raise ValueError(f"Invalid Google Fonts family: {profile['font'][7:]}")
    elif profile["font"].startswith("fontsource:"):
        from fontsource_fonts import SPEC
        if not SPEC.fullmatch(profile["font"][11:]):
            raise ValueError(f"Invalid Fontsource selection: {profile['font'][11:]}")
    elif profile["font"] not in FONTS:
        font = Path(profile["font"]).expanduser()
        if font.suffix.lower() not in FONT_EXTENSIONS:
            raise ValueError(f"Unsupported font format: {font.suffix or '(none)'}")
        if not font.is_file():
            raise ValueError(f"Selected font file is unavailable: {font}")
        try:
            from fontTools.ttLib import TTFont
            with TTFont(font, lazy=True) as selected_font:
                selected_font["name"]
        except Exception as error:
            raise ValueError(f"Selected font file is invalid: {font}") from error
    for key in ("accent", "paper"):
        if not re.fullmatch(r"#[0-9a-fA-F]{6}", profile[key]):
            raise ValueError(f"Invalid {key} color; use #RRGGBB")
    return profile


def load() -> dict[str, str] | None:
    path = profile_path()
    if not path.exists():
        return None
    content = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(content, dict):
        raise ValueError("Style profile must be a JSON object")
    return validate(content)


def save(profile: dict[str, str]) -> None:
    path = profile_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(validate(profile), indent=2) + "\n", encoding="utf-8")


def onboard() -> dict[str, str]:
    choice = input("First PDF build: use default style or customize? [default/custom]: ").strip().lower()
    if choice in ("", "default"):
        profile = DEFAULT.copy()
    elif choice == "custom":
        profile = {
            "font": input("Font [Geist/system-ui/local path/google:Family/fontsource:id]: ").strip() or DEFAULT["font"],
            "accent": input("Accent color [#RRGGBB]: ").strip() or DEFAULT["accent"],
            "paper": input("Paper color [#RRGGBB]: ").strip() or DEFAULT["paper"],
        }
    else:
        raise ValueError("Choose 'default' or 'custom'")
    if profile["font"] not in FONTS and not profile["font"].startswith(("google:", "fontsource:")):
        profile["font"] = str(Path(profile["font"]).expanduser().resolve())
    save(profile)
    return profile
