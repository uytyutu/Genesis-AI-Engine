"""HTTP façade for Farm public runtimes (/api/farm/runtime/{slug}/...)."""

from __future__ import annotations

from typing import Any

from fastapi import Request, Response
from fastapi.responses import JSONResponse

from swarm.farm_channels.rapidapi.runtime_handlers import handle_runtime, health_payload


async def dispatch_runtime(slug: str, request: Request, subpath: str = "") -> Response:
    method = request.method.upper()
    path = "/" + (subpath or "").lstrip("/")
    if path == "//" or path == "/":
        path = "/health" if method == "GET" else path
    query = {k: str(v) for k, v in request.query_params.multi_items()}
    body: Any = None
    if method in ("POST", "PUT", "PATCH"):
        try:
            body = await request.json()
        except Exception:
            body = None
    status, payload = handle_runtime(slug, method=method, path=path, query=query, body=body)
    return JSONResponse(payload, status_code=status)


def runtime_index() -> dict[str, Any]:
    from swarm.farm_channels.rapidapi.markets import coverage_summary
    from swarm.farm_channels.rapidapi.runtime_handlers import SUPPORTED_SLUGS

    return {
        "ok": True,
        "channel": "api_farm_runtime",
        "supported_slugs": sorted(SUPPORTED_SLUGS),
        "health": {s: health_payload(s) for s in sorted(SUPPORTED_SLUGS)},
        "markets": coverage_summary(),
    }
