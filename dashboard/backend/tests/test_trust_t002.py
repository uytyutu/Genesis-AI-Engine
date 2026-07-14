"""T-002 — Reflection before Direction + Single Truth."""

from __future__ import annotations

from app.execution.bridge import _site_development_hint, _site_reflection_block
from app.integration.project_platform.journey_state import (
    extract_company_name,
    extract_industry_label,
    extract_site_goal_label,
)


def test_extract_bauteam_koln():
    msg = (
        "У меня строительная фирма BauTeam Köln в Кёльне. "
        "Нужен простой сайт, чтобы люди оставляли заявку на ремонт."
    )
    assert extract_company_name(msg) == "BauTeam Köln"
    assert extract_industry_label(msg) == "строительная компания"
    assert extract_site_goal_label(msg) is not None
    assert "заявк" in extract_site_goal_label(msg) or ""


def test_reflection_before_direction():
    msg = (
        "У меня строительная фирма BauTeam Köln в Кёльне. "
        "Нужен простой сайт, чтобы люди оставляли заявку на ремонт."
    )
    reflection = _site_reflection_block(msg)
    assert "Понял." in reflection
    assert "BauTeam Köln" in reflection
    assert "строительная компания" in reflection
    assert "Кёльн" in reflection
    assert "заявк" in reflection.lower()
    assert "Это зафиксировал." in reflection
    assert "B2B" not in reflection


def test_development_not_parrot():
    msg = "У меня небольшая строительная фирма в Кёльне. Хочу больше заявок."
    hint = _site_development_hint(msg)
    assert hint is not None
    assert "фотографии работ" in hint or "доверие" in hint
