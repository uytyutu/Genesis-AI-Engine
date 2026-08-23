"""Pricing Engine — Path A SSOT across letter, checkout, Stripe, Factory."""

from __future__ import annotations

from pathlib import Path

from app.integration.commerce_engine import resolve_checkout_packages, resolve_final_offer
from app.integration.pricing_engine import (
    resolve_path_a_offer,
    stripe_major_from_total,
    stripe_unit_amount,
)


def test_de_regression_unchanged():
    offer = resolve_path_a_offer("basic", "DE")
    assert offer.amount == 299
    assert offer.currency == "EUR"
    assert offer.price_label == resolve_final_offer("basic", "DE").price_label


def test_de_website_ladder_299_599_999():
    assert resolve_path_a_offer("basic", "DE").amount == 299
    assert resolve_path_a_offer("business", "DE").amount == 599
    assert resolve_path_a_offer("premium", "DE").amount == 999
    assert resolve_path_a_offer("standalone", "DE").amount == 599
    assert resolve_path_a_offer("connected", "DE").amount == 999


def test_ssot_parity_offer_and_checkout():
    for market in ("DE", "AU", "JP", "KR", "US", "GB"):
        offer = resolve_path_a_offer("basic", market)
        grid = resolve_checkout_packages(market)
        basic = next(p for p in grid["packages"] if p["id"] == "basic")
        assert basic["price_label"] == offer.price_label
        assert float(basic["price_eur"]) == float(offer.amount)
        assert basic["currency"] == offer.currency


def test_jp_kr_curated_not_ratio_junk():
    jp = resolve_path_a_offer("basic", "JP")
    assert jp.amount == 46985
    assert jp.currency == "JPY"
    kr = resolve_path_a_offer("business", "KR")
    assert kr.amount == 820169
    assert kr.currency == "KRW"


def test_repair_jp_local_not_eur199():
    offer = resolve_path_a_offer("repair_lite", "JP")
    assert offer.amount == 35000
    assert offer.amount != 199
    assert "¥" in offer.price_label or "JPY" in offer.currency


def test_stripe_zero_decimal_jp_kr():
    assert stripe_unit_amount(55000, "JPY") == 55000
    assert stripe_unit_amount(490000, "KRW") == 490000
    assert stripe_unit_amount(199, "EUR") == 19900
    assert stripe_major_from_total(55000, "jpy") == 55000.0
    assert stripe_major_from_total(19900, "eur") == 199.0


def test_prepare_draft_matches_ssot(tmp_path: Path):
    from app.integration.outreach_language_service import OutreachLanguageService

    offer = resolve_path_a_offer("basic", "JP")
    subject, body, used = OutreachLanguageService().draft_outreach(
        company="Tokyo Dental",
        analysis={"issues": ["mobile"]},
        package={
            "name": "Landing Basic",
            "price_label": offer.price_label,
            "currency": offer.currency,
            "symbol": offer.symbol,
        },
        price=float(offer.amount),
        fit_reason="test",
        row={"market": "JP", "meta": {"market": "JP"}},
        allow_llm=False,
    )
    assert offer.price_label in body
    assert used == "ja"
    assert subject


def test_reprice_rebuilds_proposed_message(tmp_path: Path):
    from app.integration.acquisition_studio_service import AcquisitionStudioService
    from app.integration.opportunity_service import OpportunityService

    mem = tmp_path / "memory"
    mem.mkdir()
    opp = OpportunityService(mem)
    stale = "OLD PRICE 15 000 € must not remain"
    row = {
        "id": "lead-au-1",
        "company_name": "Sydney Plumber",
        "website_url": "https://example.com.au",
        "status": "qualified",
        "outreach_status": "pending_approval",
        "recommended_package_id": "basic",
        "recommended_price_eur": 350,
        "recommended_currency": "EUR",
        "recommended_price_label": "350 €",
        "proposed_subject": "old",
        "proposed_message": stale,
        "fit_reason": "no https",
        "meta": {
            "market": "AU",
            "recommended_package_id": "basic",
            "recommended_price_label": "350 €",
        },
        "market": "AU",
        "site_analysis": {"issues": ["no https"], "fetch_ok": True, "issue_count": 2},
    }
    opp._save_rows([row])

    class _Sales:
        pass

    studio = AcquisitionStudioService(opp, _Sales())
    result = studio.reprice_pipeline_leads(limit=10)
    assert result["repriced"] >= 1
    # _load_rows normalizes schema — price_label lives on meta + letter body
    updated = next(r for r in opp._load_rows() if r.get("id") == "lead-au-1")
    offer = resolve_path_a_offer("basic", "AU")
    assert float(updated["recommended_price_eur"]) == float(offer.amount)
    assert (updated.get("meta") or {}).get("recommended_price_label") == offer.price_label
    assert offer.price_label in (updated.get("proposed_message") or "")
    assert stale not in (updated.get("proposed_message") or "")


def test_desk_market_basic_anchors_match_ceo_table():
    """Country Desk Basic anchors — currency + amount (major units)."""
    expected = {
        "US": (341, "USD"),
        "DE": (299, "EUR"),
        "GB": (255, "GBP"),
        "FR": (282, "EUR"),
        "IT": (273, "EUR"),
        "ES": (257, "EUR"),
        "CA": (341, "USD"),
        "AU": (469, "AUD"),
        "NL": (316, "EUR"),
        "PL": (1025, "PLN"),
        "CH": (334, "CHF"),
        "AT": (299, "EUR"),
        "BE": (299, "EUR"),
        "PT": (231, "EUR"),
        "CZ": (12815, "CZK"),
        "RO": (171, "EUR"),
        "SK": (188, "EUR"),
        "UA": (6835, "UAH"),
        "RU": (153, "EUR"),
        "NZ": (469, "NZD"),
        "JP": (46985, "JPY"),
        "KR": (418600, "KRW"),
        "SG": (427, "SGD"),
    }
    for market, (amount, currency) in expected.items():
        offer = resolve_path_a_offer("basic", market)
        assert offer.amount == amount, f"{market} amount"
        assert offer.currency == currency, f"{market} currency"
        grid = resolve_checkout_packages(market)
        assert grid["currency"] == currency
        basic = next(p for p in grid["packages"] if p["id"] == "basic")
        assert float(basic["price_eur"]) == float(amount)
        assert basic["currency"] == currency


def test_sales_repair_uses_pricing_engine(tmp_path: Path):
    from app.integration.sales_order_service import SalesOrderService

    class _Factory:
        def submit(self, _intent):
            return {"product_id": "p1"}

    sales = SalesOrderService(tmp_path, _Factory())
    package, offer = sales._package_offer("repair_lite", market_code="JP")
    assert package["price_eur"] == 35000.0
    assert offer["amount"] == 35000
    assert package["currency"] == "JPY"
