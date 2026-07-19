"""Research-only 3D/WebGL workshop — NEVER imported by Path A checkout/Factory production.

Gates: license CREDITS, .glb budget, WebGL→CSS fallback spec.
Runtime experiments live under dashboard/backend/_research_3d/ (artifacts gitignored).

Visual Experience Engine (Product Registry): visual_experience_registry.py
Disk library path: _research_3d/showcases/ (data folder, not product brand).
"""

from __future__ import annotations

from app.factory.research_3d.fallback_spec import FALLBACK_SPEC, resolve_delivery_mode
from app.factory.research_3d.glb_budget import check_glb_budget, DEFAULT_MAX_GLB_BYTES
from app.factory.research_3d.license_gate import check_asset_license, LicenseGateResult
from app.factory.research_3d.niche_catalog import list_niche_slots, list_market_slots
from app.factory.research_3d.niche_showcase import (
    load_niche_showcase,
    resolve_package_visual_tier,
    showcase_for_niche,
)
from app.factory.research_3d.quality_gate import (
    QUALITY_POLICY,
    normalize_quality_tier,
    quality_allows_client_3d,
    resolve_visual_mode,
)
from app.factory.research_3d.showcase_registry import (
    ENGINE_ID,
    ENGINE_LABEL,
    NICHE_ALIASES,
    NicheCatalog,
    ProductEntry,
    build_showcase_embed_config,
    build_visual_experience_config,
    canonicalize_niche,
    list_niche_products,
    list_showcase_niches,
    load_library_manifest,
    pick_product,
    pick_scene,
    rebuild_library_manifest,
    resolve_niche_catalog,
    resolve_showcase,
    resolve_showcase_delivery,
    resolve_visual_experience,
    score_product,
)

__all__ = [
    "ENGINE_ID",
    "ENGINE_LABEL",
    "NICHE_ALIASES",
    "FALLBACK_SPEC",
    "QUALITY_POLICY",
    "DEFAULT_MAX_GLB_BYTES",
    "LicenseGateResult",
    "NicheCatalog",
    "ProductEntry",
    "build_showcase_embed_config",
    "build_visual_experience_config",
    "canonicalize_niche",
    "check_asset_license",
    "check_glb_budget",
    "list_market_slots",
    "list_niche_products",
    "list_niche_slots",
    "list_showcase_niches",
    "load_library_manifest",
    "load_niche_showcase",
    "normalize_quality_tier",
    "pick_product",
    "pick_scene",
    "quality_allows_client_3d",
    "rebuild_library_manifest",
    "resolve_delivery_mode",
    "resolve_niche_catalog",
    "resolve_package_visual_tier",
    "resolve_showcase",
    "resolve_showcase_delivery",
    "resolve_visual_experience",
    "resolve_visual_mode",
    "score_product",
    "showcase_for_niche",
]
