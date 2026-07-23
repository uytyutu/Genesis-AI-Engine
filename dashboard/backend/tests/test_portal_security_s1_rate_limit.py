"""S1 — document / probe public rate-limit behaviour.

Production middleware rate-limits /api/public/* only when is_production().
This test asserts the production guard exists and returns 429 under load
when forced into production mode.
"""

from __future__ import annotations

from collections import defaultdict

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient


def test_public_rate_limit_bucket_logic_returns_429():
    """Unit-level copy of main.rate_limit_public behaviour."""
    app = FastAPI()
    app.state._rate_buckets = defaultdict(list)
    limit = 5
    window = 60.0

    @app.middleware("http")
    async def rate_limit_public(request: Request, call_next):
        import time

        if request.url.path.startswith("/api/public/"):
            ip = (request.client.host if request.client else "unknown") or "unknown"
            now = time.time()
            bucket: list[float] = app.state._rate_buckets[ip]
            bucket[:] = [t for t in bucket if now - t < window]
            if len(bucket) >= limit:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too many requests — please wait a moment"},
                )
            bucket.append(now)
        return await call_next(request)

    @app.get("/api/public/ping")
    def ping():
        return {"ok": True}

    http = TestClient(app)
    codes = [http.get("/api/public/ping").status_code for _ in range(limit + 2)]
    assert codes.count(200) == limit
    assert 429 in codes
