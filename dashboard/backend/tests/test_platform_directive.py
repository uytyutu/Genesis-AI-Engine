"""Platform Directive v2 — digital company behavior."""

from app.integration.genesis_brain.user_text_normalizer import normalize_user_text
from app.integration.platform_directive import (
    PLATFORM_NORTH_STAR,
    format_natural_next_steps,
    platform_directive_v2_rules,
    suggest_next_services,
)
from app.integration.product_line import SERVICE_BUSINESS_PLAN, SERVICE_WEBSITE


def test_north_star_present():
    assert "цифровая компания" in PLATFORM_NORTH_STAR
    assert "один проект" in PLATFORM_NORTH_STAR


def test_platform_rules_cover_directive_pillars():
    rules = platform_directive_v2_rules()
    assert "один проект" in rules.lower() or "память" in rules.lower()
    assert "намерение" in rules.lower() or "опечатк" in rules.lower()
    assert "Internal CEO" in rules
    assert "самообучение без границ" in rules.lower() or "контролем владельца" in rules.lower()
    assert "результатом" in rules.lower()


def test_next_steps_after_business_plan():
    steps = suggest_next_services(SERVICE_BUSINESS_PLAN)
    ids = {s["id"] for s in steps}
    assert SERVICE_WEBSITE in ids


def test_format_natural_next_steps_not_salesy():
    text = format_natural_next_steps(SERVICE_BUSINESS_PLAN)
    assert "бизнес-план" in text.lower()
    assert "сайт" in text.lower()
    assert "навязывание" in text.lower()


def test_typo_hachu_site_understood():
    assert "хочу" in normalize_user_text("хачу сайт").lower()


def test_business_plan_phrase_normalized():
    assert "бизнес-план" in normalize_user_text("нужен бизнес план").lower()
