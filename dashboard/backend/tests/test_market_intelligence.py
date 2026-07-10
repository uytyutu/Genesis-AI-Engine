"""Market Intelligence — CEO approval flow, no auto updates."""

from app.integration.market_intelligence import (
    approve_recommendation,
    format_ceo_notification,
    list_pending_recommendations,
    propose_recommendation,
    reject_recommendation,
)
from app.integration.market_registry import MARKET_DE, get_market


def test_propose_does_not_mutate_registry():
    before = get_market(MARKET_DE).website_projects.business_website.average_market
    rec = propose_recommendation(MARKET_DE, direction="down", percent_change=3.0)
    after = get_market(MARKET_DE).website_projects.business_website.average_market
    assert before == after
    assert rec.recommended_range.average_market < before


def test_ceo_notification_format():
    rec = propose_recommendation(MARKET_DE)
    text = format_ceo_notification(rec)
    assert "Market Intelligence" in text
    assert "Принять" in text
    assert "Автоматического изменения нет" in text


def test_approve_reject_flow():
    rec = propose_recommendation(MARKET_DE, percent_change=5.0)
    assert len(list_pending_recommendations()) >= 1
    assert approve_recommendation(rec.recommendation_id)
    assert not list_pending_recommendations() or rec not in list_pending_recommendations()

    rec2 = propose_recommendation(MARKET_DE, direction="up", percent_change=2.0)
    assert reject_recommendation(rec2.recommendation_id)
