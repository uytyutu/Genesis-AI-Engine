"""Security Gate S1.2 — infrastructure hardening helpers.

Headers · rate limits · CSRF posture notes.
Every control here must have a permanent automated test.
"""

from __future__ import annotations

import os
import time
from collections import defaultdict
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse, Response

ENGINE_ID = "security_hardening_s1_2_v1"

# Baseline API response headers (adversary / mis-framing / MIME sniffing).
DEFAULT_SECURITY_HEADERS: dict[str, str] = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "X-DNS-Prefetch-Control": "off",
}


def apply_security_headers(
    response: Response, *, production: bool | None = None
) -> Response:
    for key, value in DEFAULT_SECURITY_HEADERS.items():
        response.headers.setdefault(key, value)
    if production is None:
        from app.config import is_production

        production = is_production()
    if production:
        response.headers.setdefault(
            "Strict-Transport-Security",
            "max-age=31536000; includeSubDomains",
        )
    return response


def rate_limit_key(request: Request) -> str:
    ip = (request.client.host if request.client else "unknown") or "unknown"
    return ip


def check_rate_limit(
    buckets: dict[str, list[float]],
    *,
    key: str,
    limit: int,
    window_sec: float,
    now: float | None = None,
) -> bool:
    """Return True if request is allowed; False if over limit (caller → 429)."""
    ts = time.time() if now is None else now
    bucket = buckets[key]
    bucket[:] = [t for t in bucket if ts - t < window_sec]
    if len(bucket) >= limit:
        return False
    bucket.append(ts)
    return True


def portal_rate_limit_per_min() -> int:
    return int(os.getenv("GENESIS_PORTAL_RATE_LIMIT_PER_MIN", "120"))


def public_rate_limit_per_min() -> int:
    return int(os.getenv("GENESIS_RATE_LIMIT_PER_MIN", "40"))


def rate_limited_response() -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests — please wait a moment"},
    )


def portal_path_should_rate_limit(path: str) -> bool:
    return path.startswith("/portal/")


def csrf_posture() -> dict[str, Any]:
    """Documented CSRF controls for S1.2 (cookie session).

    Portal session cookie defaults: HttpOnly + SameSite=Lax.
    Lax blocks cross-site POST cookie send → primary CSRF mitigation.
    Double-submit CSRF token is Horizon unless SameSite=None is required.
    """
    return {
        "session_cookie_httponly": True,
        "session_cookie_samesite_default": "lax",
        "cross_site_post_cookie": "blocked_by_samesite_lax",
        "double_submit_token": "not_required_while_samesite_lax",
    }


LOCAL_CORS_ORIGINS: tuple[str, ...] = (
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
)


def cors_allow_origins(*, extra_csv: str = "") -> list[str]:
    """Local Mission Control origins always kept; never returns '*'."""
    extra = [o.strip() for o in extra_csv.split(",") if o.strip()]
    origins = list(dict.fromkeys([*LOCAL_CORS_ORIGINS, *extra]))
    return [o for o in origins if o != "*"]


def cors_credentials_safe(origins: list[str], *, allow_credentials: bool) -> bool:
    if allow_credentials and "*" in origins:
        return False
    return True
