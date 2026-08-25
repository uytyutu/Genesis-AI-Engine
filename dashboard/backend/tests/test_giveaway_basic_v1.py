"""Giveaway Basic v1 — unique link, 0€ entitlement, one redeem, Profile SSOT."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.integration.customer_identity.service import CustomerIdentityService
from app.integration.giveaway import DEFAULT_CODE, GiveawayService, ORIGINAL_BASIC_EUR


@pytest.fixture
def memory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("GENESIS_CLIENT_JWT_SECRET", "test-giveaway-secret")
    mem = tmp_path / "memory"
    mem.mkdir()
    return mem


def _register_with_profile(memory: Path, email: str, company: str) -> str:
    identity = CustomerIdentityService(memory)
    identity.register(name="Gewinner", email=email, password="securepass1")
    cid = identity._store.find_customer_by_email(email)
    assert cid
    identity.upsert_business_profile(
        cid,
        {
            "company_name": company,
            "niche": "handwerk",
            "description": "Testfirma für Giveaway",
            "contacts": {"phone": "+4930111", "email": email},
            "address": {"city": "Berlin", "country": "DE"},
            "services": [{"name": "Service A"}],
            "language": "de",
            "market": "DE",
        },
        source="giveaway",
    )
    return cid


def test_default_stream_code_available(memory: Path):
    svc = GiveawayService(memory)
    status = svc.public_status(DEFAULT_CODE)
    assert status["ok"] is True
    assert status["available"] is True
    assert status["price_eur"] == 0.0
    assert status["original_value_eur"] == ORIGINAL_BASIC_EUR


def test_redeem_creates_zero_euro_giveaway_order(memory: Path):
    cid = _register_with_profile(memory, "winner1@example.com", "Gewinner GmbH")
    svc = GiveawayService(memory)
    out = svc.redeem(DEFAULT_CODE, customer_id=cid)
    assert out["ok"] is True
    assert out["need_profile"] is False
    assert out["price_eur"] == 0.0
    assert out["original_value_eur"] == ORIGINAL_BASIC_EUR
    assert out["entitlement_type"] == "giveaway"
    assert out["payment_status"] == "not_required"
    order_id = out["order_id"]
    assert order_id

    from app.factory.factory_service import FactoryService
    from app.integration.factory_intent_service import FactoryIntentService
    from app.integration.sales_order_service import SalesOrderService

    factory = FactoryService(memory_dir=memory)
    intent = FactoryIntentService(memory_dir=memory, factory=factory)
    sales = SalesOrderService(memory, intent)
    order = sales.get_order(order_id)
    assert order is not None
    assert float(order["price_eur"]) == 0.0
    assert order["entitlement_type"] == "giveaway"
    assert order["payment_mode"] == "giveaway"
    assert order["payment_status"] == "not_required"
    assert order.get("demo") is False
    assert order.get("is_demo") is False
    assert order["business_name"] == "Gewinner GmbH"
    assert order["customer_id"] == cid
    assert order["status"] in ("paid", "in_production", "ready")
    assert order.get("package_id") == "basic"


def test_second_redeem_same_code_fails(memory: Path):
    cid1 = _register_with_profile(memory, "w1@example.com", "Firma Eins")
    cid2 = _register_with_profile(memory, "w2@example.com", "Firma Zwei")
    svc = GiveawayService(memory)
    first = svc.redeem(DEFAULT_CODE, customer_id=cid1)
    assert first["ok"] is True
    with pytest.raises(ValueError, match="code_exhausted"):
        svc.redeem(DEFAULT_CODE, customer_id=cid2)
    status = svc.public_status(DEFAULT_CODE)
    assert status["available"] is False


def test_same_customer_cannot_double_redeem(memory: Path):
    cid = _register_with_profile(memory, "once@example.com", "Once GmbH")
    svc = GiveawayService(memory)
    code = svc.create_code(code="extra-basic-1", max_redeems=1)["code"]
    assert svc.redeem(code, customer_id=cid)["ok"] is True
    other = svc.create_code(code="extra-basic-2", max_redeems=1)["code"]
    with pytest.raises(ValueError, match="already_redeemed"):
        svc.redeem(other, customer_id=cid)


def test_need_profile_before_redeem(memory: Path):
    identity = CustomerIdentityService(memory)
    identity.register(name="Empty", email="empty@example.com", password="securepass1")
    cid = identity._store.find_customer_by_email("empty@example.com")
    assert cid
    svc = GiveawayService(memory)
    out = svc.redeem(DEFAULT_CODE, customer_id=cid)
    assert out["ok"] is False
    assert out["need_profile"] is True
    assert "/client/business-profile" in out["next"]


def test_owner_card_marks_giveaway(memory: Path):
    cid = _register_with_profile(memory, "owner-see@example.com", "Owner Sicht GmbH")
    svc = GiveawayService(memory)
    out = svc.redeem(DEFAULT_CODE, customer_id=cid)
    assert out["ok"] is True

    from app.integration.customer_identity.support_center import SupportCenterService

    card = SupportCenterService(memory).build_client_card(cid)
    assert card is not None
    websites = card.get("websites") or []
    assert any(w.get("is_giveaway") for w in websites) or any(
        (p.get("is_giveaway") for p in (card.get("products") or []))
    )
    payments = (card.get("finance") or {}).get("payments") or []
    assert any(p.get("is_giveaway") or p.get("entitlement_type") == "giveaway" for p in payments)
