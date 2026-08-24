"""B4.1 — Auth + Client Context tenant isolation (no LLM / research / ACTION)."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import FastAPI, HTTPException, Request
from fastapi.testclient import TestClient

from app.factory.factory_service import FactoryService
from app.integration.customer_identity.auth import issue_client_token, require_client
from app.integration.customer_identity.b3_review_fixture import (
    B3_REVIEW_COMPANY,
    seed_b3_empty_client,
    seed_b3_review_client,
)
from app.integration.factory_intent_service import FactoryIntentService
from app.integration.sales_order_service import SalesOrderService
from app.integration.vector.companion_context import (
    B4_1_SLICE,
    COMPANION_CONTEXT_PATH,
    CompanionContextService,
    enforce_tenant,
)
from app.integration.vector.companion_contracts import (
    B4_ENGINE,
    CONTEXT_ENGINE_REQUIRED,
)


@pytest.fixture()
def mem(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    monkeypatch.setenv("GENESIS_PAYMENT_SANDBOX", "1")
    monkeypatch.setenv("GENESIS_ALLOW_DEMO_PAYMENT", "1")
    monkeypatch.setenv("GENESIS_SMTP_MOCK", "1")
    monkeypatch.setenv("GENESIS_CLIENT_JWT_SECRET", "b3-review-gate-jwt-secret-32chars!!")
    root = tmp_path / "memory"
    root.mkdir()
    return root


def _sales(memory: Path) -> SalesOrderService:
    factory = FactoryService(memory_dir=memory, sandbox_dir=memory / "sandbox")
    intent = FactoryIntentService(memory_dir=memory, factory=factory)
    return SalesOrderService(memory, intent)


def test_enforce_tenant_allows_match_or_absent():
    enforce_tenant(auth_customer_id="cus_a", requested_customer_id=None)
    enforce_tenant(auth_customer_id="cus_a", requested_customer_id="cus_a")
    enforce_tenant(auth_customer_id="cus_a", requested_customer_id="  cus_a  ")


def test_enforce_tenant_rejects_foreign_id():
    with pytest.raises(HTTPException) as ei:
        enforce_tenant(auth_customer_id="cus_a", requested_customer_id="cus_b")
    assert ei.value.status_code == 403
    assert ei.value.detail == "tenant_mismatch"


def test_load_binds_auth_customer_context(mem: Path):
    fx = seed_b3_review_client(mem)
    sales = _sales(mem)
    svc = CompanionContextService(mem, sales=sales)
    out = svc.load_for_session(
        auth_customer_id=fx.customer_id,
        auth_email=fx.email,
        me={"company_display_name": fx.business_name, "email": fx.email},
        page_path="/client/analytics",
    )
    assert out["ok"] is True
    assert out["engine"] == B4_ENGINE
    assert out["slice"] == B4_1_SLICE
    assert out["customer_id"] == fx.customer_id
    assert out["location"] == "analytics"
    assert out["llm"] is False
    assert out["research"] is False
    assert out["action"] is False
    assert out["modes_enabled"] == ["context_read"]
    ctx = out["context"]
    assert ctx["engine"] == CONTEXT_ENGINE_REQUIRED
    assert ctx["business"]["company_name"] == B3_REVIEW_COMPANY
    assert ctx["products"]["website"]["owned"] is True
    assert out["context_ref"]["engine"] == CONTEXT_ENGINE_REQUIRED


def test_foreign_customer_id_query_denied(mem: Path):
    owner = seed_b3_review_client(mem)
    stranger = seed_b3_empty_client(mem)
    sales = _sales(mem)
    svc = CompanionContextService(mem, sales=sales)

    with pytest.raises(HTTPException) as ei:
        svc.load_for_session(
            auth_customer_id=owner.customer_id,
            auth_email=owner.email,
            me={"company_display_name": owner.business_name, "email": owner.email},
            requested_customer_id=stranger.customer_id,
        )
    assert ei.value.status_code == 403


def test_stranger_session_cannot_see_owner_business(mem: Path):
    owner = seed_b3_review_client(mem)
    stranger = seed_b3_empty_client(mem)
    sales = _sales(mem)
    svc = CompanionContextService(mem, sales=sales)

    owner_out = svc.load_for_session(
        auth_customer_id=owner.customer_id,
        auth_email=owner.email,
        me={"company_display_name": owner.business_name, "email": owner.email},
    )
    stranger_out = svc.load_for_session(
        auth_customer_id=stranger.customer_id,
        auth_email=stranger.email,
        me={"company_display_name": "Empty GmbH", "email": stranger.email},
    )

    assert owner_out["customer_id"] == owner.customer_id
    assert stranger_out["customer_id"] == stranger.customer_id
    assert owner_out["context"]["business"]["company_name"] == B3_REVIEW_COMPANY
    assert stranger_out["context"]["business"]["company_name"] != B3_REVIEW_COMPANY
    # Empty client must not inherit owner's owned website flag
    assert stranger_out["context"]["products"].get("website", {}).get("owned") is not True


def test_http_companion_context_auth_and_tenant(mem: Path, monkeypatch: pytest.MonkeyPatch):
    """Mini-app mirrors B4.1 route: bearer → auth sub → Context; spoof → 403."""
    monkeypatch.setenv("GENESIS_CLIENT_JWT_SECRET", "b3-review-gate-jwt-secret-32chars!!")
    owner = seed_b3_review_client(mem)
    stranger = seed_b3_empty_client(mem)
    sales = _sales(mem)
    svc = CompanionContextService(mem, sales=sales)

    app = FastAPI()

    @app.get(COMPANION_CONTEXT_PATH)
    def route(
        request: Request,
        period: str = "30d",
        page_path: str | None = None,
        customer_id: str | None = None,
    ):
        payload = require_client(request)
        auth_id = str(payload["sub"])
        email = str(payload.get("email") or "") or None
        return svc.load_for_session(
            auth_customer_id=auth_id,
            auth_email=email,
            me={"company_display_name": owner.business_name if auth_id == owner.customer_id else "Empty GmbH",
                "email": email},
            period=period,
            page_path=page_path,
            requested_customer_id=customer_id,
        )

    http = TestClient(app)

    # No token → 401
    assert http.get(COMPANION_CONTEXT_PATH).status_code == 401

    # Owner token → own context
    r = http.get(
        COMPANION_CONTEXT_PATH,
        headers={"Authorization": f"Bearer {owner.token}"},
        params={"page_path": "/client"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["customer_id"] == owner.customer_id
    assert body["context"]["business"]["company_name"] == B3_REVIEW_COMPANY
    assert body["llm"] is False

    # Owner tries stranger id in query → 403
    bad = http.get(
        COMPANION_CONTEXT_PATH,
        headers={"Authorization": f"Bearer {owner.token}"},
        params={"customer_id": stranger.customer_id},
    )
    assert bad.status_code == 403
    assert bad.json()["detail"] == "tenant_mismatch"

    # Stranger token cannot obtain owner company even with matching self id
    s = http.get(
        COMPANION_CONTEXT_PATH,
        headers={"Authorization": f"Bearer {stranger.token}"},
        params={"customer_id": stranger.customer_id},
    )
    assert s.status_code == 200
    assert s.json()["customer_id"] == stranger.customer_id
    assert s.json()["context"]["business"]["company_name"] != B3_REVIEW_COMPANY

    # Forged token for stranger sub still cannot pass owner as requested
    # (already covered); additionally: stranger requesting owner id → 403
    steal = http.get(
        COMPANION_CONTEXT_PATH,
        headers={"Authorization": f"Bearer {stranger.token}"},
        params={"customer_id": owner.customer_id},
    )
    assert steal.status_code == 403


def test_issue_token_sub_is_only_tenant_key(mem: Path):
    fx = seed_b3_review_client(mem)
    token = issue_client_token(customer_id=fx.customer_id, email=fx.email)
    assert token
    # Path constant stable for FE mirror
    assert COMPANION_CONTEXT_PATH == "/api/client/vector/companion-context"
