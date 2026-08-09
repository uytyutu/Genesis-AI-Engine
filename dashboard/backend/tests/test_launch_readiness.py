"""Launch Readiness + Success Path + Sales Focus + First Value Time."""

from __future__ import annotations

import json
from pathlib import Path

from app.integration.launch_readiness import (
    build_business_kpis,
    build_first_value_time,
    build_launch_readiness,
    build_sales_focus,
    build_time_to_launch,
)
from app.integration.platform_global_analytics import (
    build_global_analytics,
    build_platform_funnel,
)


def test_launch_readiness_core_green_launch_pending(tmp_path: Path):
    out = build_launch_readiness(tmp_path)
    assert out["title"] == "Launch Readiness"
    assert out["phase"] == "feature_freeze"
    by_id = {i["id"]: i for i in out["items"]}
    assert by_id["architecture"]["status"] == "done"
    assert by_id["visual_engine"]["status"] == "done"
    assert by_id["performance"]["status"] == "pending"
    assert by_id["launch_ready"]["status"] == "pending"
    assert out["next"]["id"] == "performance"


def test_launch_ready_when_overrides_complete(tmp_path: Path):
    (tmp_path / "launch_readiness.json").write_text(
        json.dumps(
            {
                "performance": {"status": "done", "detail": "Lighthouse 95+"},
                "beta_feedback": {"status": "done", "beta_clients": 6},
                "documentation": {"status": "done"},
                "golden_website_test": {
                    "status": "pass",
                    "guest_checkout": "pass",
                    "verification_email": "pass",
                    "pricing_ssot": "pass",
                    "production_build": "pass",
                },
            }
        ),
        encoding="utf-8",
    )
    out = build_launch_readiness(tmp_path)
    assert all(i["status"] == "done" for i in out["items"])
    assert out["pct"] == 100
    assert out["ads_allowed"] is True


def test_golden_website_blocks_ads_until_pass(tmp_path: Path):
    out = build_launch_readiness(tmp_path)
    assert out["ads_allowed"] is False
    assert out["website_launch"] == "BLOCKED"
    by_id = {i["id"]: i for i in out["items"]}
    assert by_id["golden_website_test"]["status"] == "pending"
    gwt = out["golden_website_test"]
    assert gwt["status"] in {"FAIL", "PARTIAL", "FUNCTIONAL_PASS"}
    assert gwt.get("functional_status") == "PASS" or gwt.get("logic_status") == "PASS"
    assert gwt.get("performance_status") == "OPEN"
    assert "PASS" in str(gwt.get("infrastructure_status") or "")
    assert len(gwt["blockers"]) >= 4
    assert len(gwt.get("launch_blockers") or []) == 8
    assert gwt["launch_blockers"][0]["id"] == "golden_website_test"
    assert gwt["ads_allowed"] is False
    assert {b["id"] for b in gwt["launch_blockers"]} >= {
        "golden_website_test",
        "visual_quality_gate",
        "social_integration_gate",
        "commercial_ux_gate",
        "demo_gallery",
        "preview_website",
        "brand_audit",
        "golden_store_test",
    }


def test_success_path_seven_stages(tmp_path: Path):
    out = build_business_kpis(tmp_path)
    assert out["title"] == "Success Path"
    assert out["primary_kpi"] == "successful_full_path_clients"
    assert out["total"] == 7
    assert out["done"] == 0
    assert out["next"]["id"] == "first_website_sold"
    ids = [i["id"] for i in out["items"]]
    assert ids == [
        "first_website_sold",
        "first_store_sold",
        "first_shop_order",
        "first_email_sent",
        "first_shipment",
        "first_positive_review",
        "first_repeat_client",
    ]


def test_sales_focus_first_five(tmp_path: Path):
    sales = tmp_path / "sales_orders"
    sales.mkdir()
    for i, niche in enumerate(["restaurant", "beauty", "auto"]):
        (sales / f"c{i}.json").write_text(
            json.dumps(
                {
                    "order_id": f"c{i}",
                    "client_id": f"client-{i}",
                    "status": "paid",
                    "paid_at": "2026-08-06T10:00:00+00:00",
                    "niche": niche,
                    "package_name": "Website Business",
                }
            ),
            encoding="utf-8",
        )
    out = build_sales_focus(tmp_path)
    assert out["title"] == "First 5 Clients"
    assert out["goal"] == 5
    assert out["count"] == 3
    assert out["remaining"] == 2
    assert out["path"][0] == "Sales"
    assert all(c["beta"] is True for c in out["clients"])


def test_first_value_time_median(tmp_path: Path):
    sales = tmp_path / "sales_orders"
    sales.mkdir()
    (sales / "a.json").write_text(
        json.dumps(
            {
                "order_id": "a",
                "status": "published",
                "paid_at": "2026-08-06T10:00:00+00:00",
                "published_at": "2026-08-06T10:20:00+00:00",
            }
        ),
        encoding="utf-8",
    )
    (sales / "b.json").write_text(
        json.dumps(
            {
                "order_id": "b",
                "status": "paid",
                "paid_at": "2026-08-06T11:00:00+00:00",
                "first_lead_at": "2026-08-06T11:40:00+00:00",
            }
        ),
        encoding="utf-8",
    )
    fvt = build_first_value_time(tmp_path)
    assert fvt["title"] == "First Value Time"
    assert fvt["goal_min"] == 60
    assert fvt["median_min"] == 40.0
    assert fvt["on_goal"] is True
    assert fvt["by_kind"]["published"] == 1
    assert fvt["by_kind"]["first_lead"] == 1


def test_time_to_launch_goals_and_median(tmp_path: Path):
    sales = tmp_path / "sales_orders"
    sales.mkdir()
    (sales / "o1.json").write_text(
        json.dumps(
            {
                "order_id": "o1",
                "status": "published",
                "paid_at": "2026-08-06T10:00:00+00:00",
                "published_at": "2026-08-06T10:18:00+00:00",
                "package_name": "Website Business",
            }
        ),
        encoding="utf-8",
    )
    (sales / "o2.json").write_text(
        json.dumps(
            {
                "order_id": "o2",
                "status": "published",
                "product_kind": "ai_store",
                "paid_at": "2026-08-06T11:00:00+00:00",
                "published_at": "2026-08-06T11:45:00+00:00",
            }
        ),
        encoding="utf-8",
    )
    ttl = build_time_to_launch(tmp_path)
    assert ttl["goals"]["website_min"] == 30
    assert ttl["goals"]["store_min"] == 60
    assert ttl["website"]["median_min"] == 18.0
    assert ttl["website"]["on_goal"] is True
    assert ttl["store"]["median_min"] == 45.0
    assert ttl["store"]["on_goal"] is True


def test_funnel_drop_and_global_snapshot(tmp_path: Path):
    (tmp_path / "platform_funnel.json").write_text(
        json.dumps(
            {
                "counts": {
                    "visitors": 100,
                    "leads": 40,
                    "payment": 20,
                    "factory": 18,
                    "published": 15,
                }
            }
        ),
        encoding="utf-8",
    )
    funnel = build_platform_funnel(tmp_path)
    assert funnel["title"] == "Daily Funnel"
    assert funnel["biggest_drop"] is not None
    assert funnel["biggest_drop"]["lost_pct"] >= 40
    snap = build_global_analytics(tmp_path)
    assert snap["time_to_launch"]["ok"] is True
    assert snap["first_value_time"]["ok"] is True
    assert snap["sales_focus"]["goal"] == 5
    assert snap["business_kpis"]["primary_kpi"] == "successful_full_path_clients"
