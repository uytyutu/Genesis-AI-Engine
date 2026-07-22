"""R3.8.3 — Portal Health Verification.

Read-only diagnostics for Portal registration state.
Does not register · mount · enable · or mutate the application.
"""

from __future__ import annotations

from typing import Any

from app.portal.portal_profile import is_portal_feature_enabled
from app.portal.portal_registration import last_registration_outcome

ENGINE_ID = "portal_health_v1"


def portal_registration_snapshot() -> dict[str, Any]:
    """Diagnostic snapshot of Portal registration — no side effects."""
    outcome = last_registration_outcome()
    attempted = bool(outcome and outcome.attempted)
    active = bool(outcome and outcome.active)
    return {
        "engine_id": ENGINE_ID,
        "feature_enabled": is_portal_feature_enabled(),
        "registration_attempted": attempted,
        "registration_active": active,
    }
