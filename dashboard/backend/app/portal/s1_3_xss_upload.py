"""S1.3 — XSS / upload sanitization helpers (permanent controls)."""

from __future__ import annotations

import html
import re
from pathlib import Path

ENGINE_ID = "s1_3_xss_upload_v1"

_UNSAFE_UPLOAD_EXT = frozenset(
    {
        ".html",
        ".htm",
        ".xhtml",
        ".js",
        ".mjs",
        ".php",
        ".asp",
        ".aspx",
        ".jsp",
    }
)

_TRAVERSAL = re.compile(r"\.\.|[/\\]")


def safe_upload_extension(filename: str | None) -> str:
    """Return a single safe suffix (leading dot) or empty."""
    raw = Path(filename or "file").name
    if _TRAVERSAL.search(raw):
        return ""
    ext = Path(raw).suffix.lower()
    if ext in _UNSAFE_UPLOAD_EXT:
        return ""
    if not re.fullmatch(r"\.[a-z0-9]{1,8}", ext or ""):
        return ""
    return ext


def assert_safe_upload_filename(filename: str | None) -> None:
    """Raise ValueError when filename is a traversal or executable/HTML vector."""
    raw = filename or ""
    name = Path(raw).name
    if not name or name != raw.replace("\\", "/").split("/")[-1]:
        # Path components / absolute paths rejected
        if "/" in raw.replace("\\", "/") or raw.startswith(("..",)):
            raise ValueError("unsafe filename")
    if ".." in raw:
        raise ValueError("unsafe filename")
    ext = Path(name).suffix.lower()
    if ext in _UNSAFE_UPLOAD_EXT:
        raise ValueError(f"unsupported file type: {ext}")


def html_escape_user_text(value: str) -> str:
    """XSS defense for any HTML surface that echoes user/client text."""
    return html.escape(value or "", quote=True)


def contains_reflected_xss_payload(text: str) -> bool:
    """Heuristic: classic script payloads that must never appear unescaped in HTML."""
    lowered = (text or "").lower()
    return "<script" in lowered or "javascript:" in lowered or "onerror=" in lowered
