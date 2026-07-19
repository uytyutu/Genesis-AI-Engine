"""Research-only 3D/WebGL workshop — NEVER imported by Path A checkout/Factory production.

Gates: license CREDITS, .glb budget, WebGL→CSS fallback spec.
Runtime experiments live under dashboard/backend/_research_3d/ (artifacts gitignored).
"""

from __future__ import annotations

from app.factory.research_3d.fallback_spec import FALLBACK_SPEC, resolve_delivery_mode
from app.factory.research_3d.glb_budget import check_glb_budget, DEFAULT_MAX_GLB_BYTES
from app.factory.research_3d.license_gate import check_asset_license, LicenseGateResult
from app.factory.research_3d.niche_catalog import list_niche_slots, list_market_slots

__all__ = [
    "FALLBACK_SPEC",
    "DEFAULT_MAX_GLB_BYTES",
    "LicenseGateResult",
    "check_asset_license",
    "check_glb_budget",
    "list_market_slots",
    "list_niche_slots",
    "resolve_delivery_mode",
]
