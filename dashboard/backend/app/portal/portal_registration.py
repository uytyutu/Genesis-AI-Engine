"""R3.8.2 — Controlled Portal Registration.

Uses ``PORTAL_PROFILE.feature_enabled`` as the only enablement switch.

- False → no-op (application behaviour unchanged)
- True  → compose stack via profile providers and mount the read router

Records last outcome for diagnostics (R3.8.3) without re-running registration.
No Auth · no Persistence · no business logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fastapi import FastAPI

from app.portal.portal_profile import PORTAL_PROFILE, is_portal_feature_enabled
from app.portal.read_service import PortalCatalogView

ENGINE_ID = "portal_registration_v1"


@dataclass(frozen=True)
class RegistrationOutcome:
    """Last register_portal_read result — not an HTTP/API type."""

    attempted: bool
    active: bool


_last_outcome: RegistrationOutcome | None = None


def last_registration_outcome() -> RegistrationOutcome | None:
    return _last_outcome


def clear_registration_outcome() -> None:
    """Test helper — does not unmount routes or change feature flag."""
    global _last_outcome
    _last_outcome = None


def register_portal_read(
    app: FastAPI,
    *,
    catalog: PortalCatalogView | None = None,
) -> bool:
    """Mount Portal Read routes iff the integration profile enables them.

    Returns ``True`` when the router was mounted, ``False`` when skipped.
    """
    global _last_outcome
    if not is_portal_feature_enabled():
        _last_outcome = RegistrationOutcome(attempted=True, active=False)
        return False
    stack = PORTAL_PROFILE.bootstrap_provider(catalog)
    app.include_router(stack.router)
    _last_outcome = RegistrationOutcome(attempted=True, active=True)
    return True


def registration_status() -> dict[str, Any]:
    return {
        "engine_id": ENGINE_ID,
        "feature_enabled": is_portal_feature_enabled(),
        "would_mount": is_portal_feature_enabled(),
        "decision_point": "PORTAL_PROFILE.feature_enabled",
    }
