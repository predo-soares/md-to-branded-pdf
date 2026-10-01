"""Render the project's HTML résumé to PDF with WeasyPrint."""
from __future__ import annotations

import os
import platform
import tempfile
from pathlib import Path


def _load_weasyprint():
    cache = Path(tempfile.gettempdir()) / "resume-studio-font-cache"
    cache.mkdir(exist_ok=True)
    os.environ.setdefault("XDG_CACHE_HOME", str(cache))
    # System Python on macOS can find Homebrew's Pango libraries only by path.
    # This adjusts library discovery without changing the installed package.
    if platform.system() == "Darwin":
        import cffi

        names = {
            "libgobject-2.0-0": "libgobject-2.0.dylib",
            "libpango-1.0-0": "libpango-1.0.dylib",
            "libharfbuzz-0": "libharfbuzz.dylib",
            "libharfbuzz-subset-0": "libharfbuzz-subset.dylib",
            "libfontconfig-1": "libfontconfig.dylib",
            "libpangoft2-1.0-0": "libpangoft2-1.0.dylib",
        }
        library_paths = (Path("/opt/homebrew/lib"), Path("/usr/local/lib"))
        original_dlopen = cffi.FFI.dlopen

        def homebrew_dlopen(self, name, flags=0):
            if name in names:
                for directory in library_paths:
                    candidate = directory / names[name]
                    if candidate.exists():
                        return original_dlopen(self, str(candidate), flags)
            return original_dlopen(self, name, flags)

        cffi.FFI.dlopen = homebrew_dlopen

    from weasyprint import HTML
    return HTML


def render_pdf(source: Path, destination: Path) -> None:
    HTML = _load_weasyprint()
    destination.parent.mkdir(parents=True, exist_ok=True)
    HTML(filename=str(source.resolve()), base_url=source.resolve().parent.as_uri()).write_pdf(str(destination))
