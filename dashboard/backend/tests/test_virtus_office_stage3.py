"""Virtus Office Stage 3 — execute + quality gate + artifact."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pytest
from starlette.datastructures import Headers, UploadFile

from app.integration.virtus_office import OFFICE_PIPELINE_LIVE, OfficeJobEngine, OfficeJobError

from _office_helpers import mark_office_paid


def _upload(name: str, data: bytes, content_type: str) -> UploadFile:
    return UploadFile(
        file=BytesIO(data),
        filename=name,
        headers=Headers({"content-type": content_type}),
    )


def _run_to_proposal(eng: OfficeJobEngine, *, preset: str | None, name: str, body: bytes, ctype: str):
    created = eng.create_job(service_preset=preset)
    view = eng.upload(
        created["job_id"],
        owner_token=created["owner_token"],
        upload=_upload(name, body, ctype),
    )
    return created, view


def test_pipeline_is_live():
    assert OFFICE_PIPELINE_LIVE is True


def test_translate_de_to_uk_pdf(tmp_path: Path):
    eng = OfficeJobEngine(tmp_path)
    text = (
        "Arbeitsvertrag\n\n"
        "Arbeitgeber: Muster GmbH\n"
        "Arbeitnehmer: Max Mustermann\n"
        "Datum: 01.03.2024\n"
        "Gesamtbetrag 1.250,00 €\n"
        "Probezeit drei Monate.\n"
    ).encode("utf-8")
    created, view = _run_to_proposal(
        eng, preset="translate", name="Arbeitsvertrag.txt", body=text, ctype="text/plain"
    )
    assert view["status"] == "proposal_ready"
    configured = eng.select_action(
        created["job_id"],
        owner_token=created["owner_token"],
        action_id="translate",
        target_language="uk",
        output_format="pdf",
    )
    assert configured["proposal"]["next_step"] == "awaiting_stage3"
    mark_office_paid(eng, created["job_id"], created["owner_token"])
    done = eng.execute(created["job_id"], owner_token=created["owner_token"])
    assert done["status"] == "completed", done.get("failure_detail")
    assert done["quality"]["passed"] is True
    assert done["artifact"]["ext"] == "pdf"
    assert done["artifact_download"]
    blob, _fn, _mime = eng.get_artifact_bytes(
        created["job_id"], owner_token=created["owner_token"]
    )
    assert blob.startswith(b"%PDF")


def test_convert_docx(tmp_path: Path):
    eng = OfficeJobEngine(tmp_path)
    created, _ = _run_to_proposal(
        eng,
        preset=None,
        name="brief.txt",
        body=b"Sehr geehrte Damen und Herren,\n\nRechnung Nr. 99 vom 12.01.2025.\nBetrag 40,00 EUR.\n",
        ctype="text/plain",
    )
    eng.select_action(
        created["job_id"],
        owner_token=created["owner_token"],
        action_id="convert_docx",
        output_format="docx",
    )
    mark_office_paid(eng, created["job_id"], created["owner_token"])
    done = eng.execute(created["job_id"], owner_token=created["owner_token"])
    assert done["status"] == "completed", done.get("failure_detail")
    blob, name, mime = eng.get_artifact_bytes(
        created["job_id"], owner_token=created["owner_token"]
    )
    assert name.endswith(".docx")
    assert blob[:2] == b"PK"
    assert "wordprocessingml" in mime or "openxmlformats" in mime


def test_extract_xlsx(tmp_path: Path):
    eng = OfficeJobEngine(tmp_path)
    created, _ = _run_to_proposal(
        eng,
        preset=None,
        name="kosten.csv",
        body=b"Datum,Kategorie,Betrag\n01.02.2024,Miete,800.00\n02.02.2024,Essen,45.50\n",
        ctype="text/csv",
    )
    eng.select_action(
        created["job_id"],
        owner_token=created["owner_token"],
        action_id="extract_data",
    )
    mark_office_paid(eng, created["job_id"], created["owner_token"])
    done = eng.execute(created["job_id"], owner_token=created["owner_token"])
    assert done["status"] == "completed", done.get("failure_detail")
    blob, name, _mime = eng.get_artifact_bytes(
        created["job_id"], owner_token=created["owner_token"]
    )
    assert name.endswith(".xlsx")
    assert blob[:2] == b"PK"


def test_foreign_token_cannot_download(tmp_path: Path):
    eng = OfficeJobEngine(tmp_path)
    created, _ = _run_to_proposal(
        eng,
        preset="translate",
        name="a.txt",
        body=b"Rechnung Gesamtbetrag 10,00 EUR Datum 01.01.2024 GmbH und Vertrag",
        ctype="text/plain",
    )
    eng.select_action(
        created["job_id"],
        owner_token=created["owner_token"],
        action_id="translate",
        target_language="en",
        output_format="pdf",
    )
    mark_office_paid(eng, created["job_id"], created["owner_token"])
    eng.execute(created["job_id"], owner_token=created["owner_token"])
    other = eng.create_job()
    with pytest.raises(OfficeJobError) as exc:
        eng.get_artifact_bytes(created["job_id"], owner_token=other["owner_token"])
    assert exc.value.code == "forbidden"


def test_unsupported_action_explain(tmp_path: Path):
    eng = OfficeJobEngine(tmp_path)
    created, _ = _run_to_proposal(
        eng,
        preset=None,
        name="x.txt",
        body=b"Der Vertrag und die Rechnung mit Datum 01.01.2024",
        ctype="text/plain",
    )
    with pytest.raises(OfficeJobError) as exc:
        eng.select_action(
            created["job_id"],
            owner_token=created["owner_token"],
            action_id="explain",
        )
    assert exc.value.code == "action_not_available"


def test_ocr_pending_image_fails_execution(tmp_path: Path):
    """Without OCR success, image execution must fail honestly (Stage 4)."""
    from app.integration.virtus_office.ocr_engine import set_test_ocr_hook

    set_test_ocr_hook(lambda *_a: {"ok": False, "error": "ocr_empty", "text": ""})
    try:
        png = bytes.fromhex(
            "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
            "0000000a49444154789c63000100000500010d0a2db40000000049454e44ae426082"
        )
        eng = OfficeJobEngine(tmp_path)
        created = eng.create_job(service_preset="translate")
        eng.upload(
            created["job_id"],
            owner_token=created["owner_token"],
            upload=_upload("scan.png", png, "image/png"),
        )
        eng.select_action(
            created["job_id"],
            owner_token=created["owner_token"],
            action_id="translate",
            target_language="en",
            output_format="pdf",
        )
        mark_office_paid(eng, created["job_id"], created["owner_token"])
        done = eng.execute(created["job_id"], owner_token=created["owner_token"])
        assert done["status"] == "failed"
        assert done["failure_reason"] == "ocr_failed"
    finally:
        set_test_ocr_hook(None)
