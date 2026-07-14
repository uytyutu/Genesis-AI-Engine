"""Production Platform — catalog, cost engine, auto quote."""

from app.integration.production_platform import (
    auto_quote_from_rows,
    build_production_platform,
    cost_engine_quote,
)


def test_product_catalog_has_five_services():
    p = build_production_platform()
    assert len(p["product_catalog"]) == 5
    assert p["product_catalog"][0]["service_number"] == 1


def test_cost_engine_quote_margin():
    q = cost_engine_quote(service_id="svc_document_labeling", volume=1000, workers=10)
    assert q["ok"] is True
    assert q["sell_price_eur"] > q["internal_cost_eur"]
    assert q["margin_pct"] > 0


def test_auto_quote_rows():
    q = auto_quote_from_rows(row_count=18200, workers=10)
    assert q["ok"] is True
    assert q["sell_price_eur"] > 0
    assert "18" in q["input_ru"] or "18,200" in q["input_ru"] or "18200" in q["input_ru"]


def test_revenue_router_recommends_b2b():
    p = build_production_platform(toloka_verdict="CHANNEL_REVIEW")
    channels = p["revenue_router"]["channels"]
    b2b = next(c for c in channels if c["id"] == "b2b_direct")
    assert b2b["potential"] == "very_high"
    toloka = next(c for c in channels if c["id"] == "toloka")
    assert toloka["status"] == "crash_test"
