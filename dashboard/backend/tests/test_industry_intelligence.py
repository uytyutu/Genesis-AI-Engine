"""Professional Decision Backlog — Industry Intelligence."""

from __future__ import annotations

from app.integration.vector_intelligence.industry_intelligence import (
    build_decision_leadership_response,
    list_professions,
    match_industry_profession,
    profession_style_followup,
)


def test_construction_decision_model():
    msg = (
        "У меня строительная фирма BauTeam Köln в Кёльне. "
        "Нужен сайт, чтобы люди оставляли заявки на ремонт."
    )
    prof = match_industry_profession(msg)
    assert prof is not None
    assert prof.pid == "PD-001"
    assert "доверие" in prof.leader_decisions[0].lower()
    out = build_decision_leadership_response(msg)
    assert out is not None
    assert "доверие до первого звонка" in out or "доверие" in out
    assert "B2B" not in out


def test_restaurant_decision_not_menu_list():
    prof = match_industry_profession("Нужен сайт для кафе в Берлине.")
    assert prof is not None
    assert prof.pid == "PD-002"
    assert any("сегодня" in d.lower() for d in prof.leader_decisions)


def test_dental_fear_first_visit():
    prof = match_industry_profession("Сайт для стоматологии.")
    assert prof is not None
    assert any("страх" in d.lower() for d in prof.leader_decisions)


def test_profession_library_grows():
    assert len(list_professions()) >= 5
