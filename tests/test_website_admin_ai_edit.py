"""Website Control v1 — AI edit intents."""

from __future__ import annotations

import pytest

from app.integration.website_admin.ai_edit import parse_ai_edit_prompt


def test_add_service_german() -> None:
    parsed = parse_ai_edit_prompt("Добавь услугу: Maniküre Classic")
    svc = (parsed.get("content_patch") or {}).get("_append_service") or {}
    assert "Maniküre" in str(svc.get("title") or "")


def test_modern_hero() -> None:
    parsed = parse_ai_edit_prompt("Сделай Hero современнее")
    hero = (parsed.get("content_patch") or {}).get("hero") or {}
    assert hero.get("headline") or hero.get("subheadline")


def test_green_button() -> None:
    parsed = parse_ai_edit_prompt("Сделай кнопку зелёной")
    colors = (parsed.get("design_patch") or {}).get("colors") or {}
    assert colors.get("button")


def test_premium_tone() -> None:
    parsed = parse_ai_edit_prompt("Замени тон сайта на более премиальный")
    assert (parsed.get("content_patch") or {}).get("hero")
    assert (parsed.get("design_patch") or {}).get("colors")


def test_prices_section() -> None:
    parsed = parse_ai_edit_prompt("Добавь раздел Цены")
    prices = (parsed.get("content_patch") or {}).get("prices") or {}
    assert prices.get("enabled") is True


def test_empty_prompt() -> None:
    with pytest.raises(ValueError, match="empty"):
        parse_ai_edit_prompt("   ")


def test_vector_website_capabilities_live() -> None:
    from app.integration.vector.capabilities import action_for, is_live

    for cap in (
        "website_content_hero",
        "website_content_services",
        "website_content_contacts",
        "website_design_logo",
        "website_design_colors",
        "website_ai_edit",
        "website_publish",
        "open_website_admin",
    ):
        assert is_live(cap), cap
    coming = action_for("website_impressum")
    assert coming["kind"] == "coming"
    open_admin = action_for("open_website_admin", order_id="ord-x")
    assert open_admin["kind"] == "navigate_href"
    assert "ord-x" in str(open_admin.get("href") or "")
