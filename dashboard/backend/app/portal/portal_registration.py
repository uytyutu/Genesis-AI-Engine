"""R3.8.2 — Controlled Portal Registration.

Uses ``PORTAL_PROFILE.feature_enabled`` as the only enablement switch.

- False → no-op (application behaviour unchanged)
- True  → compose stack via profile providers and mount the read router

No Auth · no Persistence · no business logic.
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI

from app.portal.portal_profile import PORTAL_PROFILE, is_portal_feature_enabled
from app.portal.read_service import PortalCatalogView

ENGINE_ID = "portal_registration_v1"


def register_portal_read(
    app: FastAPI,
    *,
    catalog: PortalCatalogView | None = None,
) -> bool:
    """Mount Portal Read routes iff the integration profile enables them.

    Returns ``True`` when the router was mounted, ``False`` when skipped.
    """
    if not is_portal_feature_enabled():
        return False
    stack = PORTAL_PROFILE.bootstrap_provider(catalog)
    app.include_router(stack.router)
    return True


def registration_status() -> dict[str, Any]:
    return {
        "engine_id": ENGINE_ID,
        "feature_enabled": is_portal_feature_enabled(),
        "would_mount": is_portal_feature_enabled(),
        "decision_point": "PORTAL_PROFILE.feature_enabled",
    }
