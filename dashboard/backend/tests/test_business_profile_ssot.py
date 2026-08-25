"""Business Profile SSOT — slice 1 schema + store (Enter once → use everywhere)."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import HTTPException

from app.integration.customer_identity.schema import BusinessProfile
from app.integration.customer_identity.service import CustomerIdentityService
from app.integration.customer_identity.store import CustomerIdentityStore


@pytest.fixture
def svc(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GENESIS_CLIENT_JWT_SECRET", "test-client-secret-bp")
    memory = tmp_path / "memory"
    memory.mkdir()
    return CustomerIdentityService(memory)


def test_ensure_one_profile_per_user(svc: CustomerIdentityService):
    out = svc.register(name="Max", email="max.bp@example.com", password="securepass1")
    cid = svc._store.find_customer_by_email("max.bp@example.com")
    assert cid

    a = svc.ensure_business_profile(cid)
    b = svc.ensure_business_profile(cid)
    assert a["profile_id"] == b["profile_id"]
    assert a["customer_id"] == cid
    assert a.get("contacts", {}).get("email") == "max.bp@example.com"


def test_upsert_persists_factory_fields(svc: CustomerIdentityService, tmp_path: Path):
    svc.register(name="Anna", email="anna.bp@example.com", password="securepass1")
    cid = svc._store.find_customer_by_email("anna.bp@example.com")
    assert cid

    saved = svc.upsert_business_profile(
        cid,
        {
            "company_name": "Berlin Rohrfix",
            "niche": "handwerk",
            "description": "Sanitär und Heizung in Berlin",
            "contacts": {
                "phone": "+493012345",
                "whatsapp": "+491701234567",
                "email": "info@rohrfix.example",
            },
            "address": {
                "city": "Berlin",
                "postal_code": "10115",
                "country": "DE",
                "street": "Musterstr. 1",
            },
            "services": [
                {"name": "Notdienst", "price_hint": "ab 89 €"},
                {"name": "Installation"},
            ],
            "socials": {"instagram": "https://instagram.com/berlinrohr"},
            "language": "de",
            "market": "DE",
        },
        source="giveaway",
    )
    assert saved["company_name"] == "Berlin Rohrfix"
    assert saved["niche"] == "handwerk"
    assert saved["contacts"]["whatsapp"].startswith("+49")
    assert len(saved["services"]) == 2
    assert saved["source"] == "giveaway"

    store = CustomerIdentityStore(tmp_path / "memory")
    loaded = store.load_business_profile_by_customer(cid)
    assert loaded is not None
    assert loaded.company_name == "Berlin Rohrfix"
    assert loaded.address.city == "Berlin"
    assert loaded.services[0].name == "Notdienst"

    card = store.load_card(cid)
    assert card is not None
    assert card.company_display_name == "Berlin Rohrfix"


def test_second_purchase_reuses_same_profile(svc: CustomerIdentityService):
    """Paid path and Giveaway must not create a second company facts entity."""
    svc.register(name="Gift", email="gift.bp@example.com", password="securepass1")
    cid = svc._store.find_customer_by_email("gift.bp@example.com")
    assert cid

    giveaway = svc.upsert_business_profile(
        cid,
        {"company_name": "X Sanitär", "niche": "handwerk"},
        source="giveaway",
    )
    paid = svc.upsert_business_profile(
        cid,
        {"description": "Same shop buys Business later"},
        source="order",
    )
    assert paid["profile_id"] == giveaway["profile_id"]
    assert paid["company_name"] == "X Sanitär"
    assert "Same shop" in paid["description"]
    assert paid["source"] == "order"


def test_from_dict_roundtrip():
    raw = {
        "profile_id": "p1",
        "customer_id": "c1",
        "company_name": "Test GmbH",
        "services": ["A", {"name": "B", "description": "d"}],
        "contacts": {"phone": "1"},
        "unknown_future_field": True,
    }
    profile = BusinessProfile.from_dict(raw)
    assert profile is not None
    assert profile.services[0].name == "A"
    assert profile.services[1].name == "B"
    again = BusinessProfile.from_dict(profile.to_dict())
    assert again is not None
    assert again.company_name == "Test GmbH"


def test_get_missing_customer(svc: CustomerIdentityService):
    with pytest.raises(HTTPException) as exc:
        svc.get_business_profile("no-such-user")
    assert exc.value.status_code == 404
