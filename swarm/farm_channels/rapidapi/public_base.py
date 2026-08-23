"""Resolve Virtus Core public production API base for RapidAPI upstream."""

from __future__ import annotations

import os
from typing import Any
from urllib.parse import urlparse


_FORBIDDEN_HOSTS = frozenset(
    {
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
        "::1",
        "[::1]",
    }
)


def _is_private_or_local_host(host: str) -> bool:
    h = (host or "").strip().lower().rstrip(".")
    if not h:
        return True
    if h in _FORBIDDEN_HOSTS:
        return True
    if h.endswith(".local") or h.endswith(".internal"):
        return True
    if h.startswith("10."):
        return True
    if h.startswith("192.168."):
        return True
    if h.startswith("172."):
        # 172.16.0.0 – 172.31.255.255
        parts = h.split(".")
        if len(parts) >= 2 and parts[1].isdigit():
            n = int(parts[1])
            if 16 <= n <= 31:
                return True
    return False


def resolve_public_api_base() -> dict[str, Any]:
    """
    Public production API URL for RapidAPI servers[].

    Env (first wins): GENESIS_API_PUBLIC_URL, NEXT_PUBLIC_API_URL.
    Rejects localhost / private hosts — those must never be Hub upstream.
    """
    # Prefer explicit public API. GENESIS_OVH_PUBLIC_API = raw OVH nginx/JSON host
    # when virtuscore.com / api.virtuscore.com still point at HTML (Vercel/AWS).
    raw = (
        (os.environ.get("GENESIS_API_PUBLIC_URL") or "").strip()
        or (os.environ.get("GENESIS_OVH_PUBLIC_API") or "").strip()
        or (os.environ.get("NEXT_PUBLIC_API_URL") or "").strip()
    )
    if not raw:
        return {
            "ok": False,
            "base": "",
            "requires_ceo_action": True,
            "error": "public_api_url_missing",
            "detail": (
                "Set GENESIS_API_PUBLIC_URL or NEXT_PUBLIC_API_URL to the public "
                "Virtus Core production API (https://…). "
                "Do not use localhost or :8000 for RapidAPI upstream."
            ),
        }
    base = raw.rstrip("/")
    parsed = urlparse(base if "://" in base else f"https://{base}")
    if parsed.scheme not in ("http", "https"):
        return {
            "ok": False,
            "base": "",
            "requires_ceo_action": True,
            "error": "public_api_url_invalid_scheme",
            "detail": f"Public API URL must be http(s): got {parsed.scheme!r}",
        }
    host = parsed.hostname or ""
    if _is_private_or_local_host(host):
        return {
            "ok": False,
            "base": "",
            "requires_ceo_action": True,
            "error": "public_api_url_not_public",
            "detail": (
                f"Rejected host {host!r}. RapidAPI must call the public production "
                "Virtus API, not localhost/private network."
            ),
        }
    # Rebuild normalized base without trailing slash
    port = f":{parsed.port}" if parsed.port else ""
    normalized = f"{parsed.scheme}://{host}{port}"
    if parsed.path and parsed.path not in ("/", ""):
        normalized = f"{normalized}{parsed.path.rstrip('/')}"
    return {
        "ok": True,
        "base": normalized,
        "requires_ceo_action": False,
        "error": "",
        "detail": "Public production API base OK",
    }


def runtime_server_url(slug: str) -> dict[str, Any]:
    """Full servers[0].url for a Farm runtime slug."""
    base = resolve_public_api_base()
    if not base.get("ok"):
        return base
    s = "".join(c if c.isalnum() else "-" for c in (slug or "").lower()).strip("-")
    if not s:
        return {
            "ok": False,
            "base": base["base"],
            "requires_ceo_action": True,
            "error": "slug_required",
            "detail": "Runtime slug missing",
        }
    return {
        "ok": True,
        "base": base["base"],
        "slug": s,
        "server_url": f"{base['base']}/api/farm/runtime/{s}",
        "requires_ceo_action": False,
        "error": "",
        "detail": "OK",
    }


def paypal_payout_confirmed() -> bool:
    return (os.environ.get("RAPIDAPI_PAYPAL_CONNECTED") or "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )
