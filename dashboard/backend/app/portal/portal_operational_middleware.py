"""OR1 — Bind request_id for /portal HTTP requests."""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from app.portal.operational_context import (
    HEADER_REQUEST_ID,
    clear_request_id,
    ensure_request_id,
)
from app.portal.operational_log import emit_ops_event

ENGINE_ID = "portal_operational_middleware_v1"


class PortalOperationalMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if not request.url.path.startswith("/portal"):
            return await call_next(request)
        incoming = request.headers.get(HEADER_REQUEST_ID)
        request_id = ensure_request_id(incoming)
        request.state.request_id = request_id
        try:
            response = await call_next(request)
            response.headers[HEADER_REQUEST_ID] = request_id
            return response
        except Exception:
            emit_ops_event(
                operation="http_request",
                status="error",
                level="error",
                error="unhandled",
                path=request.url.path,
                method=request.method,
            )
            raise
        finally:
            clear_request_id()


def register_portal_operational_middleware(app: ASGIApp) -> bool:
    app.add_middleware(PortalOperationalMiddleware)  # type: ignore[attr-defined]
    return True
