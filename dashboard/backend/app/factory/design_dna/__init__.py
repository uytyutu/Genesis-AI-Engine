"""Design DNA Engine — impression before structure (Digital Creative Studio)."""

from __future__ import annotations

from app.factory.design_dna.art_director import (
    STUDIO_ID,
    StudioDirection,
    run_digital_creative_studio,
)
from app.factory.design_dna.composition_library import (
    COMPOSITION_LIBRARY,
    compositions_for_niche,
    get_composition,
    is_predictable_funnel,
    list_compositions,
)
from app.factory.design_dna.dna import DesignDNA
from app.factory.design_dna.brand_book import BrandBook, apply_brand_book_to_dna, resolve_brand_book
from app.factory.design_dna.quality_floor import (
    atmosphere_html,
    experience_js,
    quality_floor_css,
    store_quality_floor_css,
    validate_quality_floor_html,
)
from app.factory.design_dna.resolve import resolve_design_dna
from app.factory.design_dna.rhythm import DEFAULT_SECTION_KEYS, plan_section_rhythm
from app.factory.design_dna.studio_acceptance import (
    OWNER_PASS_PHRASE,
    build_pending_report,
    print_demo_links,
    write_studio_acceptance,
)
from app.factory.design_dna.visual_benchmark import (
    QUALITY_FLOORS,
    get_visual_benchmark,
    quality_floor_for,
    require_visual_benchmark,
)

__all__ = [
    "BrandBook",
    "COMPOSITION_LIBRARY",
    "DEFAULT_SECTION_KEYS",
    "DesignDNA",
    "OWNER_PASS_PHRASE",
    "QUALITY_FLOORS",
    "STUDIO_ID",
    "StudioDirection",
    "apply_brand_book_to_dna",
    "atmosphere_html",
    "build_pending_report",
    "compositions_for_niche",
    "experience_js",
    "get_composition",
    "get_visual_benchmark",
    "is_predictable_funnel",
    "list_compositions",
    "plan_section_rhythm",
    "print_demo_links",
    "quality_floor_css",
    "quality_floor_for",
    "require_visual_benchmark",
    "resolve_brand_book",
    "resolve_design_dna",
    "run_digital_creative_studio",
    "store_quality_floor_css",
    "validate_quality_floor_html",
    "write_studio_acceptance",
]
