"""T-003 — Professional Surprise Principle."""

from __future__ import annotations

from app.integration.vector_intelligence.industry_intelligence import (
    build_decision_leadership_response,
    match_industry_profession,
    profession_style_followup,
)


def test_construction_professional_surprise():
    msg = (
        "У меня строительная фирма BauTeam Köln в Кёльне. "
        "Нужен сайт, чтобы люди оставляли заявки на ремонт."
    )
    out = build_decision_leadership_response(msg)
    assert out is not None
    assert "BauTeam Köln" in out
    assert "доверие до первого звонка" in out
    assert "фотографии работ" in out
    assert "Получить расчёт стоимости" in out
    assert "Если согласны" in out
    assert "B2B" not in out


def test_restaurant_menu_insight():
    msg = "Нужен сайт для кафе в Берлине."
    row = match_industry_profession(msg)
    assert row is not None
    assert row.pid == "PD-002"
    out = build_decision_leadership_response(msg)
    assert out is not None
    assert "два нажатия" in out or "двух кликов" in out


def test_auto_problem_not_list():
    msg = "Хочу сайт для автосервиса в Мюнхене."
    out = build_decision_leadership_response(msg)
    assert out is not None
    assert "решение проблемы" in out or "Замена тормозов" in out


def test_style_followup_no_jargon():
    msg = "Строительная компания BauTeam Köln, Кёльн, заявки на ремонт."
    followup = profession_style_followup(msg)
    assert followup is not None
    assert "B2B" not in followup
