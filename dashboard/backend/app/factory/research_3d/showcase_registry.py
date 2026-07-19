"""Back-compat shim — Visual Experience Engine lives in visual_experience_registry.

Prefer:
  from app.factory.research_3d.visual_experience_registry import (
      resolve_visual_experience,
      build_visual_experience_config,
  )

Disk library path remains showcases/ (data folder, not product brand).
"""

from __future__ import annotations

from app.factory.research_3d.visual_experience_registry import (  # noqa: F401
    ENGINE_ID,
    ENGINE_LABEL,
    NICHE_ALIASES,
    NicheCatalog,
    ProductEntry,
    ShowcaseEntry,
    ShowcaseScene,
    build_showcase_embed_config,
    build_visual_experience_config,
    canonicalize_niche,
    ensure_product_tree_example,
    library_root,
    list_niche_products,
    list_showcase_niches,
    load_library_manifest,
    load_showcase_index,
    load_specialization_map,
    pick_product,
    pick_scene,
    rebuild_library_manifest,
    resolve_niche_catalog,
    resolve_showcase,
    resolve_showcase_delivery,
    resolve_specialization_profile,
    resolve_visual_experience,
    score_product,
    showcase_root,
)

__all__ = [
    "ENGINE_ID",
    "ENGINE_LABEL",
    "NICHE_ALIASES",
    "NicheCatalog",
    "ProductEntry",
    "ShowcaseEntry",
    "ShowcaseScene",
    "build_showcase_embed_config",
    "build_visual_experience_config",
    "canonicalize_niche",
    "ensure_product_tree_example",
    "library_root",
    "list_niche_products",
    "list_showcase_niches",
    "load_library_manifest",
    "load_showcase_index",
    "load_specialization_map",
    "pick_product",
    "pick_scene",
    "rebuild_library_manifest",
    "resolve_niche_catalog",
    "resolve_showcase",
    "resolve_showcase_delivery",
    "resolve_specialization_profile",
    "resolve_visual_experience",
    "score_product",
    "showcase_root",
]
