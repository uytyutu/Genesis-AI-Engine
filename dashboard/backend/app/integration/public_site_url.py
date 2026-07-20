"""Canonical public storefront URL — never fall back to retired Vercel host."""

from __future__ import annotations

import os
from urllib.parse import urlparse, urlunparse

# Retired Mission-1 preview host — must not appear in checkout / receipts / status links.
LEGACY_PUBLIC_HOSTS = frozenset(
    {
        "genesis-ai-engine.vercel.app",
    }
)

DEFAULT_PUBLIC_URL = "https://beta.genesis-ai-engine.com"


def configured_public_base() -> str:
    """Preferred storefront origin from ENV (no legacy Vercel fallback)."""
    for key in ("GENESIS_PUBLIC_URL", "NEXT_PUBLIC_SITE_URL"):
        raw = os.getenv(key, "").strip().rstrip("/")
        if not raw:
            continue
        try:
            host = (urlparse(raw).hostname or "").lower()
        except ValueError:
            continue
        if host in LEGACY_PUBLIC_HOSTS or host.endswith(".vercel.app"):
            continue
        if raw.startswith("http://") or raw.startswith("https://"):
            return raw
    return DEFAULT_PUBLIC_URL


def is_legacy_public_host(url: str) -> bool:
    try:
        host = (urlparse(url).hostname or "").lower()
    except ValueError:
        return False
    return host in LEGACY_PUBLIC_HOSTS or host.endswith(".vercel.app")


def canonicalize_storefront_url(url: str, *, fallback_path: str = "/") -> str:
    """Rewrite legacy Vercel hosts to GENESIS_PUBLIC_URL; keep path/query/hash."""
    raw = (url or "").strip()
    public = configured_public_base()
    if not raw:
        return f"{public}{fallback_path}"
    try:
        parsed = urlparse(raw)
    except ValueError:
        return f"{public}{fallback_path}"
    if not parsed.scheme or not parsed.netloc:
        # Relative path
        path = raw if raw.startswith("/") else f"/{raw}"
        return f"{public}{path}"
    host = (parsed.hostname or "").lower()
    if host in LEGACY_PUBLIC_HOSTS or host.endswith(".vercel.app"):
        return urlunparse(
            (
                urlparse(public).scheme,
                urlparse(public).netloc,
                parsed.path or fallback_path,
                "",
                parsed.query,
                parsed.fragment,
            )
        )
    return raw
