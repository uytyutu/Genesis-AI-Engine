"""Market-aware Path A outreach templates (DE / EN-US / RU / UA)."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.integration.outreach_language_service import (
    OutreachLanguageService,
    language_for_market,
    preview_market_templates,
    resolve_market_from_row,
)
from app.legal.service import LegalFoundationService


@pytest.fixture(autouse=True)
def _no_send_interval(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GENESIS_OUTREACH_MIN_INTERVAL_SEC", "0")


def test_market_drives_language():
    assert language_for_market("DE") == "de"
    assert language_for_market("US") == "en-us"
    assert language_for_market("UA") == "uk"
    assert language_for_market("RU") == "ru"
    assert resolve_market_from_row({"meta": {"market": "US"}}) == "US"
    assert resolve_market_from_row({"meta": {"city": "Kyiv"}}) == "UA"


def test_templates_tone_by_market(monkeypatch: pytest.MonkeyPatch):
    import app.integration.outreach_language_service as ols

    monkeypatch.setattr(ols._AI, "generate_personalized_offer", lambda **kwargs: None)
    svc = OutreachLanguageService()

    _, de_body, de_lang = svc.draft_outreach(
        company="Auto Müller",
        analysis={"issues": ["Kein HTTPS"]},
        package={"name": "Landing"},
        price=350,
        fit_reason="Kfz",
        row={"market": "DE", "meta": {"market": "DE", "niche": "kfz"}},
        allow_llm=False,
    )
    assert de_lang == "de"
    assert "Guten Tag" in de_body
    assert "Mit freundlichen Grüßen" in de_body or "Werkstatt" in de_body

    _, us_body, us_lang = svc.draft_outreach(
        company="Acme Plumbing",
        analysis={"issues": ["No HTTPS"]},
        package={"name": "Landing"},
        price=350,
        fit_reason="weak site",
        row={"market": "US", "meta": {"market": "US"}},
        allow_llm=False,
    )
    assert us_lang == "en-us"
    assert us_body.startswith("Hi,")
    assert "Took a look" in us_body
    assert "Impressum" not in us_body

    _, ru_body, ru_lang = svc.draft_outreach(
        company="Сервис Плюс",
        analysis={"issues": ["Нет HTTPS"]},
        package={"name": "Landing"},
        price=350,
        fit_reason="сайт",
        row={"market": "RU", "meta": {"market": "RU"}},
        allow_llm=False,
    )
    assert ru_lang == "ru"
    assert "Здравствуйте" in ru_body
    assert "не предлагаем «починить" in ru_body

    _, ua_body, ua_lang = svc.draft_outreach(
        company="Авто Сервіс",
        analysis={"issues": ["Немає HTTPS"]},
        package={"name": "Landing"},
        price=350,
        fit_reason="сайт",
        row={"market": "UA", "meta": {"market": "UA"}},
        allow_llm=False,
    )
    assert ua_lang == "uk"
    assert "Доброго дня" in ua_body
    assert "не пропонуємо" in ua_body


def test_preview_samples_for_ceo():
    samples = preview_market_templates()
    assert {s["market"] for s in samples} == {"DE", "US", "RU", "UA"}
    assert all(s["subject"] and s["body"] for s in samples)


def test_us_footer_has_no_impressum(tmp_path: Path):
    legal = LegalFoundationService(tmp_path)
    us = legal.email_footer_for_market("US", include_opt_out=True, for_outreach=True, language="en-us")
    assert "Impressum" not in us["text"]
    assert "Unsubscribe" in us["text"]
    assert us["profile"] == "us"

    de = legal.email_footer_for_market("DE", include_opt_out=True, for_outreach=True, language="de")
    assert "Impressum" in de["text"]
    assert de["profile"] == "de"
