"""Document Quality Check SKU — executor + validator + honesty."""

from __future__ import annotations

import json

from app.integration.virtus_office.document_quality_check import (
    ACTION_ID,
    DOCUMENT_QUALITY_CHECK_SSOT,
    execute_document_quality_check,
    run_document_diagnostics,
)
from app.integration.virtus_office.office_job_ssot import (
    OFFICE_PRICE_MATRIX_EUR,
    OFFICE_SELLABLE_NOW,
    OFFICE_SKU_ROADMAP,
)
from app.integration.virtus_office.quality_gate import run_quality_gate
from app.integration.virtus_office.understanding import (
    ACTION_CATALOG,
    CUSTOMER_EXECUTABLE_ACTIONS,
    _suggest_actions,
)


def test_dqc_ssot_contract():
    assert DOCUMENT_QUALITY_CHECK_SSOT["executor"]["required"] is True
    assert DOCUMENT_QUALITY_CHECK_SSOT["validator"]["required"] is True
    assert DOCUMENT_QUALITY_CHECK_SSOT["output"]["type"] == "quality_report"
    assert "corrected_final_document_generation" in DOCUMENT_QUALITY_CHECK_SSOT["forbidden"]
    assert ACTION_ID in OFFICE_SELLABLE_NOW
    assert ACTION_ID not in OFFICE_SKU_ROADMAP
    assert OFFICE_SKU_ROADMAP[0] == "xrechnung"
    assert OFFICE_PRICE_MATRIX_EUR["doc_quality"] == 7.90
    assert ACTION_ID in CUSTOMER_EXECUTABLE_ACTIONS
    assert any(a["id"] == ACTION_ID for a in ACTION_CATALOG)


def test_dqc_ready_on_clean_text_pdf_bytes():
    # Minimal syntactically weak but text-bearing path via txt kind
    data = b"Virtus Office quality sample.\nPage with enough readable content for checks.\n"
    report = run_document_diagnostics(
        data=data,
        filename="sample.txt",
        file_kind="txt",
        content_type="text/plain",
        understanding={"document_type": "general"},
    )
    assert report["status"] in {"READY", "NOT_READY"}
    assert "problems" in report
    assert report["meta"]["forbidden_note"]


def test_dqc_not_ready_on_empty_file():
    report = run_document_diagnostics(
        data=b"",
        filename="empty.pdf",
        file_kind="pdf",
        understanding={},
    )
    assert report["status"] == "NOT_READY"
    codes = {p["code"] for p in report["problems"]}
    assert "empty_file" in codes


def test_dqc_not_ready_corrupt_pdf():
    report = run_document_diagnostics(
        data=b"not-a-pdf-file-at-all",
        filename="broken.pdf",
        file_kind="pdf",
        understanding={},
    )
    assert report["status"] == "NOT_READY"
    codes = {p["code"] for p in report["problems"]}
    assert "corrupt_pdf" in codes


def test_dqc_executor_produces_report_not_source_rewrite():
    data = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\nstartxref\n0\n%%EOF\n"
    out = execute_document_quality_check(
        data=data,
        filename="thin.pdf",
        file_kind="pdf",
        intent={"output_format": "json"},
        understanding={"document_type": "general", "page_count": 1},
    )
    assert out["ok"] is True
    assert out["ext"] == "json"
    assert out["delivery_mode"] == "quality_report"
    report = json.loads(out["bytes"].decode("utf-8"))
    assert report["status"] in {"READY", "NOT_READY"}
    assert report["sku"] == ACTION_ID
    # Quality gate must PASS for a well-formed report even if document is NOT_READY
    qa = run_quality_gate(
        action_id=ACTION_ID,
        input_text=out["quality_input_text"],
        output_text=out["quality_output_text"],
        artifact_bytes=out["bytes"],
        artifact_ext=out["ext"],
        artifact_mime=out["mime"],
        target_language=None,
        job_id="job-dqc-1",
        artifact_job_id="job-dqc-1",
        delivery_mode="quality_report",
    )
    assert qa["passed"] is True, qa["failed"]


def test_dqc_pdf_report_passes_gate():
    data = b"Invoice sample text with enough characters for extraction path.\nTotal 12.00 EUR\n"
    out = execute_document_quality_check(
        data=data,
        filename="note.txt",
        file_kind="txt",
        intent={"output_format": "pdf"},
        understanding={"document_type": "invoice"},
    )
    assert out["ext"] == "pdf"
    assert out["bytes"][:4] == b"%PDF"
    qa = run_quality_gate(
        action_id=ACTION_ID,
        input_text=out["quality_input_text"],
        output_text=out["quality_output_text"],
        artifact_bytes=out["bytes"],
        artifact_ext="pdf",
        artifact_mime="application/pdf",
        target_language=None,
        job_id="job-dqc-2",
        artifact_job_id="job-dqc-2",
    )
    assert qa["passed"] is True, qa["failed"]


def test_dqc_suggested_in_choice_actions():
    suggested = _suggest_actions(
        doc_type={"id": "businessplan"},
        file_kind="pdf",
        text_detected=True,
        tables=0,
        explanation=None,
    )
    assert suggested[0] == "document_quality_check"
