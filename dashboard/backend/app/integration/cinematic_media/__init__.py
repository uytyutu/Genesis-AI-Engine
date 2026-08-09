"""Cinematic media façade for orders / admin / future Scene Engine."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.integration.cinematic_media.budget import (
    activate_media_budget_after_payment,
    admin_media_view,
    apply_media_charge,
    attach_cinematic_to_order,
    can_start_media_job,
    release_or_refund,
)
from app.integration.cinematic_media.config import client_facing_product, list_products
from app.integration.cinematic_media.dry_run import dry_run_scene_budget
from app.integration.cinematic_media.router import MediaProviderRouter
from app.integration.cinematic_media.scene_director import build_scene_spec


def public_catalog(*, lang: str = "de") -> dict[str, Any]:
    return {
        "ok": True,
        "product": client_facing_product(lang=lang),
        "internal_products_count": len(list_products()),
    }


def provider_board() -> dict[str, Any]:
    return MediaProviderRouter().board()


def on_order_paid(order: dict[str, Any], memory_dir: Path) -> dict[str, Any]:
    return activate_media_budget_after_payment(order, memory_dir)


def request_generation(
    order: dict[str, Any],
    memory_dir: Path,
    *,
    provider_id: str = "kie",
    capability: str = "IMAGE_TO_VIDEO",
    estimated_cost_eur: float | None = None,
    prompt: str = "",
) -> dict[str, Any]:
    """Future entrypoint — currently always blocked from live network."""
    router = MediaProviderRouter()
    scene = build_scene_spec(
        niche=str(order.get("niche") or ""),
        business_name=str(order.get("business_name") or ""),
        product_kind=str(order.get("product_kind") or "website"),
        city=str(order.get("city") or ""),
        description=str(order.get("description") or ""),
    )
    out = router.submit(
        order,
        provider_id=provider_id,
        capability=capability,
        prompt=prompt or scene.get("scene_type", ""),
        estimated_cost_eur=estimated_cost_eur,
        memory_dir=memory_dir,
    )
    out["scene_spec"] = scene
    return out


__all__ = [
    "admin_media_view",
    "apply_media_charge",
    "attach_cinematic_to_order",
    "build_scene_spec",
    "can_start_media_job",
    "dry_run_scene_budget",
    "on_order_paid",
    "provider_board",
    "public_catalog",
    "release_or_refund",
    "request_generation",
]
