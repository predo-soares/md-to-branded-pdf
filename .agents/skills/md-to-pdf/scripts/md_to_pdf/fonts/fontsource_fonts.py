"""Resolve a Fontsource family to exact-version cached local WOFF2 files."""
from __future__ import annotations

import hashlib
import io
import json
import os
import re
import urllib.request
from pathlib import Path
from typing import Callable

from fontTools.ttLib import TTFont


SPEC = re.compile(r"^(?P<family>[a-z][a-z0-9-]{0,79})(?:@(?P<version>[0-9]+\.[0-9]+\.[0-9]+))?$")


def cache_root() -> Path:
    root = Path(os.environ.get("XDG_CACHE_HOME", str(Path.home() / ".cache")))
    return root / "md-to-pdf/fontsource"


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "md-to-pdf/1"})
    with urllib.request.urlopen(request, timeout=20) as response:
        data = response.read(5_000_001)
    if len(data) > 5_000_000:
        raise ValueError("Fontsource response is too large")
    return data


def _cached_css(folder: Path, family: str, version: str) -> str | None:
    manifest = folder / "manifest.json"
    if not manifest.exists():
        return None
    record = json.loads(manifest.read_text(encoding="utf-8"))
    if record.get("family") != family or record.get("version") != version:
        raise ValueError("Fontsource cache metadata does not match the selected family and version")
    for filename, digest in record["files"].items():
        path = folder / filename
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError(f"Fontsource cache file is missing or changed: {path}")
    return record["css"]


def resolve(specifier: str, *, allow_download: bool, fetcher: Callable[[str], bytes] = fetch) -> str:
    match = SPEC.fullmatch(specifier)
    if not match:
        raise ValueError(f"Invalid Fontsource selection: {specifier}")
    family, requested_version = match.group("family", "version")
    family_folder = cache_root() / family
    selection = family_folder / "selection.json"
    version = requested_version
    if version is None and selection.exists():
        saved = json.loads(selection.read_text(encoding="utf-8"))
        version = saved.get("version") if saved.get("family") == family else None
        if not isinstance(version, str) or not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version):
            raise ValueError("Fontsource saved version is invalid")
    if version is not None:
        cached = _cached_css(family_folder / version, family, version)
        if cached is not None:
            return cached
    if not allow_download:
        raise PermissionError(f"Fontsource family '{specifier}' is not cached; permission is required before download")
    if version is None:
        version_url = f"https://api.fontsource.org/v1/version/{family}"
        metadata = json.loads(fetcher(version_url).decode("utf-8"))
        version = metadata.get("latest") if isinstance(metadata, dict) else None
        if not isinstance(version, str) or not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version):
            raise ValueError(f"Fontsource did not return a valid version for '{family}'")

    folder = family_folder / version
    folder.mkdir(parents=True, exist_ok=True)
    files: dict[str, str] = {}
    faces: list[str] = []
    for weight in (400, 700):
        filename = f"latin-{weight}-normal.woff2"
        url = f"https://cdn.jsdelivr.net/fontsource/fonts/{family}@{version}/{filename}"
        try:
            data = fetcher(url)
        except OSError as error:
            raise ValueError(f"Fontsource asset is unavailable: {url}") from error
        path = folder / filename
        try:
            with TTFont(io.BytesIO(data), lazy=False) as font:
                font["name"]
        except Exception as error:
            raise ValueError(f"Fontsource asset is missing or invalid: {url}") from error
        path.write_bytes(data)
        files[filename] = hashlib.sha256(data).hexdigest()
        faces.append(f'@font-face {{ font-family: "FontsourceSelectedFont"; font-style: normal; '
                     f'font-weight: {weight}; src: url("{path.as_uri()}") format("woff2"); }}')
    css = "\n".join(faces)
    (folder / "manifest.json").write_text(json.dumps({"family": family, "version": version,
                                                       "files": files, "css": css}, indent=2) + "\n",
                                         encoding="utf-8")
    if requested_version is None:
        selection.write_text(json.dumps({"family": family, "version": version}, indent=2) + "\n",
                             encoding="utf-8")
    return css
