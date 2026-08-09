"""Dry-run cinematic cost — no live KIE/Kling calls."""

from __future__ import annotations

from app.integration.cinematic_media.budget import (
    activate_media_budget_after_payment,
    attach_cinematic_to_order,
)
from app.integration.cinematic_media.dry_run import dry_run_scene_budget
from app.integration.cinematic_media.scene_director import build_scene_spec


def test_barbershop_scene_has_eight_shots() -> None:
    scene = build_scene_spec(
        niche="barbershop",
        business_name="Nord Fade",
        city="Dresden",
        description="premium men's barber",
        product_kind="shop",
        style="premium",
    )
    assert scene["scene_type"] == "barbershop"
    assert len(scene["shots"]) == 8
    assert scene["shots"][0]["action"] == "camera_enters_shop"
    assert scene["shots"][-1]["action"] == "shop_cta"


def test_dry_run_allow_if_paid_preview() -> None:
    out = dry_run_scene_budget(
        {
            "niche": "barbershop",
            "business_name": "Nord Fade",
            "city": "Dresden",
            "description": "мужская парикмахерская",
            "product_kind": "shop",
            "cinematic_enabled": True,
            "style": "premium",
        }
    )
    assert out["dry_run"] is True
    assert out["network_called"] is False
    assert out["live_job_submitted"] is False
    assert out["cost_estimate"]["ok"] is True
    assert out["cost_estimate"]["estimated_cost_eur"] > 0
    assert out["cost_estimate"]["quote_certainty"] in ("estimate_only", "measured_partial")
    assert out["decision"] in ("ALLOW_IF_PAID", "MANUAL_REVIEW", "ALLOW")
    # Client summary must not expose internal budget
    assert "media_budget_eur" not in out["client_safe_summary"]


def test_dry_run_with_paid_order_allow(tmp_path) -> None:
    order = {
        "order_id": "ord-dry1",
        "status": "awaiting_payment",
        "price_eur": 650.0,
        "symbol": "€",
        "niche": "barbershop",
        "business_name": "Nord Fade",
        "city": "Dresden",
        "description": "premium barber",
        "product_kind": "shop",
    }
    attach_cinematic_to_order(order, enabled=True, is_shop=True)
    order["status"] = "paid"
    order["paid_at"] = "2026-08-09T12:00:00+00:00"
    activate_media_budget_after_payment(order, tmp_path)
    out = dry_run_scene_budget(
        {
            "niche": order["niche"],
            "business_name": order["business_name"],
            "city": order["city"],
            "description": order["description"],
            "product_kind": "shop",
            "cinematic_enabled": True,
        },
        order=order,
    )
    cost = float(out["cost_estimate"]["estimated_cost_eur"])
    assert cost <= float(order["media_budget_eur"])
    assert out["decision"] == "ALLOW"
    assert out["network_called"] is False


def test_dry_run_blocks_without_cinematic() -> None:
    out = dry_run_scene_budget(
        {
            "niche": "barbershop",
            "business_name": "Nord Fade",
            "cinematic_enabled": False,
        }
    )
    assert out["decision"] == "BLOCK"
    assert out["reason"] == "cinematic_not_requested"
