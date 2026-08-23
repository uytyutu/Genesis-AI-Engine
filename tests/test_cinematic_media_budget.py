"""Cinematic Media Budget — payment gate, enforcement, disabled providers."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.integration.cinematic_media.budget import (
    activate_media_budget_after_payment,
    apply_media_charge,
    attach_cinematic_to_order,
    can_start_media_job,
    order_is_payment_confirmed,
    release_or_refund,
)
from app.integration.cinematic_media.config import client_facing_product, get_product
from app.integration.cinematic_media.providers.kie import KieMediaProvider
from app.integration.cinematic_media.providers.kling import KlingMediaProvider
from app.integration.cinematic_media.router import MediaProviderRouter
from app.integration.cinematic_media.scene_director import build_scene_spec


def _base_order(**kwargs):
    row = {
        "order_id": "ord-test1",
        "status": "awaiting_payment",
        "price_eur": 650.0,
        "symbol": "€",
        "price_label": "650 €",
        "paid_at": None,
        "cinematic_enabled": False,
        "media_status": "NOT_REQUESTED",
        "media_spent_eur": 0.0,
    }
    row.update(kwargs)
    return row


def test_client_catalog_hides_internal_budget() -> None:
    card = client_facing_product()
    assert card["ok"] is True
    assert card["price_eur"] == 99
    assert "media_budget" not in card
    assert "media_budget_eur" not in card
    assert "margin" not in str(card).lower()


def test_product_config_has_internal_budget() -> None:
    p = get_product("cinematic_ai_experience")
    assert p is not None
    assert float(p["media_budget_eur"]) == 40
    assert float(p["price_eur"]) == 99


def test_unpaid_order_cannot_generate() -> None:
    order = attach_cinematic_to_order(_base_order(), enabled=True)
    assert order["media_status"] == "AWAITING_PAYMENT"
    assert order["price_eur"] == 749.0
    gate = can_start_media_job(order, estimated_cost_eur=10)
    assert gate["allow"] is False
    assert gate["error"] == "unpaid_order"


def test_checkout_created_not_payment() -> None:
    order = attach_cinematic_to_order(
        _base_order(status="checkout_created", checkout_session_id="cs_test"),
        enabled=True,
    )
    assert order_is_payment_confirmed(order) is False
    gate = can_start_media_job(order, estimated_cost_eur=5)
    assert gate["allow"] is False


def test_webhook_paid_activates_budget(tmp_path: Path) -> None:
    order = attach_cinematic_to_order(_base_order(), enabled=True)
    order["status"] = "paid"
    order["paid_at"] = "2026-08-09T10:00:00+00:00"
    out = activate_media_budget_after_payment(order, tmp_path)
    assert out["activated"] is True
    assert order["media_status"] == "READY_FOR_GENERATION"
    assert order["media_budget_eur"] == 40
    assert order["media_remaining_eur"] == 40


def test_budget_allows_when_cost_fits(tmp_path: Path) -> None:
    order = attach_cinematic_to_order(_base_order(), enabled=True)
    order["status"] = "paid"
    order["paid_at"] = "2026-08-09T10:00:00+00:00"
    activate_media_budget_after_payment(order, tmp_path)
    gate = can_start_media_job(order, estimated_cost_eur=18)
    assert gate["allow"] is True
    charged = apply_media_charge(
        order, tmp_path, amount_eur=18, provider="kling", capability="IMAGE_TO_VIDEO"
    )
    assert charged["ok"] is True
    assert order["media_spent_eur"] == 18
    assert order["media_remaining_eur"] == 22


def test_budget_blocks_when_cost_exceeds(tmp_path: Path) -> None:
    order = attach_cinematic_to_order(_base_order(), enabled=True)
    order["status"] = "paid"
    order["paid_at"] = "2026-08-09T10:00:00+00:00"
    activate_media_budget_after_payment(order, tmp_path)
    gate = can_start_media_job(order, estimated_cost_eur=95)
    assert gate["allow"] is False
    assert gate["error"] == "budget_exceeded"
    assert order["media_status"] == "BUDGET_EXHAUSTED"


def test_unknown_cost_blocks() -> None:
    order = attach_cinematic_to_order(_base_order(), enabled=True)
    order["status"] = "paid"
    order["paid_at"] = "2026-08-09T10:00:00+00:00"
    order["media_status"] = "READY_FOR_GENERATION"
    order["media_remaining_eur"] = 40
    gate = can_start_media_job(order, estimated_cost_eur=None)
    assert gate["allow"] is False
    assert gate["error"] == "unknown_cost"
    assert order["media_status"] == "MANUAL_REVIEW"


def test_budget_exhaustion_stops(tmp_path: Path) -> None:
    order = attach_cinematic_to_order(_base_order(), enabled=True)
    order["status"] = "paid"
    order["paid_at"] = "2026-08-09T10:00:00+00:00"
    activate_media_budget_after_payment(order, tmp_path)
    apply_media_charge(order, tmp_path, amount_eur=40, provider="kie")
    assert order["media_status"] == "BUDGET_EXHAUSTED"
    gate = can_start_media_job(order, estimated_cost_eur=1)
    assert gate["allow"] is False


def test_media_spend_does_not_claim_stripe_revenue(tmp_path: Path) -> None:
    order = attach_cinematic_to_order(_base_order(), enabled=True)
    order["status"] = "paid"
    order["paid_at"] = "2026-08-09T10:00:00+00:00"
    activate_media_budget_after_payment(order, tmp_path)
    apply_media_charge(order, tmp_path, amount_eur=10, provider="kling")
    ledger = (tmp_path / "media_budget_ledger.jsonl").read_text(encoding="utf-8")
    assert "does not alter Stripe" in ledger or "media_spend_only" in ledger
    # Order stripe fields untouched by media charge
    assert "stripe_actual_revenue" not in order


def test_failed_job_not_paid_revenue() -> None:
    order = attach_cinematic_to_order(_base_order(), enabled=True)
    # Generation request while unpaid fails — no revenue mutation
    router = MediaProviderRouter()
    out = router.submit(
        order,
        provider_id="kling",
        capability="IMAGE_TO_VIDEO",
        estimated_cost_eur=10,
    )
    assert out["ok"] is False
    assert out["network_called"] is False
    assert order.get("counts_toward_revenue") is None


def test_disabled_provider_cannot_network() -> None:
    kling = KlingMediaProvider()
    kie = KieMediaProvider()
    assert kling.enabled() is False
    assert kie.enabled() is False
    res = kling.submit(
        __import__(
            "app.integration.cinematic_media.providers.base", fromlist=["MediaJobRequest"]
        ).MediaJobRequest(
            order_id="ord-x",
            capability="IMAGE_TO_VIDEO",
            estimated_cost_eur=5,
        )
    )
    assert res.network_called is False
    assert res.status == "DISABLED"


def test_no_auto_spend_without_budget(tmp_path: Path) -> None:
    order = _base_order()  # cinematic not attached
    gate = can_start_media_job(order, estimated_cost_eur=1)
    assert gate["allow"] is False
    out = MediaProviderRouter().submit(
        order, provider_id="kie", capability="TEXT_TO_VIDEO", estimated_cost_eur=1
    )
    assert out["network_called"] is False


def test_refund_release(tmp_path: Path) -> None:
    order = attach_cinematic_to_order(_base_order(), enabled=True)
    order["status"] = "paid"
    order["paid_at"] = "2026-08-09T10:00:00+00:00"
    activate_media_budget_after_payment(order, tmp_path)
    apply_media_charge(order, tmp_path, amount_eur=20, provider="kling")
    release_or_refund(order, tmp_path, amount_eur=20, op="RELEASE", provider="kling")
    assert order["media_spent_eur"] == 0
    assert order["media_remaining_eur"] == 40


def test_scene_director_json_only() -> None:
    spec = build_scene_spec(niche="barbershop", business_name="Nord Fade")
    assert spec["scene_type"] == "barbershop"
    assert spec["beats"][0]["scroll"] == 0.0
    assert "no media generated" in spec["note"].lower()
    assert len(spec["shots"]) >= 5
