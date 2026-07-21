"""Proxy CEO /api/support calls to Railway production inbox when configured."""

from __future__ import annotations

import os
from typing import Any

import httpx
from fastapi import HTTPException, Request, Response


def remote_base() -> str:
    return os.getenv("SUPPORT_INBOX_REMOTE_URL", "").strip().rstrip("/")


def bridge_secret() -> str:
    return (
        os.getenv("SUPPORT_BRIDGE_SECRET", "").strip()
        or os.getenv("RESEND_INBOUND_WEBHOOK_SECRET", "").strip()
    )


def remote_enabled() -> bool:
    return bool(remote_base() and bridge_secret())


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
        raise HTTPException(status_code=502, detail=f"support_remote_unreachable:{exc}") from exc

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
