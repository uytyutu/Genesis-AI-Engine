"""Commercial API Gateway — pricing catalog, scopes, rate limit, sanitize."""

from __future__ import annotations

from pathlib import Path

from app.commercial_api.catalog import catalog, product
from app.commercial_api.gateway import CommercialApiGateway
from app.commercial_api.keys import CommercialApiKeyStore
from app.commercial_api.pricing import DEFAULT_PRICES_EUR, price_eur, pricing_public
from app.commercial_api.rate_limit import allow_request
from app.commercial_api.sanitize import sanitize_public


def test_pricing_not_hardcoded_only_in_gateway(tmp_path: Path):
    assert price_eur("audit") == DEFAULT_PRICES_EUR["audit"]
    (tmp_path / "commercial_api_pricing.json").write_text(
        '{"audit": {"price_eur": 0.99}}', encoding="utf-8"
    )
    assert price_eur("audit", tmp_path) == 0.99
    pub = pricing_public(tmp_path)
    assert any(m["product"] == "audit" and m["price_eur"] == 0.99 for m in pub["methods"])
    assert "roadmap" in pub


def test_catalog_merges_prices(tmp_path: Path):
    cat = catalog(tmp_path)
    audit = next(p for p in cat["products"] if p["id"] == "audit")
    assert audit["price_eur"] == price_eur("audit", tmp_path)
    assert cat["pricing_url"] == "/api/v1/pricing"


def test_scope_and_revoke(tmp_path: Path):
    store = CommercialApiKeyStore(tmp_path)
    created = store.create_key(label="t", balance_eur=5.0, scopes=["audit"])
    raw = created["api_key"]
    row = store.resolve(raw)
    assert row is not None
    assert store.has_scope(row, "audit") is True
    assert store.has_scope(row, "factory") is False
    store.revoke(str(row["id"]))
    assert store.resolve(raw) is None


def test_rate_limit_blocks():
    ok, _ = allow_request("k-test", limit_per_min=2)
    assert ok is True
    ok, _ = allow_request("k-test", limit_per_min=2)
    assert ok is True
    ok, rem = allow_request("k-test", limit_per_min=2)
    assert ok is False
    assert rem == 0


def test_sanitize_strips_internals():
    clean = sanitize_public({"url": "https://x", "engine_id": "secret", "debug": True, "score": 1})
    assert "engine_id" not in clean
    assert "debug" not in clean
    assert clean["score"] == 1


def test_run_audit_uses_catalog_price(tmp_path: Path):
    from unittest.mock import patch

    (tmp_path / "commercial_api_pricing.json").write_text(
        '{"audit": {"price_eur": 0.25}}', encoding="utf-8"
    )
    store = CommercialApiKeyStore(tmp_path)
    created = store.create_key(label="t", balance_eur=5.0, scopes=["audit"])
    gw = CommercialApiGateway(tmp_path)
    with patch("app.integration.website_analysis_v1.WebsiteAnalysisV1") as cls:
        cls.return_value.analyze.return_value = {
            "ok": True,
            "engine_id": "hide-me",
            "health_score": 70,
        }
        result = gw.run_audit(created["api_key"], url="https://example.com")
    assert result["ok"] is True
    assert result["charged_eur"] == 0.25
    assert "engine_id" not in result["report"]
    assert result["report"]["health_score"] == 70


def test_leads_scope_denied(tmp_path: Path):
    store = CommercialApiKeyStore(tmp_path)
    created = store.create_key(label="t", balance_eur=5.0, scopes=["audit"])
    gw = CommercialApiGateway(tmp_path)
    result = gw.run_leads_preview(created["api_key"], city="Dresden")
    assert result["ok"] is False
    assert result["reason"] == "scope_denied"


def test_offer_scores_pick_max_not_hard_saas_rule():
    from app.commercial_api.platform_billing import (
        resolve_offer_lane,
        score_commercial_offers,
    )

    restaurant = score_commercial_offers(
        {"company_name": "Pizzeria Roma", "niche": "restaurant", "meta": {}}
    )
    by_id = {p["id"]: p["score"] for p in restaurant["products"]}
    assert by_id["website"] > by_id["platform_api"]
    assert restaurant["selected_lane"] == "website"

    saas = score_commercial_offers(
        {"company_name": "CloudCRM GmbH", "niche": "SaaS CRM software", "meta": {}}
    )
    assert saas["selected_id"] == "platform_api"
    assert saas["selected_lane"] == "api"
    assert resolve_offer_lane(saas) == "api" or resolve_offer_lane(
        {"company_name": "CloudCRM", "niche": "saas crm"}
    ) == "api"

    # Website rejected → API can still win (dual product, one Hunt)
    healthy = score_commercial_offers(
        {
            "company_name": "DevTools AI",
            "niche": "devtools platform",
            "meta": {"website_offer": "rejected"},
        }
    )
    assert healthy["selected_lane"] == "api"
    assert next(p["score"] for p in healthy["products"] if p["id"] == "website") == 0


def test_usage_analytics_gated_before_first_buyer(tmp_path: Path):
    from app.commercial_api.platform_billing import PlatformApiBilling

    panel = PlatformApiBilling(tmp_path).analytics()
    assert panel["phase"] == "awaiting_first_buyer"
    assert panel["keys"] == []
    assert "перв" in panel["gate_ru"].lower() or "1" in panel["gate_ru"]


