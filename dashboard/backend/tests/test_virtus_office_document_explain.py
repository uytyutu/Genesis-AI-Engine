"""Unit tests for deterministic Office document explanation."""

from __future__ import annotations

from app.integration.virtus_office.document_explain import build_document_explanation
from app.integration.virtus_office.understanding import (
    build_proposal_from_understanding,
    build_understanding,
)


SAMPLE_RECHNUNG = """
Rechnung
Lieferant: Mustermann GmbH
Rechnungsempfänger: Frau Beispiel
Rechnungsnr: RE-2026-0042
Rechnungsdatum: 12.03.2026

Pos. 1 Beratung 100,00 EUR
Pos. 2 Support 50,00 EUR
Pos. 3 Lizenz 25,00 EUR

Netto-Summe: 175,00 EUR
MwSt. 19%: 33,25 EUR
Brutto-Summe / Gesamtbetrag: 208,25 EUR
"""


def test_invoice_explanation_finds_signals_without_invention():
    explanation = build_document_explanation(
        text=SAMPLE_RECHNUNG,
        doc_type={"id": "invoice", "label_de": "Rechnung", "confidence": 0.9},
        lang={"code": "de", "confidence": 0.9},
        structure={"pages": 1, "tables": 0, "text_detected": True, "ocr_status": "not_needed"},
        filename="Rechnung.pdf",
    )
    ids = {f["id"] for f in explanation["findings"]}
    assert "supplier_block" in ids
    assert "client_block" in ids
    assert "invoice_number" in ids
    assert "mwst" in ids
    assert "netto" in ids
    assert "brutto" in ids
    inv = next(f for f in explanation["findings"] if f["id"] == "invoice_number")
    assert inv.get("value") == "RE-2026-0042"
    # Must not invent employer names as free-form prose
    assert explanation["honesty"] == "no_invention"


def test_build_understanding_exposes_explanation_on_proposal():
    u = build_understanding(
        data=SAMPLE_RECHNUNG.encode("utf-8"),
        filename="Rechnung.txt",
        file_kind="txt",
        content_type="text/plain",
    )
    assert u.get("explanation")
    assert u["explanation"]["about_id"] in {"invoice", "general"}
    proposal = build_proposal_from_understanding(u, filename="Rechnung.txt")
    assert isinstance(proposal.get("explanation"), dict)
    assert proposal["explanation"].get("findings")
