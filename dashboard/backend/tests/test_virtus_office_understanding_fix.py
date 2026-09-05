"""Regression: language/type detection must not mislabel German Businessplan."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.integration.virtus_office.document_classify import classify_document_type
from app.integration.virtus_office.document_explain import build_document_explanation
from app.integration.virtus_office.language_detect import detect_source_language
from app.integration.virtus_office.understanding import (
    build_proposal_from_understanding,
    build_understanding,
)

BIZPLAN = (
    Path(__file__).resolve().parents[3]
    / "docs"
    / "business"
    / "Virtus_Core_Businessplan_Oltiiev.pdf"
)

RECHNUNG = """
Rechnung
Rechnungsnr: RE-99
Rechnungsdatum: 01.02.2026
Netto 100,00 EUR
MwSt. 19% 19,00 EUR
Brutto / Gesamtbetrag 119,00 EUR
"""

KONTO = """
Kontoauszug
IBAN DE12 3456 7890
BIC COBADEFFXXX
Anfangssaldo 1.000,00 EUR
Buchungstext Gehalt
Endsaldo 1.250,00 EUR
"""

CV = """
Lebenslauf
Berufserfahrung
Schulbildung
"""

BESCHEID = """
Bescheid
Aktenzeichen: JC-2026-11
Jobcenter Dresden
Widerspruchsfrist
"""


def test_cyrillic_noise_does_not_force_russian_on_german_text():
    # Simulate Businessplan: mostly German + a few Cyrillic glyphs
    text = (
        "Businessplan Virtus Core Dresden Deutschland "
        "Geschäftsidee Zielgruppe Marktanalyse Finanzierung Umsatz "
        "und der die das mit für werden können Unternehmen "
        + ("а" * 20)
    )
    lang = detect_source_language(text, filename="BUSINESSPLAN.pdf")
    assert lang["code"] == "de"
    assert lang["confidence"] >= 0.55


def test_real_cyrillic_document_still_russian():
    text = "Это договор компании для услуг и заявление. Пожалуйста проверьте счёт." * 5
    lang = detect_source_language(text)
    assert lang["code"] == "ru"


def test_businessplan_not_bank_or_invoice():
    text = (
        "BUSINESSPLAN\nVIRTUS CORE\nGeschäftsidee Leistungsangebot Zielgruppe "
        "Marktanalyse Wettbewerbsanalyse SWOT Finanzplanung Finanzierung "
        "Umsatzplanung Risiken Roadmap Executive Summary Inhaltsverzeichnis "
        "Gründungsvorhaben Business Model Canvas"
    )
    dtype = classify_document_type(text=text, filename="note.pdf", file_kind="pdf")
    assert dtype["id"] == "businessplan"
    assert dtype["confidence"] >= 0.7


def test_kontoauszug_still_bank():
    dtype = classify_document_type(text=KONTO, filename="auszug.pdf", file_kind="pdf")
    assert dtype["id"] == "bank_statement"


def test_rechnung_invoice():
    dtype = classify_document_type(text=RECHNUNG, filename="r.pdf", file_kind="pdf")
    assert dtype["id"] == "invoice"


def test_cv_and_bescheid():
    assert classify_document_type(text=CV, filename="cv.pdf")["id"] == "cv_lebenslauf"
    assert classify_document_type(text=BESCHEID, filename="b.pdf")["id"] == "official_notice"


@pytest.mark.skipif(not BIZPLAN.is_file(), reason="Businessplan PDF not in repo")
def test_real_businessplan_pdf_understanding():
    data = BIZPLAN.read_bytes()
    u = build_understanding(
        data=data,
        filename=BIZPLAN.name,
        file_kind="pdf",
        content_type="application/pdf",
    )
    assert u["language"] == "de", u
    assert u["document_type"] == "businessplan", u
    assert (u.get("page_count") or 0) >= 20
    assert (u.get("text_excerpt_chars") or 0) > 5000
    exp = u.get("explanation") or {}
    assert exp.get("about_id") == "businessplan"
    assert len(exp.get("sections") or []) >= 3
    proposal = build_proposal_from_understanding(u, filename=BIZPLAN.name)
    assert proposal["explanation"]["kind"] == "businessplan"
    assert proposal["detected"]["language"] == "de"
    ids = {c["id"] for c in (proposal.get("choice_options") or [])}
    assert "translate" in ids
    assert "summarize" not in ids  # no fake executor
