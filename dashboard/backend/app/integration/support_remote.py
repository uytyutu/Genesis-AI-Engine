"""Proxy CEO /api/support calls to Railway production inbox when configured."""

from __future__ import annotations

import os
from typing import Any

import httpx
from fastapi import Request, Response


def remote_base() -> str:
    return os.getenv("SUPPORT_INBOX_REMOTE_URL", "").strip().rstrip("/")


def bridge_secret() -> str:
    return (
        os.getenv("SUPPORT_BRIDGE_SECRET", "").strip()
        or os.getenv("RESEND_INBOUND_WEBHOOK_SECRET", "").strip()
    )


def remote_enabled() -> bool:
    return bool(remote_base() and bridge_secret())


def remote_response_is_unavailable(response: Response) -> bool:
    """True when Railway is down or does not expose Support routes → use local handlers.

    Distinguishes FastAPI missing-route ``{"detail":"Not Found"}`` from our
    thread miss ``{"detail":"not_found"}``.
    """
    code = int(getattr(response, "status_code", 0) or 0)
    if code in (502, 503, 504):
        return True
    if code != 404:
        return False
    raw = getattr(response, "body", None) or b""
    if isinstance(raw, memoryview):
        raw = raw.tobytes()
    text = raw.decode("utf-8", errors="ignore").strip()
    compact = text.replace(" ", "").lower()
    # Real Support API: thread / resource missing
    if '"detail":"not_found"' in compact:
        return False
    # Bare gateway / missing FastAPI route
    if not text or text.lower() in {"not found", "404 page not found"}:
        return True
    if '"detail":"notfound"' in compact or compact == '{"detail":"not found"}':
        return True
    if "not found" in text.lower() and "not_found" not in compact:
        return True
    return False


async def proxy_support(request: Request, path: str) -> Response | None:
    """Forward to Railway Support Inbox. Returns None when remote not configured."""
    base = remote_base()
    secret = bridge_secret()
    if not base or not secret:
        return None

    url = f"{base}{path}"
    if request.url.query:
        url = f"{url}?{request.url.query}"

    body = await request.body()
    headers = {
        "X-Support-Bridge": secret,
        "Content-Type": request.headers.get("content-type") or "application/json",
        "Accept": "application/json",
        "User-Agent": "Genesis-Support-Bridge/1.0",
    }
    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            res = await client.request(request.method, url, content=body, headers=headers)
    except httpx.HTTPError as exc:
        # Let local middleware fall back instead of hard-failing the CEO desk.
        return Response(
            content=f'{{"detail":"support_remote_unreachable","error":"{type(exc).__name__}"}}'.encode(
                "utf-8"
            ),
            status_code=502,
            media_type="application/json",
        )

    return Response(
        content=res.content,
        status_code=res.status_code,
        media_type=res.headers.get("content-type") or "application/json",
    )


def remote_status_overlay(local: dict[str, Any]) -> dict[str, Any]:
    out = dict(local)
    out["remote_proxy"] = remote_enabled()
    out["remote_url"] = remote_base() or None
    return out
