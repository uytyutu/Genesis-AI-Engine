"""Global Market Database v1 tests."""

from app.integration.market_registry import MARKET_DE, MARKET_US, STAGE1_MARKET_CODES, get_market, list_active_markets
from app.integration.market_registry_schema import PROJECT_BUSINESS_WEBSITE, PROJECT_ONLINE_STORE


def test_stage1_markets_v1():
    assert len(STAGE1_MARKET_CODES) == 30
    assert len(list_active_markets()) == 30


def test_germany_business_website_ceo_band():
    m = get_market(MARKET_DE)
    b = m.project_range(PROJECT_BUSINESS_WEBSITE)
    assert b is not None
    assert b.from_amount == 490
    assert b.to_amount == 590
    assert b.average_market == 540


def test_germany_ecommerce_band():
    m = get_market(MARKET_DE)
    b = m.project_range(PROJECT_ONLINE_STORE)
    assert b is not None
    assert b.from_amount == 890
    assert b.to_amount == 1190


def test_market_has_intelligence_metadata():
    m = get_market(MARKET_DE)
    assert m.intelligence.competition_level == "high"
    assert m.intelligence.market_factor == 1.0
    assert m.intelligence.last_review == "2026-07"
    assert m.requires == ("impressum", "datenschutz", "gdpr")


def test_portugal_and_russia_in_registry():
    from app.integration.market_registry import MARKET_PT, MARKET_RU

    pt = get_market(MARKET_PT)
    ru = get_market(MARKET_RU)
    assert pt.code == "PT" and pt.currency == "EUR"
    assert ru.code == "RU" and ru.currency == "EUR"
    assert get_market("PT").code != "DEFAULT"
    assert get_market("RU").code != "DEFAULT"


def test_us_usd_business_band():
    m = get_market(MARKET_US)
    b = m.project_range(PROJECT_BUSINESS_WEBSITE)
    assert m.currency == "USD"
    assert b is not None
    assert b.from_amount >= 600
