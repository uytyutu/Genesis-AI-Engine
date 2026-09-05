"""Virtus Office Stage 2 — understanding → intent → proposal."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pytest
from starlette.datastructures import Headers, UploadFile

from app.integration.virtus_office import (
    OFFICE_PIPELINE_LIVE,
    STAGE2_SUCCESS_STATUS,
    OfficeJobEngine,
    OfficeJobError,
    catalog_public,
)
from app.integration.virtus_office.language_detect import detect_source_language
from app.integration.virtus_office.understanding import build_understanding


def _upload(name: str, data: bytes, content_type: str) -> UploadFile:
    return UploadFile(
        file=BytesIO(data),
        filename=name,
        headers=Headers({"content-type": content_type}),
    )


def test_pipeline_still_off_and_catalog_expandable():
    assert OFFICE_PIPELINE_LIVE is True
    cat = catalog_public()
    assert cat["source_default"] == "auto"
    codes = {r["code"] for r in cat["languages"]}
    assert {"de", "en", "uk", "ru", "tr", "fr"}.issubset(codes)


def test_detect_german_and_ukrainian():
    de = detect_source_language(
        "Der Arbeitgeber und der Arbeitnehmer schließen diesen Arbeitsvertrag.",
        filename="Arbeitsvertrag.pdf",
    )
    assert de["code"] == "de"
    uk = detect_source_language("Договір та рахунок для України", filename="x.pdf")
    assert uk["code"] == "uk"


def test_upload_reaches_proposal_ready_with_choice_cards(tmp_path: Path):
    eng = OfficeJobEngine(tmp_path)
    created = eng.create_job()
    text = (
        "Arbeitsvertrag\nArbeitgeber GmbH\nArbeitnehmer Max Mustermann\n"
        "Probezeit drei Monate. Der Vertrag gilt ab dem Datum."
    )
    view = eng.upload(
        created["job_id"],
        owner_token=created["owner_token"],
        upload=_upload("Arbeitsvertrag.txt", text.encode("utf-8"), "text/plain"),
    )
    assert view["status"] == STAGE2_SUCCESS_STATUS
    assert view["stage2_complete"] is True
    assert view["understanding"]["filled"] is True
    assert view["understanding"]["document_type"] == "employment_contract"
    assert view["understanding"]["language"] == "de"
    assert view["proposal"]["filled"] is True
    assert view["proposal"]["payment_enabled"] is False
    assert view["proposal"]["show_choice_cards"] is True
    assert view["artifact_download"] is None


def test_translate_preset_skips_to_configure(tmp_path: Path):
    eng = OfficeJobEngine(tmp_path)
    created = eng.create_job(service_preset="translate")
    assert created["service_preset"] == "translate"
    view = eng.upload(
        created["job_id"],
        owner_token=created["owner_token"],
        upload=_upload(
            "Rechnung.txt",
            "Rechnung Nr. 12 Gesamtbetrag 100 EUR MwSt GmbH".encode("utf-8"),
            "text/plain",
        ),
    )
    assert view["status"] == "proposal_ready"
    assert view["understanding"]["intent"]["id"] == "translate"
    assert view["understanding"]["intent"]["locked"] is True
    assert view["proposal"]["next_step"] == "configure_translate"

    configured = eng.select_action(
        created["job_id"],
        owner_token=created["owner_token"],
        action_id="translate",
        target_language="uk",
        output_format="pdf",
    )
    assert configured["proposal"]["target_language"] == "uk"
    assert configured["proposal"]["price_eur"] == 7.9
    assert configured["proposal"]["next_step"] == "awaiting_stage3"

    from _office_helpers import mark_office_paid

    mark_office_paid(eng, created["job_id"], created["owner_token"])
    stub = eng.continue_stub(created["job_id"], owner_token=created["owner_token"])
    assert stub["status"] == "completed"
    assert stub["stage3_complete"] is True
    assert stub["quality"]["passed"] is True
    assert stub["artifact_download"]
    assert stub["payment"]["paid"] is True
    data, name, mime = eng.get_artifact_bytes(
        created["job_id"], owner_token=created["owner_token"]
    )
    assert data[:4] == b"%PDF"
    assert "pdf" in mime
    assert name.endswith(".pdf")


def test_image_ocr_failed_without_provider(tmp_path: Path):
    # 1x1 PNG — no OCR provider / empty result → honest failed (Stage 4)
    png = bytes.fromhex(
        "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
        "0000000a49444154789c63000100000500010d0a2db40000000049454e44ae426082"
    )
    eng = OfficeJobEngine(tmp_path)
    created = eng.create_job()
    view = eng.upload(
        created["job_id"],
        owner_token=created["owner_token"],
        upload=_upload("scan.png", png, "image/png"),
    )
    assert view["status"] == "proposal_ready"
    assert view["understanding"]["structure"]["ocr_status"] == "failed"
    assert view["understanding"]["structure"]["text_detected"] is False
    assert view["proposal"]["show_choice_cards"] is True


def test_csv_and_docx_strategies(tmp_path: Path):
    eng = OfficeJobEngine(tmp_path)
    c = eng.create_job()
    csv_view = eng.upload(
        c["job_id"],
        owner_token=c["owner_token"],
        upload=_upload("data.csv", b"a,b,c\n1,2,3\n4,5,6\n", "text/csv"),
    )
    assert csv_view["file_kind"] == "csv"
    assert csv_view["understanding"]["structure"]["tables"] >= 1

    # Minimal DOCX zip
    import zipfile
    from io import BytesIO

    buf = BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"></Types>',
        )
        zf.writestr(
            "word/document.xml",
            '<?xml version="1.0"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            "<w:body><w:p><w:r><w:t>Lebenslauf Berufserfahrung Schulbildung</w:t></w:r></w:p></w:body></w:document>",
        )
    d = eng.create_job()
    docx_view = eng.upload(
        d["job_id"],
        owner_token=d["owner_token"],
        upload=_upload(
            "CV.docx",
            buf.getvalue(),
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ),
    )
    assert docx_view["file_kind"] == "docx"
    assert docx_view["understanding"]["document_type"] == "cv_lebenslauf"


def test_continue_requires_action(tmp_path: Path):
    eng = OfficeJobEngine(tmp_path)
    created = eng.create_job()
    eng.upload(
        created["job_id"],
        owner_token=created["owner_token"],
        upload=_upload("x.txt", b"hello world and the company invoice", "text/plain"),
    )
    with pytest.raises(OfficeJobError) as exc:
        eng.continue_stub(created["job_id"], owner_token=created["owner_token"])
    assert exc.value.code == "action_required"


def test_build_understanding_pdf_bytes_reuse():
    from pypdf import PdfWriter

    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    buf = BytesIO()
    writer.write(buf)
    u = build_understanding(
        data=buf.getvalue(),
        filename="scan.pdf",
        file_kind="pdf",
        content_type="application/pdf",
    )
    assert u["filled"] is True
    # Blank PDF: text layer empty → Stage 4 OCR attempt (done or failed)
    assert u["structure"]["ocr_status"] in {"done", "failed"}
    assert u["structure"]["parse_strategy"] in {
        "knowledge_intake_pdf",
        "pdf_scan_ocr",
        "pdf_ocr_after_parse_error",
    } or u["structure"]["ocr_status"] == "failed"
