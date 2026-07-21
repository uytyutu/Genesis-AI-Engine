"""Path A funnel aggregates + adaptive VXP preview."""

from __future__ import annotations

from pathlib import Path


def test_path_a_funnel_summary(tmp_path: Path):
    from app.integration.pricing_display_service import PricingDisplayService

    svc = PricingDisplayService(memory_dir=tmp_path)
    svc.log_event(event="tier_page_view", tier_id=None, page="site", meta={})
    svc.log_event(event="tier_select", tier_id="business", page="order", meta={"niche": "dental"})
    svc.log_event(
        event="premium_preview_view",
        tier_id="premium",
        page="order",
        meta={"niche": "dental", "product_id": "implant"},
    )
    svc.log_event(event="upgrade_click", tier_id="premium", page="order", meta={})
    svc.log_event(
        event="checkout_start",
        tier_id="premium",
        page="order",
        meta={"order_id": "ord-test"},
    )
    svc.log_event(
        event="checkout_paid",
        tier_id="premium",
        page="order_status",
        meta={"order_id": "ord-test"},
    )
    svc.log_event(
        event="vxp_product_shown",
        tier_id="business",
        page="order",
        meta={"niche": "dental", "product_id": "implant"},
    )
    svc.log_event(
        event="specialization_selected",
        tier_id=None,
        page="order",
        meta={"niche": "dental", "specialization_id": "implantology"},
    )

    summary = svc.path_a_funnel_summary()
    assert summary["steps"][0]["count"] >= 1
    totals = summary["event_totals"]
    assert totals["tier_page_view"] == 1
    assert totals["checkout_paid"] == 1
    assert totals["upgrade_click"] == 1
    assert any(n["id"] == "dental" for n in summary["top_niches"])
    assert any(p["id"] == "implant" for p in summary["top_products"])


def test_order_experience_funnel_a21(tmp_path: Path):
    """A2.1 — Order Experience funnel aggregates on existing Path A analytics."""
    from app.integration.pricing_display_service import PricingDisplayService
    from app.schemas import PathAFunnelDashboard

    svc = PricingDisplayService(memory_dir=tmp_path)
    for ev in (
        "order_started",
        "step_1_completed",
        "step_2_completed",
        "step_3_completed",
        "step_4_completed",
        "draft_restored",
        "checkout_summary_viewed",
        "checkout_confirmed",
        "stripe_redirect_started",
        "stripe_return_success",
        "order_completed",
    ):
        svc.log_event(
            event=ev,
            tier_id="business",
            page="order",
            meta={"order_id": "ord-oe", "mode": "order_experience_v2"},
        )
    svc.log_event(
        event="stripe_return_cancel",
        tier_id="business",
        page="order_status",
        meta={"order_id": "ord-cancel"},
    )

    summary = svc.path_a_funnel_summary()
    oe = summary["order_experience_funnel"]
    assert oe["title_ru"] == "Order Experience Funnel"
    assert oe["steps"][0]["id"] == "order_started"
    assert oe["steps"][0]["count"] == 1
    assert oe["steps"][-1]["id"] == "order_completed"
    assert oe["steps"][-1]["count"] == 1
    assert oe["event_totals"]["draft_restored"] == 1
    assert oe["event_totals"]["stripe_return_cancel"] == 1
    assert summary["event_totals"]["order_started"] == 1

    # Nested block must validate for Money Monitor / public Path A API
    dash = PathAFunnelDashboard(**summary)
    assert dash.order_experience_funnel is not None
    assert dash.order_experience_funnel.steps[0].count == 1


def test_path_a_visual_preview_adaptive_law():
    from app.integration.path_a_visual_preview import resolve_path_a_visual_preview

    law = resolve_path_a_visual_preview(niche_id="law", tier="premium")
    assert law["ok"] is True
    assert law["mode"] in ("preview", "css_motion", "none")
    assert law["mode"] != "interactive_3d"
    assert law.get("adaptive") is True

    dental = resolve_path_a_visual_preview(
        niche_id="dental",
        tier="business",
        specialization="implantology",
    )
    assert dental["ok"] is True
    assert dental["mode"] in ("preview", "css_motion")
    assert dental.get("product_id")
    assert dental.get("never_empty") is True

    basic = resolve_path_a_visual_preview(niche_id="dental", tier="basic")
    assert basic["mode"] == "none"
