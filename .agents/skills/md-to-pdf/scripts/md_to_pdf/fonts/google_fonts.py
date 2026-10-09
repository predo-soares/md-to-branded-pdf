"""Resolve one Google Fonts family to cached local font files."""
from __future__ import annotations

import hashlib
import json
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Callable

from fontTools.ttLib import TTFont


FAMILY = re.compile(r"^[A-Za-z][A-Za-z0-9 ]{0,79}$")
FACE = re.compile(r"/\*\s*([^*]+?)\s*\*/\s*@font-face\s*\{([^}]+)\}", re.S)
SOURCE = re.compile(r"url\((?:['\"])?(https://fonts\.gstatic\.com/[^)'\"]+)(?:['\"])?\)")


def cache_root() -> Path:
    root = Path(os.environ.get("XDG_CACHE_HOME", str(Path.home() / ".cache")))
    return root / "md-to-pdf/google-fonts"


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 md-to-pdf/1"})
    with urllib.request.urlopen(request, timeout=20) as response:
        data = response.read(5_000_001)
    if len(data) > 5_000_000:
        raise ValueError("Google Fonts response is too large")
    return data


def resolve(family: str, *, allow_download: bool, fetcher: Callable[[str], bytes] = fetch) -> str:
    if not FAMILY.fullmatch(family):
        raise ValueError(f"Invalid Google Fonts family: {family}")
    key = hashlib.sha256(family.casefold().encode()).hexdigest()[:16]
    folder = cache_root() / key
    manifest = folder / "manifest.json"
    if manifest.exists():
        record = json.loads(manifest.read_text(encoding="utf-8"))
        if record.get("family") != family:
            raise ValueError("Google Fonts cache family mismatch")
        for name, digest in record["files"].items():
            path = folder / name
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                raise ValueError(f"Google Fonts cache file is missing or changed: {path}")
        return record["css"]
    if not allow_download:
        raise PermissionError(f"Google Fonts family '{family}' is not cached; permission is required before download")

    spec = urllib.parse.quote(family.replace(" ", "+"), safe="+")
    css_url = f"https://fonts.googleapis.com/css2?family={spec}:wght@400;700&display=swap"
    stylesheet = fetcher(css_url).decode("utf-8")
    selected: list[tuple[str, str]] = []
    for subset, face in FACE.findall(stylesheet):
        if subset.strip() not in {"latin", "latin-ext"}:
            continue
        match = SOURCE.search(face)
        if match:
            selected.append((face, match.group(1)))
    if not selected:
        raise ValueError(f"Google Fonts returned no Latin font files for '{family}'")

    folder.mkdir(parents=True, exist_ok=True)
    files: dict[str, str] = {}
    local_faces: list[str] = []
    for face, url in selected:
        data = fetcher(url)
        digest = hashlib.sha256(data).hexdigest()
        filename = f"{digest[:16]}.woff2"
        path = folder / filename
        path.write_bytes(data)
        try:
            with TTFont(path, lazy=True) as font:
                font["name"]
        except Exception as error:
            path.unlink(missing_ok=True)
            raise ValueError(f"Google Fonts returned an invalid font for '{family}'") from error
        files[filename] = digest
        local_face = face.replace(url, path.as_uri())
        local_face = re.sub(r"font-family:\s*[^;]+;", 'font-family: "GoogleSelectedFont";', local_face)
        local_faces.append(f"@font-face {{{local_face}}}")
    local_css = "\n".join(local_faces)
    manifest.write_text(json.dumps({"family": family, "files": files, "css": local_css,
                                    "source": css_url}, indent=2) + "\n", encoding="utf-8")
    return local_css
