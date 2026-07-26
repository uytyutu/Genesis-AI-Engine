"""Internal Module Policy — TikTok Horizon is Owner-only forever unless flag changes.

visibility = INTERNAL_OWNER means:
  - not Products / Services / public site / Client Workspace / order forms / marketplace
  - not public API
  - Owner Mission Control only
"""

from __future__ import annotations

from typing import Any

from modules.tiktok_factory.gate import load_features

VISIBILITY_INTERNAL_OWNER = "INTERNAL_OWNER"

# Paths that must never surface Horizon as a customer product
FORBIDDEN_PUBLIC_SURFACES = (
    "products",
    "services",
    "site",
    "client",
    "order",
    "marketplace",
    "public_api",
)


def visibility_policy() -> dict[str, Any]:
    features = load_features()
    horizon = features.get("tiktok_horizon") if isinstance(features.get("tiktok_horizon"), dict) else {}
    visibility = str(
        horizon.get("visibility")
        or features.get("tiktok_horizon_visibility")
        or VISIBILITY_INTERNAL_OWNER
    ).strip()
    owner_internal_only = horizon.get("owner_internal_only")
    if owner_internal_only is None:
        owner_internal_only = visibility == VISIBILITY_INTERNAL_OWNER
    else:
        owner_internal_only = bool(owner_internal_only)

    return {
        "visibility": visibility,
        "owner_internal_only": bool(owner_internal_only),
        "allowed_roles": ["owner"],
        "denied_roles": ["admin", "client", "public"],
        "forbidden_surfaces": list(FORBIDDEN_PUBLIC_SURFACES),
        "note_ru": (
            "TikTok Horizon — внутренний модуль владельца. "
            "Не коммерческий продукт. Не показывается клиентам и на /site."
        ),
    }


def assert_owner_internal_access() -> None:
    """Hard gate: refuse if someone flips visibility without an intentional architecture decision."""
    policy = visibility_policy()
    if not policy["owner_internal_only"]:
        # Still Owner-API only in practice; flag must stay INTERNAL_OWNER for Stage 2.
        raise RuntimeError("horizon_visibility_not_internal")
    if policy["visibility"] != VISIBILITY_INTERNAL_OWNER:
        raise RuntimeError("horizon_visibility_not_internal")


def is_commercial_surface_forbidden(surface: str) -> bool:
    s = (surface or "").strip().lower()
    return s in FORBIDDEN_PUBLIC_SURFACES or any(s.startswith(f) for f in FORBIDDEN_PUBLIC_SURFACES)
