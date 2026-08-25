"""Business Profile SSOT Slice 4 — Workspace write-back."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.integration.customer_identity.profile_writeback import (
    profile_to_website_contacts,
    website_contacts_to_profile_patch,
    writeback_website_contacts,
)
from app.integration.customer_identity.service import CustomerIdentityService
from app.integration.customer_identity.store import CustomerIdentityStore
from app.main import app


@pytest.fixture
def mem(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("GENESIS_CLIENT_JWT_SECRET", "test-bp-slice4-secret")
    memory = tmp_path / "memory"
    memory.mkdir()
    return memory


def test_website_contacts_patch_mapping():
    patch = website_contacts_to_profile_patch(
        {
            "phone": "+49111",
            "whatsapp": "+49222",
            "email": "a@b.de",
            "city": "Berlin",
            "address": "Weg 1",
        }
    )
    assert patch["contacts"]["phone"] == "+49111"
    assert patch["address"]["city"] == "Berlin"
    assert patch["address"]["street"] == "Weg 1"
    back = profile_to_website_contacts(
        {
            "contacts": {"phone": "+49111", "email": "a@b.de"},
            "address": {"city": "Berlin", "street": "Weg 1"},
        }
    )
    assert back["phone"] == "+49111"
    assert back["city"] == "Berlin"
    assert back["address"] == "Weg 1"


def test_settings_upsert_is_ssot(mem: Path):
    svc = CustomerIdentityService(mem)
    svc.register(name="Owner", email="slice4@example.com", password="securepass1")
    cid = svc._store.find_customer_by_email("slice4@example.com")
    assert cid
    a = svc.upsert_business_profile(
        cid,
        {"company_name": "Müller Handwerk", "contacts": {"phone": "+49001"}},
        source="workspace",
    )
    b = svc.upsert_business_profile(
        cid,
        {"contacts": {"phone": "+49999"}},
        source="workspace",
    )
    assert a["profile_id"] == b["profile_id"]
    assert b["company_name"] == "Müller Handwerk"
    assert b["contacts"]["phone"] == "+49999"


def test_website_kontakte_writeback_same_profile(mem: Path):
    svc = CustomerIdentityService(mem)
    svc.register(name="WC", email="wc4@example.com", password="securepass1")
    cid = svc._store.find_customer_by_email("wc4@example.com")
    assert cid
    first = svc.upsert_business_profile(
        cid,
        {
            "company_name": "B3 Review Handwerk Berlin",
            "contacts": {"phone": "+493000"},
        },
        source="order",
    )
    wb = writeback_website_contacts(
        memory_dir=mem,
        customer_id=cid,
        contacts={"phone": "+493012345678", "email": "neu@example.com", "city": "Berlin"},
        company_name="Müller Handwerk",
    )
    assert wb is not None
    assert wb["profile_id"] == first["profile_id"]
    assert wb["company_name"] == "Müller Handwerk"
    assert wb["contacts"]["phone"] == "+493012345678"
    assert wb["contacts"]["email"] == "neu@example.com"
    assert wb["address"]["city"] == "Berlin"
    store = CustomerIdentityStore(mem)
    loaded = store.load_business_profile_by_customer(cid)
    assert loaded is not None
    assert loaded.profile_id == first["profile_id"]
    assert loaded.company_name == "Müller Handwerk"


def test_client_profile_put_route_registered():
    routes = {getattr(r, "path", None) for r in app.routes}
    assert "/api/client/business-profile" in routes
