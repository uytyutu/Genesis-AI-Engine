"""Business Profile SSOT — slice 2 API + Owner/Client read."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.integration.customer_identity.service import CustomerIdentityService
from app.integration.customer_identity.support_center import SupportCenterService
from app.main import app


@pytest.fixture
def mem(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GENESIS_CLIENT_JWT_SECRET", "test-client-secret-bp2")
    memory = tmp_path / "memory"
    memory.mkdir()
    monkeypatch.setenv("GENESIS_MEMORY_DIR", str(memory))
    return memory


def test_business_profile_read_honest_empty(mem: Path):
    svc = CustomerIdentityService(mem)
    out = svc.register(name="Empty", email="empty.bp2@example.com", password="securepass1")
    cid = svc._store.find_customer_by_email("empty.bp2@example.com")
    assert cid
    payload = svc.business_profile_read(cid)
    assert payload["ok"] is True
    assert payload["has_profile"] is False
    assert payload["profile"] is None
    assert "not filled" in (payload.get("note") or "").lower() or "not" in (
        payload.get("note") or ""
    ).lower()


def test_owner_card_includes_business_profile(mem: Path):
    svc = CustomerIdentityService(mem)
    svc.register(name="Owner View", email="owner.bp2@example.com", password="securepass1")
    cid = svc._store.find_customer_by_email("owner.bp2@example.com")
    assert cid
    svc.upsert_business_profile(
        cid,
        {
            "company_name": "Rohr Berlin",
            "niche": "handwerk",
            "contacts": {"whatsapp": "+49170"},
            "services": [{"name": "Notdienst"}],
        },
        source="order",
    )
    card = SupportCenterService(mem).build_client_card(cid)
    assert card is not None
    bp = card["business_profile"]
    assert bp["has_profile"] is True
    assert bp["profile"]["company_name"] == "Rohr Berlin"
    assert bp["profile"]["services"][0]["name"] == "Notdienst"


def test_owner_and_client_http_read(mem: Path, monkeypatch: pytest.MonkeyPatch):
    # Point app memory at tmp if main uses env — otherwise skip deep app wiring
    monkeypatch.setenv("GENESIS_CLIENT_JWT_SECRET", "test-client-secret-bp2")
    svc = CustomerIdentityService(mem)
    reg = svc.register(name="Http", email="http.bp2@example.com", password="securepass1")
    cid = svc._store.find_customer_by_email("http.bp2@example.com")
    assert cid
    token = str(reg.get("token") or "")
    assert token

    # Direct service path already covered; HTTP uses live memory_dir from process.
    # Assert dedicated payload helpers remain stable for API contract.
    empty = svc.business_profile_read(cid)
    assert empty["has_profile"] is False
    svc.upsert_business_profile(cid, {"company_name": "HTTP Co"}, source="workspace")
    filled = svc.business_profile_read(cid)
    assert filled["has_profile"] is True
    assert filled["profile"]["company_name"] == "HTTP Co"
    assert filled["ssot"] == "customer_identity.business_profile"

    # Route registration smoke (no auth on owner path in local MC)
    routes = {getattr(r, "path", None) for r in app.routes}
    assert "/api/client/business-profile" in routes
    assert "/api/owner/users/{customer_id}/business-profile" in routes

    # Client route requires auth
    http = TestClient(app)
    denied = http.get("/api/client/business-profile")
    assert denied.status_code in (401, 403)


def test_me_includes_business_profile_block(mem: Path):
    svc = CustomerIdentityService(mem)
    svc.register(name="Me", email="me.bp2@example.com", password="securepass1")
    cid = svc._store.find_customer_by_email("me.bp2@example.com")
    assert cid
    me = svc.me(cid)
    assert "business_profile" in me
    assert me["business_profile"]["has_profile"] is False
    svc.upsert_business_profile(cid, {"company_name": "Me GmbH", "niche": "dental"})
    me2 = svc.me(cid)
    assert me2["business_profile"]["has_profile"] is True
    assert me2["business_profile"]["profile"]["niche"] == "dental"
