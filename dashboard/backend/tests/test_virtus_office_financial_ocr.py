"""Financial OCR field honesty + quality gate regression."""

from __future__ import annotations

from io import BytesIO

from app.integration.virtus_office.financial_fields import (
    extract_financial_fields,
    looks_like_financial_document,
    validate_financial_fields,
)
from app.integration.virtus_office.quality_gate import run_quality_gate


def _clean_invoice_text() -> str:
    return (
        "RECHNUNG\n"
        "Nr. RE-SCAN-77\n"
        "Datum 10.06.2026\n"
        "Kunde: Virtus Core\n"
        "Betrag 199,00 EUR\n"
        "MwSt 19% 37,81 EUR\n"
        "Gesamt 236,81 EUR\n"
    )


def _garbled_invoice_text() -> str:
    return (
        "RECHNUNG\n"
        "Nr RE-SCANT7\n"
        "Datum 10.08, 2028,\n"
        "Kunde: Virtus Core\n"
        "Betrag 199,00 EUR\n"
        "Mwst19%97,81 EUR\n"
        "Gesamt23681 EUR\n"
    )


def test_clean_invoice_financial_pass():
    text = _clean_invoice_text()
    assert looks_like_financial_document(text)
    fields = extract_financial_fields(text)
    assert fields["invoice_number"] == "RE-SCAN-77"
    assert fields["date"] == "10.06.2026"
    assert str(fields["netto"]) == "199.00"
    assert str(fields["mwst_amount"]) == "37.81"
    assert str(fields["brutto"]) == "236.81"
    qa = validate_financial_fields(text, confidence=0.9)
    assert qa["passed"] is True
    assert qa["needs_review"] is False


def test_garbled_invoice_financial_fail():
    text = _garbled_invoice_text()
    qa = validate_financial_fields(text, confidence=0.6)
    assert qa["is_financial"] is True
    assert qa["passed"] is False
    assert qa["needs_review"] is True
    assert qa["warning_de"]


def test_quality_gate_rejects_garbled_financial_ocr():
    text = _garbled_invoice_text()
    qa = validate_financial_fields(text)
    blob = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n1 0 obj<<>>endobj\ntrailer<<>>\nstartxref\n0\n%%EOF\n"
    # pad
    blob = blob + b" " * 64
    result = run_quality_gate(
        action_id="translate",
        input_text=text,
        output_text="INVOICE\nNo RE-SCANT7\n...",
        artifact_bytes=blob,
        artifact_ext="pdf",
        artifact_mime="application/pdf",
        target_language="en",
        translation_provider="groq",
        job_id="j1",
        artifact_job_id="j1",
        document_type="invoice",
        ocr_financial_qa=qa,
        delivery_mode="text_rebuild_pdf",
    )
    assert result["passed"] is False
    assert "financial_fields_ok" in result["failed"]


def test_quality_gate_rejects_businessplan_text_rebuild_layout():
    src = "A" * 3000 + "\n\nFinanzplanung\nvertraulich\n"
    out = "B" * 3000 + "\n\nFinancial planning\nconfidential\n"
    # Minimal valid-ish PDF bytes
    blob = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\nstartxref\n0\n%%EOF\n" + b"x" * 100
    result = run_quality_gate(
        action_id="translate",
        input_text=src,
        output_text=out,
        artifact_bytes=blob,
        artifact_ext="pdf",
        artifact_mime="application/pdf",
        target_language="en",
        translation_provider="groq",
        job_id="j2",
        artifact_job_id="j2",
        document_type="businessplan",
        source_page_count=28,
        source_image_count=12,
        delivery_mode="text_rebuild_pdf",
    )
    assert result["passed"] is False
    assert "layout_fidelity" in result["failed"]


def test_arbeitsvertrag_not_forced_financial():
    text = (
        "Arbeitsvertrag\nArbeitgeber: Muster GmbH\n"
        "Arbeitnehmer: Max Mustermann\nDatum: 01.03.2024\n"
        "Gesamtbetrag 1.250,00 €\nProbezeit drei Monate.\n"
    )
    assert looks_like_financial_document(text) is False
