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


def test_packages_and_lab_ceo_actions(tmp_path: Path):
    from app.commercial_api.packages import get_package, list_packages
    from app.commercial_api.revenue_lab import RevenueLab

    pkgs = list_packages()
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
    assert "Подключи" in brief["headline_ru"] or brief["ceo_actions"][0]["title_ru"].startswith(
        "Подключи"
    )
