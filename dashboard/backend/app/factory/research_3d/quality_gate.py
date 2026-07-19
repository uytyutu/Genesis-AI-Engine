"""3D visual quality gate — research / future Premium contour.

Rule (CEO feedback): if 3D quality is below the rest of the site, do NOT show the
mesh. Prefer thematic licensed models; otherwise CSS-Motion or photography.

Placeholder meshes from scripts/generate_research_3d_presets.py are for lab
geometry tests only — never client-facing “Premium 3D”.
"""

from __future__ import annotations

from typing import Any, Literal

QualityTier = Literal["placeholder", "approved", "premium"]
VisualMode = Literal["webgl_3d", "css_motion", "photo", "classic"]

# Niches where a random / abstract mesh looks unprofessional to buyers.
PROFESSIONAL_NICHES: frozenset[str] = frozenset(
    {
        "dental",
        "auto",
        "law",
        "energy",
        "handwerk",
        "appliance",
        "computer",
        "beauty",
        "green",
        "generic",
    }
)

QUALITY_POLICY: dict[str, Any] = {
    "version": 1,
    "rule": (
        "If 3D quality is below site quality, use photography or CSS-Motion "
        "instead of a weak model."
    ),
    "tiers": {
        "placeholder": {
            "client_facing_3d": False,
            "lab_ok": True,
            "note": "Procedural / tiny research GLB — not sellable Premium 3D",
        },
        "approved": {
            "client_facing_3d": True,
            "lab_ok": True,
            "note": "Thematic licensed model reviewed for realism",
        },
        "premium": {
            "client_facing_3d": True,
            "lab_ok": True,
            "note": "Studio PBR + HDR interactive — paid Premium contour",
        },
    },
    "commerce": {
        "business": "css_motion_or_photo",
        "premium_3d": "approved_or_premium_mesh_only",
    },
}


def normalize_quality_tier(value: str | None) -> QualityTier:
    raw = str(value or "placeholder").strip().lower()
    if raw in ("approved", "ok", "thematic"):
        return "approved"
    if raw in ("premium", "studio", "premium_3d"):
        return "premium"
    return "placeholder"


def quality_allows_client_3d(tier: str | None) -> bool:
    t = normalize_quality_tier(tier)
    return bool(QUALITY_POLICY["tiers"][t]["client_facing_3d"])


def resolve_visual_mode(
    *,
    niche_id: str | None,
    quality_tier: str | None,
    webgl_ok: bool,
    license_ok: bool,
    budget_ok: bool,
    want_3d: bool = True,
    photo_available: bool = False,
) -> VisualMode:
    """Pick what the client-facing page should render.

    Professional niches never show placeholder meshes as Premium 3D.
    """
    if not want_3d:
        return "photo" if photo_available else "classic"

    tier = normalize_quality_tier(quality_tier)
    niche = str(niche_id or "").strip().lower()
    professional = niche in PROFESSIONAL_NICHES or niche == ""

    if not license_ok:
        return "photo" if photo_available else "classic"

    # Weak mesh + professional niche → never WebGL hero
    if professional and not quality_allows_client_3d(tier):
        if photo_available:
            return "photo"
        return "css_motion"

    if not budget_ok or not webgl_ok:
        if photo_available:
            return "photo"
        return "css_motion"

    if quality_allows_client_3d(tier):
        return "webgl_3d"

    return "photo" if photo_available else "css_motion"
