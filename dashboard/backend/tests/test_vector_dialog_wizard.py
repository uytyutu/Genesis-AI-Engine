"""Vector Phase 2 — dialog wizard + business setup + honesty rules."""

from __future__ import annotations

from app.integration.store_admin.commerce_settings import default_commerce_settings
from app.integration.store_admin.design_service import default_design
from app.integration.store_admin.setup_status import build_setup_status
from app.integration.vector.business_setup import build_business_setup
from app.integration.vector.capabilities import action_for, is_live
from app.integration.vector.dialog_wizard import (
    build_platform_dialog,
    build_store_dialog,
)


def test_honesty_live_stripe():
    assert is_live("payments_stripe") is True
    action = action_for("payments_stripe")
    assert action["kind"] == "navigate_section"
    assert action["section"] == "payments"


def test_honesty_shipping_live():
    assert is_live("shipping_carriers") is True
    assert action_for("shipping_carriers")["kind"] == "navigate_section"
    assert action_for("shipping_carriers")["section"] == "shipping"


def test_honesty_live_products():
    action = action_for("store_products", cta_override="Open Products")
    assert action["kind"] == "navigate_section"
    assert action["section"] == "products"
    assert action["label"] == "Open Products"


def test_store_dialog_learning_gate():
    setup = build_setup_status(
        order_id="o1",
        product_count=0,
        design=default_design(),
        commerce_settings=default_commerce_settings(),
    )
    gate = build_store_dialog(setup, learning_mode=None)
    assert gate["mode"] == "learning_gate"
    assert any(a["kind"] == "set_learning" for a in gate["actions"])


def test_store_dialog_logo_step():
    setup = build_setup_status(
        order_id="o1",
        product_count=0,
        design=default_design(),
        commerce_settings=default_commerce_settings(),
    )
    dialog = build_store_dialog(setup, learning_mode="skip", step_id="logo")
    assert dialog["mode"] == "dialog_wizard"
    assert "logo" in dialog["messages"][0]["text"].lower()
    assert any(a.get("section") == "design" for a in dialog["actions"])


def test_store_dialog_stripe_connect_live():
    design = default_design()
    design["branding"]["logo"] = {"id": "x"}
    design["colors"]["primary"] = "#111111"
    setup = build_setup_status(
        order_id="o1",
        product_count=12,
        design=design,
        commerce_settings=default_commerce_settings(),
        shop_pipeline="published",
    )
    dialog = build_store_dialog(setup, learning_mode="skip", step_id="stripe")
    text = " ".join(m["text"] for m in dialog["messages"]).lower()
    assert "stripe" in text
    assert any(
        a.get("kind") == "navigate_section" and a.get("section") == "payments"
        for a in dialog["actions"]
    )


def test_business_setup_progress():
    biz = build_business_setup(
        has_website=True,
        has_store=True,
        product_count=5,
        branding_done=True,
        primary_store_order_id="shop-1",
    )
    assert biz["pct"] > 0
    payments = next(i for i in biz["items"] if i["id"] == "payments")
    assert payments["actionable"] is True
    assert payments.get("coming") is None
    shipping = next(i for i in biz["items"] if i["id"] == "shipping")
    assert shipping["actionable"] is True
    assert biz["next"] is not None


def test_platform_dialog_with_store():
    biz = build_business_setup(has_store=True, primary_store_order_id="s1")
    dialog = build_platform_dialog(
        has_store=True,
        store_order_id="s1",
        store_name="Demo Shop",
        has_website=False,
        business_setup=biz,
    )
    assert dialog["surface"] == "platform"
    assert any(a.get("kind") == "navigate_href" for a in dialog["actions"])
    href = next(a["href"] for a in dialog["actions"] if a.get("href"))
    assert "/client/stores/s1/admin" in href
