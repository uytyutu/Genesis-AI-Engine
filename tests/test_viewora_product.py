"""Virtus Video AI product SSOT + orchestrator smoke (no live video providers)."""

from __future__ import annotations

from pathlib import Path

from app.integration.viewora.billing import VieworaBilling
from app.integration.viewora.orchestrator import (
    build_package,
    generate_ten,
    hook_lab,
    viral_lab,
    watchability_score,
)
from app.integration.viewora.product import UNIT_COSTS, public_catalog


def test_catalog_brand_and_affordable_plans():
    cat = public_catalog()
    assert cat["name"] == "Virtus Video AI"
    plans = {p["id"]: p for p in cat["plans"]}
    assert plans["free"]["creations"] == 3
    assert plans["creator"]["monthly_eur"] == 12.99
    assert plans["pro"]["monthly_eur"] == 29.99
    assert plans["business"]["monthly_eur"] == 59.99
    assert plans["studio"]["monthly_eur"] == 149.0
    assert len(cat["credit_packs"]) == 4
    assert UNIT_COSTS["short_video"] == 10
    assert UNIT_COSTS["podcast_20"] == 100
    assert cat["credit_costs"]["create"] == 10
    assert cat["credit_costs"]["podcast_shorts"] == 100


def test_orchestrator_hides_models_and_watchability():
    pkg = build_package(brief="Emotional TikTok about a new track", mode="viral")
    assert pkg["orchestrator"]["exposed_models"] is False
    assert pkg["render"]["mp4_available"] is False
    assert len(pkg["hooks"]) >= 5
    score = pkg["watchability"]
    assert score["label"] == "WATCHABILITY"
    assert set(score["scores"]) == {"hook", "pacing", "visual", "emotion", "cta"}
    assert score["overall"] >= 1
    assert watchability_score("x")["label"] == "WATCHABILITY"


def test_generate_10_hooks_and_viral_lab():
    versions = generate_ten("product launch")
    assert len(versions) == 10
    lab = hook_lab("coffee brand")
    assert lab["count"] == 20
    vlab = viral_lab("one upload")
    assert vlab["count"] == 8
    assert vlab["versions"][0]["version_label"].startswith("A")


def test_demo_checkout_and_fulfill(tmp_path: Path):
    billing = VieworaBilling(tmp_path)
    snap = billing.account_snapshot(None)
    aid = snap["account"]["id"]
    out = billing.create_order(
        account_id=aid,
        kind="plan",
        sku="creator",
        email="test@example.com",
        success_url="https://example.com/viewora/success",
        cancel_url="https://example.com/viewora/pricing",
        prefer_demo=True,
    )
    assert out["ok"] is True
    assert out["payment_mode"] == "demo"
    paid = billing.pay_demo(out["order_id"])
    assert paid["ok"] is True
    assert paid["account"]["plan_id"] == "creator"
    assert paid["account"]["credits"] == 120
