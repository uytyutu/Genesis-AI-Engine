"""Full market localization."""

from app.integration.market_localization import full_localization_rules_for_vector, resolve_localized_commerce
from app.integration.market_context import resolve_market_context


def test_us_commerce_usd():
    ctx = resolve_market_context(text="website for United States market")
    commerce = resolve_localized_commerce(ctx)
    assert commerce.currency == "USD"


def test_poland_commerce_pln():
    ctx = resolve_market_context(text="сайт для Польши")
    commerce = resolve_localized_commerce(ctx)
    assert commerce.currency == "PLN"


def test_localization_includes_intelligence_meta():
    ctx = resolve_market_context(text="сайт для Германии")
    commerce = resolve_localized_commerce(ctx)
    assert commerce.competition_level == "high"
    assert commerce.last_review == "2026-07"


def test_localization_rules_no_early_price():
    rules = full_localization_rules_for_vector()
    assert "Не показывать цену в начале диалога" in rules
