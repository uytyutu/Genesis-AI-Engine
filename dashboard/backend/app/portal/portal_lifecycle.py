"""R3.8.4 — Portal Lifecycle Contract.

Formal states for Portal Read integration (no endpoints · no Auth · no business logic).

Allowed progression (happy path)::

    disabled → registered → active → teardown

Semantics
---------
disabled
    Feature off and registration has never run.
registered
    ``register_portal_read`` has run (``registration_attempted``).
    Does **not** mean success — see ``active``.
active
    Registration mounted the read router (``registration_active``).
teardown
    Read stack handler slot was cleared after use (``teardown_portal_read``).

Derived from ``PortalIntegrationProfile``, ``RegistrationOutcome``, and
``portal_registration_snapshot`` — resolve is read-only except the teardown note.
"""

from __future__ import annotations

from typing import Any, Literal

from app.portal.portal_health import portal_registration_snapshot
from app.portal.portal_profile import is_portal_feature_enabled

ENGINE_ID = "portal_lifecycle_v1"

PortalLifecycleState = Literal["disabled", "registered", "active", "teardown"]

PORTAL_LIFECYCLE_STATES: tuple[PortalLifecycleState, ...] = (
    "disabled",
    "registered",
    "active",
    "teardown",
)

# From → allowed next states (documentation + validation helper)
PORTAL_LIFECYCLE_TRANSITIONS: dict[PortalLifecycleState, tuple[PortalLifecycleState, ...]] = {
    "disabled": ("registered",),
    "registered": ("active", "teardown", "disabled"),
    "active": ("teardown",),
    "teardown": ("disabled", "registered"),
}

_teardown_noted: bool = False


def note_portal_teardown() -> None:
    """Record that teardown ran — does not mount or enable Portal."""
    global _teardown_noted
    _teardown_noted = True


def clear_portal_lifecycle_notes() -> None:
    """Test helper — clears teardown note only."""
    global _teardown_noted
    _teardown_noted = False


def resolve_portal_lifecycle_state() -> PortalLifecycleState:
    """Map current profile/registration/health signals to one lifecycle state."""
    if _teardown_noted:
        return "teardown"
    snap = portal_registration_snapshot()
    if snap["registration_active"]:
        return "active"
    if snap["registration_attempted"]:
        return "registered"
    return "disabled"


def portal_lifecycle_snapshot() -> dict[str, Any]:
    """Contract + current state — no side effects beyond reading health."""
    state = resolve_portal_lifecycle_state()
    health = portal_registration_snapshot()
    return {
        "engine_id": ENGINE_ID,
        "lifecycle_state": state,
        "feature_enabled": is_portal_feature_enabled(),
        "registration_attempted": health["registration_attempted"],
        "registration_active": health["registration_active"],
        "states": list(PORTAL_LIFECYCLE_STATES),
        "transitions": {
            k: list(v) for k, v in PORTAL_LIFECYCLE_TRANSITIONS.items()
        },
    }


def is_transition_allowed(
    current: PortalLifecycleState,
    nxt: PortalLifecycleState,
) -> bool:
    return nxt in PORTAL_LIFECYCLE_TRANSITIONS.get(current, ())