def test_sandbox_checkout_fulfills_micro_key(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("GENESIS_PAYMENT_SANDBOX", "1")
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    monkeypatch.delenv("STRIPE_SECRET_KEY_LIVE", raising=False)

    from app.commercial_api.platform_billing import PlatformApiBilling

    billing = PlatformApiBilling(tmp_path)
    result = billing.create_checkout(
        package_id="micro",
        customer_email="buyer@example.com",
    )
    assert result["ok"] is True
    assert result["sandbox"] is True
    fulfilled = result["fulfilled"]
    assert fulfilled["ok"] is True
    assert str(fulfilled.get("api_key") or "").startswith("vk_live_")
    assert float(fulfilled.get("balance_eur") or 0) == 5.0


def test_webhook_branches_to_platform_api_fulfill(monkeypatch, tmp_path: Path):
    import json

    import app.services.finance_center as finance_center
    from app.commercial_api.platform_billing import PlatformApiBilling
    from app.services.finance_center import handle_stripe_webhook_event

    class FakeRevenue:
        def __init__(self) -> None:
            self._memory = tmp_path

        def apply_stripe_checkout_payment(self, **_kwargs):
            raise AssertionError("website order path must not run for Platform API")

    event = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_test_api_1",
                "payment_intent": "pi_test_1",
                "amount_total": 500,
                "currency": "eur",
                "customer_details": {"email": "api@example.com"},
                "metadata": {
                    "order_id": "api_micro_api",
                    "product": "commercial_api_package",
                    "package_id": "micro",
                    "customer_email": "api@example.com",
                },
            }
        },
    }

    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_test")
    monkeypatch.setattr(
        finance_center.stripe.Webhook,
        "construct_event",
        lambda payload, signature, secret: json.loads(payload.decode("utf-8")),
    )

    out = handle_stripe_webhook_event(
        json.dumps(event).encode("utf-8"),
        "t=1,v1=x",
        FakeRevenue(),
    )
    assert out["status"] == "success"
    assert out["product"] == "commercial_api_package"
    assert out["package_id"] == "micro"
    row = PlatformApiBilling(tmp_path).already_fulfilled("cs_test_api_1")
    assert row is not None
    assert row["package_id"] == "micro"


def test_packages_and_lab_ceo_actions(tmp_path: Path):
    from app.commercial_api.packages import get_package, list_packages
    from app.commercial_api.revenue_lab import RevenueLab

    pkgs = list_packages()
    assert any(p["id"] == "micro" for p in pkgs)
    micro = get_package("micro")
    assert micro is not None
    assert float(micro["price_eur"]) == 5.0
    assert any(p["id"] == "starter" for p in pkgs)
    starter = get_package("starter")
    assert starter is not None
    assert "audit" in starter["scopes"]

    store = CommercialApiKeyStore(tmp_path)
    key = store.create_from_package(package=starter, label="Agency")
    assert key["balance_eur"] == starter["balance_eur"]
    assert "audit" in key["scopes"]

    brief = RevenueLab(tmp_path).ceo_brief()
    assert brief["ceo_actions"]
    assert any(
        a.get("kind") in {"connect_key", "complete_keys", "use_connected"}
        or "Подключи" in a.get("title_ru", "")
        or "Используй" in a.get("title_ru", "")
        for a in brief["ceo_actions"]
    )


def test_lab_digistore_key_stops_connect_asks_use(monkeypatch, tmp_path: Path):
    from app.commercial_api.revenue_lab import RevenueLab

    monkeypatch.setenv("DIGISTORE24_API_KEY", "ds24_test_key")
    monkeypatch.delenv("AWIN_API_TOKEN", raising=False)
    monkeypatch.delenv("AWIN_PUBLISHER_ID", raising=False)
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_x")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_x")

    scan = RevenueLab(tmp_path).research_scan(persist_alerts=False)
    digi = next(f for f in scan["findings"] if f["id"] == "digistore24_affiliate")
    assert digi["connected"] is True
    assert not any(
        a.get("source_id") == "digistore24_affiliate" and a.get("kind") == "connect_key"
        for a in scan["ceo_actions"]
    )
    use = next(
        a
        for a in scan["ceo_actions"]
        if a.get("source_id") == "digistore24_affiliate" and a.get("kind") == "use_connected"
    )
    assert "не просим" in use["action_ru"].lower() or "уже" in use["action_ru"].lower()
    assert any("Digistore" in (a.get("title_ru") or "") or a.get("source_id") == "digistore24_affiliate" for a in scan["ceo_actions"])
    assert scan["digistore24"]["key_present"] is True
    assert "Country Desk" in scan["headline_ru"] or "Digistore" in scan["headline_ru"]


def test_digistore24_capability_brief_standalone():
    from app.commercial_api.digistore24_capability import digistore24_capability_brief

    brief = digistore24_capability_brief(key_present=True)
    caps = {a["capability"]: a["ok"] for a in brief["q1_api_allows"]["answers"]}
    assert caps["Статистика"] is True
    assert caps["Продажи"] is True
    assert caps["Комиссии"] is True
    assert caps["Клики / сырой трафик"] is False
    enables = [a for a in brief["q2_automatable"]["actions"] if a["leads_to_first_commission"] == "enables"]
    assert enables
    assert brief["reality_chain_ru"][-1] == "Реальный доход"
