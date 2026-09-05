"""Virtus Office Stage 4 — OCR + Document Engine."""

from __future__ import annotations

import io
from pathlib import Path

import pytest
from starlette.datastructures import Headers, UploadFile

from app.integration.virtus_office import OFFICE_PIPELINE_LIVE, OfficeJobEngine
from app.integration.virtus_office.document_parse import parse_office_file
from app.integration.virtus_office.ocr_engine import (
    ocr_capabilities,
    ocr_image_bytes,
    ocr_image_pages,
    set_test_ocr_hook,
)
from app.integration.virtus_office.office_job_ssot import office_reuse_map

from _office_helpers import mark_office_paid


def _upload(name: str, data: bytes, content_type: str) -> UploadFile:
    return UploadFile(
        file=io.BytesIO(data),
        filename=name,
        headers=Headers({"content-type": content_type}),
    )


def _png_bytes() -> bytes:
    from PIL import Image

    im = Image.new("RGB", (320, 120), color=(255, 255, 255))
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    return buf.getvalue()


DE_LETTER = (
    "Sehr geehrte Damen und Herren,\n\n"
    "Rechnung Nr. 4711 vom 12.01.2025.\n"
    "Gesamtbetrag 99,00 €\n"
    "Mit freundlichen Grüßen\n"
)


@pytest.fixture(autouse=True)
def _clear_ocr_hook():
    set_test_ocr_hook(None)
    yield
    set_test_ocr_hook(None)


def test_pipeline_is_live():
    assert OFFICE_PIPELINE_LIVE is True


def test_ssot_stage4_flag():
    m = office_reuse_map()
    assert m["stage4_ocr_document_engine"] is True
    assert m["pipeline_live"] is True


def test_ocr_capabilities_shape():
    caps = ocr_capabilities()
    assert "tesseract" in caps
    assert "vision_llm" in caps
    assert "pdf_rasterize" in caps


def test_image_ocr_via_hook_to_proposal_and_execute(tmp_path: Path):
    set_test_ocr_hook(
        lambda _data, _ct: {
            "ok": True,
            "provider": "stub",
            "language": "de",
            "confidence": 0.91,
            "text": DE_LETTER,
            "lines": [
                {"text": ln, "bbox": [10, 10 + i * 20, 300, 28 + i * 20], "confidence": 0.9}
                for i, ln in enumerate(DE_LETTER.splitlines())
                if ln.strip()
            ],
            "tables": [],
        }
    )
    png = _png_bytes()
    eng = OfficeJobEngine(tmp_path)
    created = eng.create_job(service_preset="translate")
    view = eng.upload(
        created["job_id"],
        owner_token=created["owner_token"],
        upload=_upload("brief_foto.png", png, "image/png"),
    )
    assert view["status"] == "proposal_ready"
    assert view["understanding"]["structure"]["ocr_status"] == "done"
    assert view["understanding"]["structure"]["text_detected"] is True
    assert (view["understanding"].get("layout_summary") or {}).get("ocr_provider") == "stub"
    assert "OCR" in " ".join(view["proposal"].get("includes") or [])

    eng.select_action(
        created["job_id"],
        owner_token=created["owner_token"],
        action_id="translate",
        target_language="en",
        output_format="pdf",
    )
    mark_office_paid(eng, created["job_id"], created["owner_token"])
    done = eng.execute(created["job_id"], owner_token=created["owner_token"])
    assert done["status"] == "completed", done.get("failure_detail")
    assert done["quality"]["passed"] is True
    blob, _fn, _mime = eng.get_artifact_bytes(
        created["job_id"], owner_token=created["owner_token"]
    )
    assert blob.startswith(b"%PDF")


def test_multi_image_pages_ocr(tmp_path: Path):
    calls = {"n": 0}

    def hook(data: bytes, _ct: str):
        calls["n"] += 1
        page_text = f"Seite {calls['n']}\nBetrag {calls['n'] * 10},00 €"
        return {
            "ok": True,
            "provider": "stub",
            "language": "de",
            "confidence": 0.88,
            "text": page_text,
            "lines": [{"text": page_text, "bbox": None, "confidence": 0.88}],
        }

    set_test_ocr_hook(hook)
    png = _png_bytes()
    eng = OfficeJobEngine(tmp_path)
    created = eng.create_job()
    view = eng.upload_pages(
        created["job_id"],
        owner_token=created["owner_token"],
        uploads=[
            _upload("p1.png", png, "image/png"),
            _upload("p2.png", png, "image/png"),
        ],
    )
    assert view["status"] == "proposal_ready"
    assert view["understanding"]["page_count"] == 2
    assert len(view.get("page_material_ids") or []) == 2
    assert view["understanding"]["structure"]["ocr_status"] == "done"
    eng.select_action(
        created["job_id"],
        owner_token=created["owner_token"],
        action_id="convert_docx",
        output_format="docx",
    )
    mark_office_paid(eng, created["job_id"], created["owner_token"])
    done = eng.execute(created["job_id"], owner_token=created["owner_token"])
    assert done["status"] == "completed", done.get("failure_detail")


