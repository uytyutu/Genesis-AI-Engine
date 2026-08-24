"""B4.2 — READ Business Companion (context-grounded conversation)."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import FastAPI, HTTPException, Request
from fastapi.testclient import TestClient

from app.factory.factory_service import FactoryService
from app.integration.customer_identity.auth import require_client
from app.integration.customer_identity.b3_review_fixture import (
    B3_REVIEW_COMPANY,
    seed_b3_empty_client,
    seed_b3_review_client,
)
from app.integration.factory_intent_service import FactoryIntentService
from app.integration.sales_order_service import SalesOrderService
from app.integration.vector.companion_read import (
    B4_2_SLICE,
    COMPANION_TURN_PATH,
    CompanionReadService,
    compose_read_reply,
    detect_read_intent,
    snapshot_from_context,
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


def _read_svc(mem: Path) -> CompanionReadService:
    return CompanionReadService(mem, sales=_sales(mem), llm_enabled=False)


def test_detect_read_intents():
    assert detect_read_intent("__welcome__") == "welcome"
    assert detect_read_intent("Что у меня сейчас подключено?") == "connected"
    assert detect_read_intent("Was ist bei mir verbunden?") == "connected"
    assert detect_read_intent("Warum brauche ich Analytics?") == "analytics"
    assert detect_read_intent("Was soll ich als Nächstes tun?") == "next_steps"
    assert detect_read_intent("Tell me about quantum physics") == "unknown"


def test_real_context_connected_reply_ru(mem: Path):
    fx = seed_b3_review_client(mem)
    svc = _read_svc(mem)
    out = svc.turn(
        auth_customer_id=fx.customer_id,
        auth_email=fx.email,
        me={"company_display_name": fx.business_name, "email": fx.email},
        message="Что у меня сейчас подключено?",
    )
    assert out["ok"] is True
    assert out["slice"] == B4_2_SLICE
    assert out["mode"] == "read"
    assert out["action"] is False
    assert out["research"] is False
    assert out["llm_used"] is False
    reply = out["reply"]
    assert "Website" in reply or "Сайт" in reply
    assert "актив" in reply.lower() or "Актив" in reply
    assert "Besucher" not in reply or "выдум" in reply.lower() or "не подключ" in reply.lower()


def test_empty_context_no_fake_products(mem: Path):
    fx = seed_b3_empty_client(mem)
    svc = _read_svc(mem)
    out = svc.turn(
        auth_customer_id=fx.customer_id,
        auth_email=fx.email,
        me={"company_display_name": "Mein Unternehmen", "email": fx.email},
        message="Was ist verbunden?",
    )
    reply = out["reply"]
    assert B3_REVIEW_COMPANY not in reply
    assert "aktiv" in reply.lower() or "keine" in reply.lower() or "нет" in reply.lower() or "No active" in reply


def test_analytics_not_connected_honest_de(mem: Path):
    fx = seed_b3_review_client(mem)
    svc = _read_svc(mem)
    out = svc.turn(
        auth_customer_id=fx.customer_id,
        auth_email=fx.email,
        me={"company_display_name": fx.business_name, "email": fx.email},
        message="Warum brauche ich Analytics?",
    )
    reply = out["reply"]
    assert out["read_intent"] == "analytics"
    assert "Besucher" in reply or "Kennzahlen" in reply or "Analytics" in reply
    # Must not invent visitor counts
    assert "1.000" not in reply
    assert "1000" not in reply


def test_unknown_question_clarifies(mem: Path):
    fx = seed_b3_review_client(mem)
    svc = _read_svc(mem)
    out = svc.turn(
        auth_customer_id=fx.customer_id,
        auth_email=fx.email,
        me={"company_display_name": fx.business_name, "email": fx.email},
        message="Was ist der Sinn des Lebens?",
    )
    assert out["read_intent"] == "unknown"
    assert out["clarify_question"]
    assert "Context" in out["reply"] or "Virtus" in out["reply"]


def test_multilingual_german_vs_russian(mem: Path):
    fx = seed_b3_review_client(mem)
    svc = _read_svc(mem)
    de = svc.turn(
        auth_customer_id=fx.customer_id,
        auth_email=fx.email,
        me={"company_display_name": fx.business_name, "email": fx.email},
        message="Was ist verbunden?",
    )
    ru = svc.turn(
        auth_customer_id=fx.customer_id,
        auth_email=fx.email,
        me={"company_display_name": fx.business_name, "email": fx.email},
        message="Что подключено?",
    )
    assert "Aktiv" in de["reply"] or "aktiv" in de["reply"]
    assert "Актив" in ru["reply"] or "актив" in ru["reply"].lower()


def test_welcome_proactive_de(mem: Path):
    fx = seed_b3_review_client(mem)
    svc = _read_svc(mem)
    out = svc.turn(
        auth_customer_id=fx.customer_id,
        auth_email=fx.email,
        me={"company_display_name": fx.business_name, "email": fx.email},
        message="__welcome__",
        page_path="/client",
    )
    reply = out["reply"]
    assert "Vector" in reply or "Business Assistant" in reply
    assert B3_REVIEW_COMPANY in reply or fx.business_name in reply
    assert "Analytics" in reply


def test_tenant_isolation_turn_endpoint(mem: Path):
    owner = seed_b3_review_client(mem)
    stranger = seed_b3_empty_client(mem)
    svc = CompanionReadService(mem, sales=_sales(mem), llm_enabled=False)

    app = FastAPI()

    @app.post(COMPANION_TURN_PATH)
    def route(request: Request, body: dict):
        payload = require_client(request)
        auth_id = str(payload["sub"])
        email = str(payload.get("email") or "") or None
        return svc.turn(
            auth_customer_id=auth_id,
            auth_email=email,
            me={"company_display_name": owner.business_name if auth_id == owner.customer_id else "Empty", "email": email},
            message=str((body or {}).get("message") or ""),
            page_path=str((body or {}).get("page_path") or "") or None,
            requested_customer_id=str((body or {}).get("customer_id") or "") or None,
        )

    http = TestClient(app)
    assert http.post(COMPANION_TURN_PATH, json={"message": "test"}).status_code == 401

    owner_r = http.post(
        COMPANION_TURN_PATH,
        headers={"Authorization": f"Bearer {owner.token}"},
        json={"message": "Was ist verbunden?"},
    )
    assert owner_r.status_code == 200
    owner_reply = owner_r.json()["reply"]
    assert "Website" in owner_reply
    assert "Aktiv" in owner_reply or "aktiv" in owner_reply

    steal = http.post(
        COMPANION_TURN_PATH,
        headers={"Authorization": f"Bearer {stranger.token}"},
        json={"message": "Was ist verbunden?", "customer_id": owner.customer_id},
    )
    assert steal.status_code == 403

    stranger_r = http.post(
        COMPANION_TURN_PATH,
        headers={"Authorization": f"Bearer {stranger.token}"},
        json={"message": "Was ist verbunden?"},
    )
    assert stranger_r.status_code == 200
    assert B3_REVIEW_COMPANY not in stranger_r.json()["reply"]


def test_next_steps_from_context(mem: Path):
    fx = seed_b3_review_client(mem)
    svc = _read_svc(mem)
    out = svc.turn(
        auth_customer_id=fx.customer_id,
        auth_email=fx.email,
        me={"company_display_name": fx.business_name, "email": fx.email},
        message="Was soll ich als Nächstes für mein Business tun?",
    )
    assert out["read_intent"] == "next_steps"
    reply = out["reply"]
    assert "Analytics" in reply or "Shop" in reply or "AI" in reply


def test_snapshot_from_context_structure(mem: Path):
    fx = seed_b3_review_client(mem)
    from app.integration.client_analytics import ClientAnalyticsService

    ctx = ClientAnalyticsService(mem, sales=_sales(mem)).client_context(
        customer_id=fx.customer_id,
        email=fx.email,
        me={"company_display_name": fx.business_name},
    )
    snap = snapshot_from_context(ctx)
    assert snap.website_owned is True
    assert snap.analytics_state == "not_connected"

    reply, clarify = compose_read_reply(
        message="test",
        snapshot=snap,
        intent="connected",
        locale="de",
    )
    assert "Website" in reply
    assert clarify is None
