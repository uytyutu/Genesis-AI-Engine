"""R3.8.1 — Portal Integration Profile.

Declares how Portal would attach to the app — without mounting it.

- feature_enabled defaults to False (Portal inactive)
- router_provider / bootstrap_provider expose integration points
- no Auth · no Persistence · no business logic · main.py untouched
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from fastapi import APIRouter

from app.portal.portal_bootstrap import (
    PortalReadStack,
    compose_portal_read,
    teardown_portal_read,
)
from app.portal.portal_read_router import portal_read_router
from app.portal.read_service import PortalCatalogView

ENGINE_ID = "portal_profile_v1"


@dataclass(frozen=True)
class PortalIntegrationProfile:
    """Integration knobs for a future main.py mount (not applied here)."""

    feature_enabled: bool
    router_provider: Callable[[], APIRouter]
    bootstrap_provider: Callable[..., PortalReadStack]
    teardown: Callable[[], None]
    notes: str = ""


def _provide_router() -> APIRouter:
    return portal_read_router


def _provide_bootstrap(
    catalog: PortalCatalogView | None = None,
    *,
    wire_router: bool = True,
) -> PortalReadStack:
    return compose_portal_read(catalog, wire_router=wire_router)


PORTAL_PROFILE = PortalIntegrationProfile(
    feature_enabled=False,
    router_provider=_provide_router,
    bootstrap_provider=_provide_bootstrap,
    teardown=teardown_portal_read,
    notes=(
        "Portal Read stack is composed via portal_bootstrap only. "
        "Mount portal_read_router in main.py only when feature_enabled is True "
        "and FastAPI DI replaces the temporary handler setter."
    ),
)


def is_portal_feature_enabled() -> bool:
    return PORTAL_PROFILE.feature_enabled


def portal_profile_snapshot() -> dict[str, Any]:
    return {
        "engine_id": ENGINE_ID,
        "feature_enabled": PORTAL_PROFILE.feature_enabled,
        "router": "portal_read_router",
        "bootstrap": "compose_portal_read",
        "mounted_in_app": False,
        "auth": False,
    }
