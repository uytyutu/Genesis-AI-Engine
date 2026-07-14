"""Decision Intelligence Platform — O → D → D → E."""

from __future__ import annotations

from app.integration.vector_intelligence.decision_intelligence import (
    build_decision_intelligence_response,
    evaluate_company_situation,
    try_decision_intelligence_route,
)


def test_construction_without_site_request_defers_website():
    msg = "У меня небольшая строительная фирма в Кёльне. Клиентов мало, всё в Excel."
    brief = evaluate_company_situation(msg)
    assert brief is not None
    assert brief.website_first is False
    assert brief.recommended_focus == "presence_first"
    out = build_decision_intelligence_response(msg)
    assert out is not None
    assert "Google Business" in out
    assert "сайт" in out.lower()
    assert "потом" in out.lower() or "подождать" in out.lower()
    assert "B2B" not in out


def test_construction_with_site_request_proceeds_website():
    msg = "Нужен сайт для строительной фирмы BauTeam Köln в Кёльне."
    brief = evaluate_company_situation(msg)
    assert brief is not None
    assert brief.website_first is True
    route = try_decision_intelligence_route(msg)
    assert route is None


def test_restaurant_without_site_suggests_qr_first():
    msg = "У меня небольшое кафе в Берлине, мало гостей."
    brief = evaluate_company_situation(msg)
    assert brief is not None
    assert brief.website_first is False
    out = build_decision_intelligence_response(msg)
    assert out is not None
    assert "QR" in out or "меню" in out


def test_route_returns_execution_context():
    msg = "Строительная бригада в Кёльне, хочу больше заказов."
    route = try_decision_intelligence_route(msg)
    assert route is not None
    assert route["context"]["decision_intelligence"] is True
    assert route["context"]["website_first"] is False
