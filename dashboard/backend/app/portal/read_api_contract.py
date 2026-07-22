"""R3.7.1 — Portal Read API Contract.

Describes GET /portal/... routes and I/O shapes for a future HTTP layer.
This module is a contract only:

- not mounted on any HTTP app
- no handlers / routers
- no Auth
- no write operations
- not wired to PortalReadService yet

Output shapes reuse Portal View Models (read-only projections).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from app.portal.asset import AssetType
from app.portal.views import (
    AssetView,
    ClientView,
    DeploymentView,
    EditSessionView,
    WebsiteView,
)

ENGINE_ID = "portal_read_api_contract_v1"

HttpMethod = Literal["GET"]


# --- Input models (path / query) — parameters only ---


@dataclass(frozen=True)
class ClientPath:
    client_id: str


@dataclass(frozen=True)
class WebsitePath:
    website_id: str


@dataclass(frozen=True)
class WebsiteAssetsQuery:
    website_id: str
    asset_type: AssetType | None = None


# --- Route contract ---


@dataclass(frozen=True)
class PortalReadRoute:
    """One declared read endpoint — not an HTTP handler."""

    method: HttpMethod
    path: str
    name: str
    summary: str
    path_params: type
    query_params: type | None
    response_model: type
    response_is_list: bool = False


PORTAL_READ_ROUTES: tuple[PortalReadRoute, ...] = (
    PortalReadRoute(
        method="GET",
        path="/portal/clients/{client_id}",
        name="get_client",
        summary="Read Client identity",
        path_params=ClientPath,
        query_params=None,
        response_model=ClientView,
    ),
    PortalReadRoute(
        method="GET",
        path="/portal/websites/{website_id}",
        name="get_website",
        summary="Read Website",
        path_params=WebsitePath,
        query_params=None,
        response_model=WebsiteView,
    ),
    PortalReadRoute(
        method="GET",
        path="/portal/websites/{website_id}/deployment",
        name="get_current_deployment",
        summary="Read current Deployment for Website",
        path_params=WebsitePath,
        query_params=None,
        response_model=DeploymentView,
    ),
    PortalReadRoute(
        method="GET",
        path="/portal/websites/{website_id}/assets",
        name="get_assets",
        summary="List Assets for Website",
        path_params=WebsitePath,
        query_params=WebsiteAssetsQuery,
        response_model=AssetView,
        response_is_list=True,
    ),
    PortalReadRoute(
        method="GET",
        path="/portal/websites/{website_id}/edit-session",
        name="get_open_edit_session",
        summary="Read open EditSession for Website",
        path_params=WebsitePath,
        query_params=None,
        response_model=EditSessionView,
    ),
)


def list_read_paths() -> tuple[str, ...]:
    return tuple(r.path for r in PORTAL_READ_ROUTES)


def route_by_name(name: str) -> PortalReadRoute | None:
    for route in PORTAL_READ_ROUTES:
        if route.name == name:
            return route
    return None


def contract_as_dict() -> dict[str, Any]:
    """Machine-readable contract snapshot (docs / future OpenAPI seed)."""
    return {
        "engine_id": ENGINE_ID,
        "mounted": False,
        "auth": False,
        "methods": ["GET"],
        "routes": [
            {
                "method": r.method,
                "path": r.path,
                "name": r.name,
                "summary": r.summary,
                "response_model": r.response_model.__name__,
                "response_is_list": r.response_is_list,
            }
            for r in PORTAL_READ_ROUTES
        ],
    }
