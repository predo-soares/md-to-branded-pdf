"""Validate Markdown images and links before PDF rendering."""
from __future__ import annotations

from pathlib import Path
from urllib.parse import unquote, urlparse

from markdown_it.token import Token


GENERIC_ALT = {"image", "photo", "picture", "graphic", "logo", "figure", "img"}
GENERIC_LINK = {"here", "click here", "read more", "link", "learn more"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}


def _image_url(raw: str, source: Path, verified_hosts: set[str]) -> str:
    parsed = urlparse(raw)
    if parsed.scheme in {"http", "https"}:
        if parsed.scheme != "https" or (parsed.hostname or "").lower() not in verified_hosts:
            raise ValueError(f"Remote image host is not verified: {raw}")
        return raw
    if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment:
        raise ValueError(f"Unsupported image location: {raw}")
    path = Path(unquote(parsed.path)).expanduser()
    if not path.is_absolute():
        path = source.parent / path
    path = path.resolve()
    if path.suffix.lower() not in IMAGE_EXTENSIONS:
        raise ValueError(f"Unsupported image format: {path}")
    if not path.is_file():
        raise ValueError(f"Image file does not exist: {path}")
    return path.as_uri()


def validate_and_rewrite(tokens: list[Token], source: Path, verified_hosts: set[str]) -> None:
    for token in tokens:
        if not token.children:
            continue
        line = token.map[0] + 1 if token.map else "unknown"
        link_label: list[str] | None = None
        link_url = ""
        for child in token.children:
            if child.type == "image":
                alt = child.content.strip()
                if not alt or alt.casefold() in GENERIC_ALT:
                    raise ValueError(f"Image on line {line} needs meaningful alternative text")
                child.attrSet("src", _image_url(child.attrGet("src") or "", source, verified_hosts))
            elif child.type == "link_open":
                link_label = []
                link_url = child.attrGet("href") or ""
            elif child.type == "link_close" and link_label is not None:
                label = "".join(link_label).strip()
                if not label or label.casefold() in GENERIC_LINK or label == link_url:
                    raise ValueError(f"Link on line {line} needs descriptive visible text")
                link_label = None
            elif link_label is not None:
                link_label.append(child.content)


def guarded_fetcher(verified_hosts: set[str]):
    from weasyprint.urls import default_url_fetcher

    def fetch(url: str):
        parsed = urlparse(url)
        if parsed.scheme not in {"file", "https"}:
            raise ValueError(f"Resource scheme is not allowed: {url}")
        if parsed.scheme == "https" and (parsed.hostname or "").lower() not in verified_hosts:
            raise ValueError(f"Resource host is not verified: {url}")
        result = default_url_fetcher(url)
        redirected = urlparse(result.get("redirected_url", url))
        if (redirected.scheme != parsed.scheme or
                (redirected.scheme == "https" and (redirected.hostname or "").lower() not in verified_hosts)):
            if "file_obj" in result:
                result["file_obj"].close()
            raise ValueError(f"Resource redirected to an unverified host: {redirected.geturl()}")
        return result

    return fetch
