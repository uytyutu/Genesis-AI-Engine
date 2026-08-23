"""Visual Polish R-cycle — mobile hero, client nav, demo strip, DE copy."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.factory.business_interview import interview_from_payload, interview_to_contacts
from app.factory.business_intelligence import resolve_business_intelligence
from app.factory.de_export_text import polish_de_export_html, resolve_differentiator
from app.factory.factory_service import FactoryService


def _auto_contacts() -> dict:
    iv = interview_from_payload(
        {
            "company_name": "Kfz Meisterbetrieb Schmidt",
            "city": "Berlin",
            "free_text": "Werkstatt fuer Inspektion, Bremsen, Oelwechsel.",
            "top_services": ["Inspektion", "Bremsenservice", "Oelwechsel"],
            "niche": "auto",
        }
    )
    return interview_to_contacts(
        iv,
        {
            "package_id": "business",
            "market_code": "DE",
            "client_delivery": True,
            "phone": "+49 30 1",
            "email": "a@b.de",
        },
    )


def _rest_contacts() -> dict:
    iv = interview_from_payload(
        {
            "company_name": "Restaurant Alt Berlin",
            "city": "Berlin",
            "free_text": "Regionale Kueche, saisonale Speisekarte.",
            "top_services": ["Mittagstisch", "Abendkarte"],
            "niche": "restaurant",
        }
    )
    return interview_to_contacts(
        iv,
        {
            "package_id": "business",
            "market_code": "DE",
            "client_delivery": True,
            "phone": "+49 30 2",
            "email": "g@b.de",
        },
    )


def test_de_export_polish_umlauts():
    raw = "Werkstatt fuer Oelwechsel und Regionale Kueche — Ueber uns"
    out = polish_de_export_html(f"<p>{raw}</p>", market_code="DE")
    assert "für" in out
    assert "Öl" in out
    assert "Küche" in out
    assert "Über" in out
    assert "fuer" not in out
    assert "Oel" not in out


def test_niche_differentiators_not_generic_bleed():
    auto = resolve_differentiator(niche_id="auto", city="Berlin", raw="")
    rest = resolve_differentiator(niche_id="restaurant", city="Berlin", raw="")
    assert auto != rest
    assert "Meisterwerkstatt" in auto or "Diagnose" in auto
    assert "Küche" in rest or "Gastfreundschaft" in rest


def test_client_delivery_build_has_no_demo_strip_or_reputation_nav(tmp_path: Path):
    factory = FactoryService(memory_dir=tmp_path, sandbox_dir=tmp_path / "sandbox")
    product = factory.build_landing(
        "Kfz Berlin Inspektion Bremsen Service.",
        package_id="business",
        market_code="DE",
        client_legal={
            "owner_name": "Schmidt",
            "street": "S 1",
            "zip": "10115",
            "city": "Berlin",
            "email": "a@b.de",
            "phone": "+49 30 1",
        },
        contacts=_auto_contacts(),
    )
    html = (tmp_path / "sandbox" / product["product_id"] / "index.html").read_text(
        encoding="utf-8"
    )
    assert "Demonstrativ — Referenzbilder" not in html
    assert "Demonstrativ" not in html
    assert "<p>Demo</p>" not in html
    assert ">Reputation</a>" not in html
    assert "Nachweise</a>" in html or "#reputation" in html
    assert "rep-demo-banner" not in html or "Beispielinhalte" not in html


def test_business_intelligence_differentiators_distinct():
    auto_bi = resolve_business_intelligence(
        contacts=_auto_contacts(),
        niche_id="auto",
        city="Berlin",
    )
    rest_bi = resolve_business_intelligence(
        contacts=_rest_contacts(),
        niche_id="restaurant",
        city="Berlin",
    )
    assert auto_bi.differentiator != rest_bi.differentiator


@pytest.mark.parametrize("niche,contacts,desc", [
    ("auto", _auto_contacts(), "Kfz Berlin Werkstatt Inspektion Bremsen."),
    ("restaurant", _rest_contacts(), "Restaurant Berlin Speisekarte Reservierung."),
])
def test_mobile_hero_css_single_column(tmp_path: Path, niche: str, contacts: dict, desc: str):
    factory = FactoryService(memory_dir=tmp_path, sandbox_dir=tmp_path / "sandbox")
    product = factory.build_landing(
        desc,
        package_id="business",
        market_code="DE",
        client_legal={
            "owner_name": "T",
            "street": "S 1",
            "zip": "10115",
            "city": "Berlin",
            "email": "t@b.de",
            "phone": "+49 30 1",
        },
        contacts=contacts,
    )
    html = (tmp_path / "sandbox" / product["product_id"] / "index.html").read_text(
        encoding="utf-8"
    )
    assert "grid-template-columns: 1fr !important" in html
    assert "min(52vh" in html or "52vh" in html