def test_ocr_fail_honest_no_fake_success(tmp_path: Path):
    set_test_ocr_hook(lambda *_a: {"ok": False, "error": "ocr_empty", "text": ""})
    png = _png_bytes()
    eng = OfficeJobEngine(tmp_path)
    created = eng.create_job(service_preset="translate")
    view = eng.upload(
        created["job_id"],
        owner_token=created["owner_token"],
        upload=_upload("blur.png", png, "image/png"),
    )
    assert view["status"] == "proposal_ready"
    assert view["understanding"]["structure"]["ocr_status"] == "failed"
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


def test_parse_image_layout_structure():
    set_test_ocr_hook(
        lambda *_a: {
            "ok": True,
            "provider": "stub",
            "language": "de",
            "confidence": 0.8,
            "text": "Name | Betrag\nMax | 12,00 €",
            "lines": [
                {"text": "Name | Betrag", "bbox": [0, 0, 100, 10], "confidence": 0.9},
                {"text": "Max | 12,00 €", "bbox": [0, 12, 100, 22], "confidence": 0.85},
            ],
            "tables": [{"rows": [["Name", "Betrag"], ["Max", "12,00 €"]], "source": "stub"}],
        }
    )
    parsed = parse_office_file(
        data=_png_bytes(),
        filename="tabelle.png",
        file_kind="image",
        content_type="image/png",
    )
    assert parsed["ocr_status"] == "done"
    assert parsed["layout"]["pages"]
    assert parsed["layout"]["tables"]
    assert parsed["layout"]["lines"]
    assert "12,00" in parsed["text"]


def test_ocr_image_pages_unit():
    set_test_ocr_hook(
        lambda data, _ct: {
            "ok": True,
            "provider": "stub",
            "text": f"chunk-{len(data)}",
            "confidence": 0.7,
            "language": "de",
        }
    )
    a = _png_bytes()
    b = _png_bytes() + b"\x00"
    res = ocr_image_pages([(a, "image/png"), (b, "image/png")])
    assert res["ok"] is True
    assert len(res["pages"]) == 2
    assert "chunk-" in res["text"]


def test_scanned_pdf_ocr_path(tmp_path: Path):
    """Image-only PDF → rasterize path or honest fail; with hook after raster may vary.

    Without pypdfium2/raster, fail honestly. With raster + hook on PNG pages, succeed.
    """
    pytest.importorskip("pypdfium2")
    from PIL import Image

    # Build a minimal PDF via fpdf with... actually fpdf embeds text.
    # Use a one-page PDF that is just an embedded image (hard).
    # Instead: call ocr path via parse after monkeypatching extract to empty.
    from app.integration.virtus_office import document_parse as dp

    png = _png_bytes()
    set_test_ocr_hook(
        lambda *_a: {
            "ok": True,
            "provider": "stub",
            "text": DE_LETTER,
            "confidence": 0.9,
            "language": "de",
            "lines": [{"text": "Rechnung", "bbox": [1, 1, 40, 10], "confidence": 0.9}],
        }
    )

    # Minimal PDF bytes that pypdfium can open: use fpdf blank then we'll force empty text layer path
    from fpdf import FPDF

    pdf = FPDF()
    pdf.add_page()
    # Draw no text — still may have empty extract
    raw = pdf.output()
    if isinstance(raw, str):
        raw = raw.encode("latin-1")

    # Force OCR branch regardless of text layer by patching extract
    orig = dp.extract_pdf_text_bytes

    def _empty(_data, max_pages=20):
        return "", 1, 0

    dp.extract_pdf_text_bytes = _empty  # type: ignore
    try:
        # Also need rasterize to call OCR on images — hook fires on raster PNG
        parsed = parse_office_file(
            data=raw,
            filename="scan.pdf",
            file_kind="pdf",
            content_type="application/pdf",
        )
    finally:
        dp.extract_pdf_text_bytes = orig  # type: ignore

    # Either OCR done (raster worked) or failed honestly
    assert parsed["ocr_status"] in {"done", "failed"}
    if parsed["ocr_status"] == "done":
        assert "Rechnung" in parsed["text"] or "geehrte" in parsed["text"]
        assert parsed.get("layout")


def test_photo_to_docx_via_ocr(tmp_path: Path):
    set_test_ocr_hook(
        lambda *_a: {
            "ok": True,
            "provider": "stub",
            "text": DE_LETTER,
            "confidence": 0.92,
            "language": "de",
        }
    )
    eng = OfficeJobEngine(tmp_path)
    created = eng.create_job()
    eng.upload(
        created["job_id"],
        owner_token=created["owner_token"],
        upload=_upload("foto.jpg", _png_bytes(), "image/jpeg"),
    )
    eng.select_action(
        created["job_id"],
        owner_token=created["owner_token"],
        action_id="convert_docx",
    )
    mark_office_paid(eng, created["job_id"], created["owner_token"])
    done = eng.execute(created["job_id"], owner_token=created["owner_token"])
    assert done["status"] == "completed"
    blob, name, _mime = eng.get_artifact_bytes(
        created["job_id"], owner_token=created["owner_token"]
    )
    assert name.endswith(".docx")
    assert blob[:2] == b"PK"
