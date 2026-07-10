"""Global pricing — preliminary project estimates."""

from app.integration.global_pricing import (
    build_preliminary_project_estimate,
    format_preliminary_project_estimate,
    global_pricing_rules_for_vector,
)
from app.integration.market_context import resolve_market_context
from app.integration.market_registry import MARKET_DE, PROJECT_BUSINESS_WEBSITE


def test_germany_preliminary_band():
    est = build_preliminary_project_estimate(MARKET_DE, project_type=PROJECT_BUSINESS_WEBSITE)
    assert est is not None
    assert est.amount_min == 490
    assert est.amount_max == 590


def test_preliminary_uses_project_terminology():
    est = build_preliminary_project_estimate(MARKET_DE)
    text = format_preliminary_project_estimate(est, market_name="Германия")
    assert "Предварительная смета проекта" in text
    assert "Business Website" in text
    assert "стоимость сайта" not in text.lower()


def test_rules_no_price_at_dialog_start():
    rules = global_pricing_rules_for_vector()
    assert "Не" in rules and "первом сообщении" in rules
    assert "предварительная смета" in rules.lower()


def test_estimate_after_market_context():
    ctx = resolve_market_context(text="сайт для Германии")
    est = build_preliminary_project_estimate(ctx.target_market_code)
    assert est is not None
    assert est.currency == "EUR"
