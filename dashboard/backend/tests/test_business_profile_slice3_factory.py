"""Business Profile SSOT Slice 3 — Factory consume adapter."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.integration.customer_identity.factory_profile_adapter import (
    SSOT_MARKER,
    apply_business_profile_to_contacts,
    profile_dict_to_interview,
)
from app.integration.customer_identity.service import CustomerIdentityService
from app.integration.customer_identity.store import CustomerIdentityStore


@pytest.fixture
def mem(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("GENESIS_CLIENT_JWT_SECRET", "test-bp-slice3-secret")
    memory = tmp_path / "memory"
    memory.mkdir()
    return memory


def _seed_handwerk_profile(mem: Path) -> tuple[str, dict]:
    svc = CustomerIdentityService(mem)
    svc.register(
        name="B3 Review Gate",
        email="b3-slice3-handwerk@virtuscore-test.example",
        password="securepass1",
        locale="de",
        country="DE",
    )
    cid = svc._store.find_customer_by_email("b3-slice3-handwerk@virtuscore-test.example")
    assert cid
    profile = svc.upsert_business_profile(
        cid,
        {
            "company_name": "B3 Review Handwerk Berlin",
            "niche": "auto",
            "description": (
                "B3 Review Handwerk Berlin — Sanitär und Heizung, Meisterbetrieb. "
                "Notdienst, Badrenovierung, Heizungswartung."
            ),
            "contacts": {
                "phone": "+493012345678",
                "whatsapp": "+491701112233",
                "email": "kontakt@b3-handwerk-berlin.example",
            },
            "address": {
                "street": "Handwerkerweg 12",
                "city": "Berlin",
                "postal_code": "10115",
                "country": "DE",
            },
            "services": [
                {"name": "Notdienst", "price_hint": "ab 89 €"},
                {"name": "Badrenovierung", "description": "Komplettsanierung"},
                {"name": "Heizungswartung"},
            ],
            "socials": {"instagram": "https://instagram.com/b3handwerk"},
            "language": "de",
            "market": "DE",
        },
        source="order",
    )
    return cid, profile


def test_adapter_maps_profile_fields():
    profile = {
        "profile_id": "p1",
        "customer_id": "c1",
        "company_name": "B3 Review Handwerk Berlin",
        "niche": "handwerk",
        "description": "Meisterbetrieb",
        "contacts": {"phone": "+49", "whatsapp": "+4917", "email": "a@b.de"},
        "address": {"city": "Berlin", "street": "Weg 1"},
        "services": [{"name": "Notdienst"}, {"name": "Heizung"}],
        "language": "de",
        "market": "DE",
    }
    iv = profile_dict_to_interview(profile)
    assert iv["company_name"] == "B3 Review Handwerk Berlin"
    assert iv["city"] == "Berlin"
    assert iv["top_services"] == ["Notdienst", "Heizung"]
    assert iv["source"] == "business_profile_ssot"
    assert iv["ssot"] == SSOT_MARKER


def test_profile_wins_over_order_contacts(mem: Path):
    cid, _ = _seed_handwerk_profile(mem)
    contacts = {
        "customer_id": cid,
        "business_name": "WRONG ORDER NAME",
        "phone": "000",
        "city": "München",
        "business_interview": {
            "company_name": "Legacy Interview Co",
            "about": "should be replaced",
            "source": "form",
        },
    }
    merged = apply_business_profile_to_contacts(contacts, memory_dir=mem, customer_id=cid)
    assert merged["business_name"] == "B3 Review Handwerk Berlin"
    assert merged["phone"] == "+493012345678"
    assert merged["city"] == "Berlin"
    assert merged["business_interview"]["company_name"] == "B3 Review Handwerk Berlin"
    assert merged["business_interview"]["source"] == "business_profile_ssot"
    assert merged["_business_profile_ssot"]["applied"] is True
    # Still one profile on disk
    store = CustomerIdentityStore(mem)
    again = store.load_business_profile_by_customer(cid)
    assert again is not None
    assert again.profile_id == merged["_business_profile_ssot"]["profile_id"]


def test_missing_profile_does_not_invent(mem: Path):
    svc = CustomerIdentityService(mem)
    svc.register(name="No Profile", email="noprof@example.com", password="securepass1")
    cid = svc._store.find_customer_by_email("noprof@example.com")
    assert cid
    merged = apply_business_profile_to_contacts(
        {"customer_id": cid, "business_name": "Order Only GmbH"},
        memory_dir=mem,
        customer_id=cid,
    )
    assert merged["business_name"] == "Order Only GmbH"
    assert merged["_business_profile_ssot"]["applied"] is False
    assert merged["_business_profile_ssot"]["reason"] == "profile_missing"


def test_factory_contacts_path_uses_profile_not_order_copy(mem: Path):
    """End-to-end contact chain Factory uses — without full media/HTML pipeline."""
    from app.factory.business_interview import interview_from_payload, interview_to_contacts

    cid, profile = _seed_handwerk_profile(mem)
    contacts = {
        "customer_id": cid,
        "business_name": "SHOULD_NOT_WIN",
        "phone": "000",
        "city": "München",
        "package_id": "basic",
        "business_interview": {
            "company_name": "Legacy Order Interview",
            "about": "order copy",
            "source": "form",
        },
    }
    contacts = apply_business_profile_to_contacts(
        contacts, memory_dir=mem, customer_id=cid
    )
    assert contacts["_business_profile_ssot"]["applied"] is True
    assert contacts["business_name"] == "B3 Review Handwerk Berlin"
    interview = interview_from_payload(contacts["business_interview"])
    contacts = interview_to_contacts(interview, contacts)
    assert contacts["business_name"] == "B3 Review Handwerk Berlin"
    assert "Notdienst" in (contacts.get("services_list") or [])
    assert contacts.get("_business_profile_ssot", {}).get("applied") is True
    assert contacts["business_interview"].get("source") in (
        "business_profile_ssot",
        "form",
        "hybrid",
        "dialogue",
    )
    # Provenance marker may be re-stamped in FactoryService after interview_to_contacts
    assert contacts["_business_profile_ssot"]["ssot"] == SSOT_MARKER
    # Changing order-shaped leftovers must not recreate a second profile
    store = CustomerIdentityStore(mem)
    before = store.load_business_profile_by_customer(cid)
    contacts["business_name"] = "HACKED ORDER NAME"
    contacts2 = apply_business_profile_to_contacts(
        contacts, memory_dir=mem, customer_id=cid
    )
    assert contacts2["business_name"] == "B3 Review Handwerk Berlin"
    after = store.load_business_profile_by_customer(cid)
    assert before is not None and after is not None
    assert before.profile_id == after.profile_id == profile["profile_id"]
