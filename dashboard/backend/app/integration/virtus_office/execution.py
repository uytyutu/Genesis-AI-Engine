"""Stage 3 executors — translate, convert_docx, extract_data (XLSX)."""

from __future__ import annotations

import re
from typing import Any

from app.integration.virtus_office.artifact_writers import (
    artifact_filename,
    write_csv_bytes,
    write_docx_bytes,
    write_pdf_bytes,
    write_xlsx_bytes,
)
from app.integration.virtus_office.bewerbung_generate import generate_bewerbung_artifacts
from app.integration.virtus_office.bewerbung_profile import profile_facts_index
from app.integration.virtus_office.bewerbung_ssot import BEWERBUNG_ACTION_IDS
from app.integration.virtus_office.document_parse import parse_office_file
from app.integration.virtus_office.language_catalog import language_label_de
from app.integration.virtus_office.translator import translate_text

MIME = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "csv": "text/csv",
    "txt": "text/plain",
    "zip": "application/zip",
}

# Single source for job_engine execute gate + capability audit.
EXECUTABLE_ACTION_IDS: frozenset[str] = frozenset(
    {
        "translate",
        "convert_docx",
        "extract_data",
        "document_quality_check",
    }
) | set(BEWERBUNG_ACTION_IDS)


def load_source_text(
    *,
    data: bytes,
    filename: str,
    file_kind: str,
    content_type: str,
    extra_pages: list[tuple[bytes, str]] | None = None,
) -> dict[str, Any]:
    parsed = parse_office_file(
        data=data,
        filename=filename,
        file_kind=file_kind,
        content_type=content_type,
        extra_pages=extra_pages,
    )
    text = str(parsed.get("text") or "").strip()
    ocr_status = parsed.get("ocr_status")
    if not text and ocr_status == "failed":
        ocr = parsed.get("ocr") or {}
        return {
            "ok": False,
            "error": "ocr_failed",
            "detail": str(ocr.get("detail") or ocr.get("error") or "OCR fehlgeschlagen"),
            "parsed": parsed,
            "text": "",
        }
    if not text and ocr_status == "pending":
        # Legacy pending should not appear after Stage 4; keep honest guard.
        return {
            "ok": False,
            "error": "ocr_failed",
            "detail": "Scan/Foto ohne Text — OCR nicht abgeschlossen.",
            "parsed": parsed,
            "text": "",
        }
    if not text:
        return {
            "ok": False,
            "error": "no_text",
            "detail": "Kein extrahierbarer Text im Dokument.",
            "parsed": parsed,
            "text": "",
        }
    return {"ok": True, "text": text, "parsed": parsed, "error": None, "detail": None}


def execute_office_action(
    *,
    action_id: str,
    data: bytes,
    filename: str,
    file_kind: str,
    content_type: str,
    intent: dict[str, Any],
    understanding: dict[str, Any],
    extra_pages: list[tuple[bytes, str]] | None = None,
    profile: dict[str, Any] | None = None,
    photo_bytes: bytes | None = None,
) -> dict[str, Any]:
    """Return execution result dict (bytes + meta) or error."""
    action = (action_id or "").strip().lower()

    if action in BEWERBUNG_ACTION_IDS:
        return _exec_bewerbung(
            action_id=action,
            profile=profile or {},
            photo_bytes=photo_bytes,
            intent=intent,
        )

    if action == "document_quality_check":
        from app.integration.virtus_office.document_quality_check import (
            execute_document_quality_check,
        )

        return execute_document_quality_check(
            data=data,
            filename=filename,
            file_kind=file_kind,
            content_type=content_type,
            intent=intent,
            understanding=understanding,
            extra_pages=extra_pages,
        )

    source = load_source_text(
        data=data,
        filename=filename,
        file_kind=file_kind,
        content_type=content_type,
        extra_pages=extra_pages,
    )
    if not source["ok"]:
        return {
            "ok": False,
            "error": source["error"],
            "detail": source["detail"],
            "quality_input_text": "",
            "quality_output_text": "",
        }

    text = source["text"]

    if action == "translate":
        return _exec_translate(
            text=text,
            filename=filename,
            intent=intent,
            understanding=understanding,
            parsed=source.get("parsed") or {},
            source_bytes=data,
            file_kind=file_kind,
        )
    if action == "convert_docx":
        return _exec_docx(text=text, filename=filename, understanding=understanding)
    if action == "extract_data":
        return _exec_xlsx(text=text, filename=filename, file_kind=file_kind, understanding=understanding)

    return {
        "ok": False,
        "error": "unsupported_action",
        "detail": f"Aktion noch nicht unterstützt: {action}",
        "quality_input_text": text,
        "quality_output_text": "",
    }


def _exec_bewerbung(
    *,
    action_id: str,
    profile: dict[str, Any],
    photo_bytes: bytes | None,
    intent: dict[str, Any],
) -> dict[str, Any]:
    out_fmt = str(intent.get("output_format") or "pdf").lower()
    gen = generate_bewerbung_artifacts(
        action_id=action_id,
        profile=profile,
        photo_bytes=photo_bytes,
        output_format=out_fmt,
    )
    if not gen.get("ok"):
        return {
            "ok": False,
            "error": gen.get("error") or "bewerbung_failed",
            "detail": gen.get("detail") or "Bewerbung konnte nicht erzeugt werden",
            "quality_input_text": "",
            "quality_output_text": "",
        }
    return {
        **gen,
        "translation_provider": None,
        "target_language": "de",
        "profile_facts": profile_facts_index(profile),
    }


def _exec_translate(
    *,
    text: str,
    filename: str,
    intent: dict[str, Any],
    understanding: dict[str, Any],
    parsed: dict[str, Any] | None = None,
    source_bytes: bytes | None = None,
    file_kind: str | None = None,
) -> dict[str, Any]:
    tgt = str(intent.get("target_language") or "").lower().split("-")[0]
    if not tgt or tgt in {"auto", "unknown"}:
        return {
            "ok": False,
            "error": "target_language_required",
            "detail": "Zielsprache fehlt",
            "quality_input_text": text,
            "quality_output_text": "",
        }
    src = str(
        intent.get("source_language_override")
        or (
            intent.get("source_language")
            if intent.get("source_language") not in {None, "", "auto", "unknown"}
            else None
        )
        or intent.get("detected_source_language")
        or understanding.get("language")
        or "auto"
    )
    out_fmt = str(intent.get("output_format") or "pdf").lower()
    if out_fmt not in {"pdf", "docx", "txt"}:
        out_fmt = "pdf"

    from app.integration.virtus_office.document_settings import apply_text_replacements
    from app.integration.virtus_office.financial_fields import validate_financial_fields

    settings = intent.get("document_settings") if isinstance(intent.get("document_settings"), dict) else {}
    work_text = apply_text_replacements(text, settings)
    preserve_names = True
    preserve_numbers_dates = True
    for op in settings.get("ops") or []:
        if not isinstance(op, dict):
            continue
        if op.get("id") == "preserve_names" and op.get("to") is False:
            preserve_names = False
        if op.get("id") == "preserve_numbers_dates" and op.get("to") is False:
            preserve_numbers_dates = False
    if "preserve_names" in (settings.get("values") or {}):
        preserve_names = bool(settings["values"]["preserve_names"])
    if "preserve_numbers_dates" in (settings.get("values") or {}):
        preserve_numbers_dates = bool(settings["values"]["preserve_numbers_dates"])

    parsed = parsed or {}
    ocr_meta = parsed.get("ocr") if isinstance(parsed.get("ocr"), dict) else {}
    financial_qa = parsed.get("financial_qa") or ocr_meta.get("financial_qa")
    if not financial_qa:
        financial_qa = validate_financial_fields(
            work_text, confidence=ocr_meta.get("confidence")
        )

    dtype = str(understanding.get("document_type") or "")
    ocr_status = str(parsed.get("ocr_status") or "")
    financial_hard_gate = dtype == "invoice" or ocr_status == "done"
    if (
        financial_hard_gate
        and financial_qa.get("is_financial")
        and not financial_qa.get("passed")
    ):
        return {
            "ok": False,
            "error": "financial_ocr_needs_review",
            "detail": financial_qa.get("warning_de")
            or "Finanzfelder unsicher — bitte prüfen, bevor die Übersetzung fortgesetzt wird.",
            "quality_input_text": work_text,
            "quality_output_text": "",
            "ocr_financial_qa": financial_qa,
            "document_type": dtype,
            "source_page_count": parsed.get("page_count") or understanding.get("page_count"),
            "source_image_count": parsed.get("images") or 0,
            "delivery_mode": "blocked_financial_review",
        }

    src_pages = parsed.get("page_count") or understanding.get("page_count")
    src_imgs = int(parsed.get("images") or 0)
    title = f"Translation · {language_label_de(tgt)}"

    # A-lite presentation rebuild for Businessplan / rich multi-page PDFs
    use_presentation = _should_use_presentation_rebuild(
        dtype=dtype,
        file_kind=file_kind or "",
        out_fmt=out_fmt,
        source_bytes=source_bytes,
        page_count=int(src_pages or 0),
        image_count=src_imgs,
    )
    if use_presentation and source_bytes:
        from app.integration.virtus_office.presentation_rebuild import (
            extract_presentation_pdf,
            rebuild_presentation_pdf,
            translate_presentation_pages,
        )

        extracted = extract_presentation_pdf(source_bytes)
        if not extracted.get("ok"):
            return {
                "ok": False,
                "error": extracted.get("error") or "presentation_extract_failed",
                "detail": extracted.get("detail") or "Presentation extract failed",
                "quality_input_text": work_text,
                "quality_output_text": "",
                "document_type": dtype,
                "source_page_count": src_pages,
                "source_image_count": src_imgs,
                "delivery_mode": "presentation_rebuild",
            }

        # Apply date/name replacements on each page text before translate
        pages = []
        for pg in extracted.get("pages") or []:
            pg2 = dict(pg)
            pg2["text"] = apply_text_replacements(str(pg.get("text") or ""), settings)
            # Drop binary-heavy spans from translate payload; keep images for rebuild
            pages.append(pg2)

        tr_pages = translate_presentation_pages(
            pages,
            source_language=src,
            target_language=tgt,
            preserve_names=preserve_names,
            preserve_numbers_dates=preserve_numbers_dates,
        )
        if not tr_pages.get("ok"):
            return {
                "ok": False,
                "error": tr_pages.get("error") or "translate_failed",
                "detail": tr_pages.get("detail") or "Presentation translate failed",
                "quality_input_text": tr_pages.get("quality_input_text") or work_text,
                "quality_output_text": "",
                "document_type": dtype,
                "source_page_count": extracted.get("page_count") or src_pages,
                "source_image_count": extracted.get("image_count") or src_imgs,
                "delivery_mode": "presentation_rebuild",
            }

        meta = [
            f"Source file: {filename}",
            f"Source language: {src}",
            f"Target language: {tgt}",
            f"Provider: {tr_pages.get('provider')}",
            "Delivery: presentation-grade rebuild (not pixel-perfect)",
            f"Pages: {extracted.get('page_count')} · Images: {extracted.get('image_count')}",
        ]
        rebuilt = rebuild_presentation_pdf(
            list(tr_pages.get("pages") or []),
            title=title,
            meta_lines=meta,
        )
        if not rebuilt.get("ok"):
            return {
                "ok": False,
                "error": rebuilt.get("error") or "presentation_rebuild_failed",
                "detail": rebuilt.get("detail") or "Presentation rebuild failed",
                "quality_input_text": tr_pages.get("quality_input_text") or work_text,
                "quality_output_text": tr_pages.get("quality_output_text") or "",
                "document_type": dtype,
                "source_page_count": extracted.get("page_count"),
                "source_image_count": extracted.get("image_count"),
                "delivery_mode": "presentation_rebuild",
            }

        return {
            "ok": True,
            "action_id": "translate",
            "ext": "pdf",
            "mime": MIME["pdf"],
            "filename": artifact_filename(f"{filename.rsplit('.', 1)[0]}_{tgt}", "pdf"),
            "bytes": rebuilt["bytes"],
            "quality_input_text": tr_pages.get("quality_input_text") or work_text,
            "quality_output_text": tr_pages.get("quality_output_text") or "",
            "translation_provider": tr_pages.get("provider"),
            "entities": [],
            "target_language": tgt,
            "chars_in": tr_pages.get("chars_in"),
            "chars_out": tr_pages.get("chars_out"),
            "chunks": tr_pages.get("chunks"),
            "delivery_mode": "presentation_rebuild",
            "document_type": dtype,
            "source_page_count": extracted.get("page_count"),
            "source_image_count": extracted.get("image_count"),
            "artifact_page_count": rebuilt.get("page_count"),
            "artifact_image_count": rebuilt.get("image_count"),
            "ocr_financial_qa": None,
        }

    tr = translate_text(
        work_text,
        source_language=src,
        target_language=tgt,
        preserve_names=preserve_names,
        preserve_numbers_dates=preserve_numbers_dates,
    )
    if not tr.get("ok"):
        return {
            "ok": False,
            "error": tr.get("error") or "translate_failed",
            "detail": tr.get("detail")
            or tr.get("error")
            or "Übersetzung fehlgeschlagen",
            "quality_input_text": work_text,
            "quality_output_text": "",
        }
    translated = str(tr["text"])
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", translated) if p.strip()]
    # Plain text rebuild — never claim presentation layout
    delivery_mode = "text_rebuild_pdf" if out_fmt == "pdf" else f"text_rebuild_{out_fmt}"
    meta = [
        f"Source file: {filename}",
        f"Source language: {src}",
        f"Target language: {tgt}",
        f"Provider: {tr.get('provider')}",
        f"Delivery: text rebuild (not layout-preserving)",
    ]
    if tr.get("chunks"):
        meta.append(f"Chunks: {tr.get('chunks')}")
    if out_fmt == "pdf":
        blob = write_pdf_bytes(title=title, paragraphs=paragraphs, meta_lines=meta)
    elif out_fmt == "docx":
        blob = write_docx_bytes(title=title, paragraphs=paragraphs, headings=meta)
    else:
        blob = translated.encode("utf-8")

    return {
        "ok": True,
        "action_id": "translate",
        "ext": out_fmt,
        "mime": MIME[out_fmt],
        "filename": artifact_filename(f"{filename.rsplit('.', 1)[0]}_{tgt}", out_fmt),
        "bytes": blob,
        "quality_input_text": work_text,
        "quality_output_text": translated,
        "translation_provider": tr.get("provider"),
        "entities": tr.get("entities") or [],
        "target_language": tgt,
        "chars_in": tr.get("chars_in"),
        "chars_out": tr.get("chars_out"),
        "chunks": tr.get("chunks"),
        "delivery_mode": delivery_mode,
        "document_type": dtype,
        "source_page_count": src_pages,
        "source_image_count": src_imgs,
        "ocr_financial_qa": financial_qa if financial_hard_gate else None,
    }


def _should_use_presentation_rebuild(
    *,
    dtype: str,
    file_kind: str,
    out_fmt: str,
    source_bytes: bytes | None,
    page_count: int,
    image_count: int,
) -> bool:
    if out_fmt != "pdf" or not source_bytes:
        return False
    if dtype == "businessplan":
        return True
    if page_count >= 8 and image_count >= 1:
        return True
    return False


def _exec_docx(
    *,
    text: str,
    filename: str,
    understanding: dict[str, Any],
) -> dict[str, Any]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if len(paragraphs) <= 1:
        paragraphs = [ln.strip() for ln in text.splitlines() if ln.strip()] or [text]
    title = understanding.get("document_type_label_de") or "Dokument"
    headings = [
        f"Typ: {understanding.get('document_type_label_de') or '—'}",
        f"Sprache: {understanding.get('language_label_de') or '—'}",
        f"Quelle: {filename}",
    ]
    blob = write_docx_bytes(title=str(title), paragraphs=paragraphs, headings=headings)
    # Mirror text for QA (include headings + body)
    out_text = "\n\n".join([str(title), *headings, *paragraphs])
    return {
        "ok": True,
        "action_id": "convert_docx",
        "ext": "docx",
        "mime": MIME["docx"],
        "filename": artifact_filename(filename, "docx"),
        "bytes": blob,
        "quality_input_text": text,
        "quality_output_text": out_text,
        "translation_provider": None,
        "entities": [],
        "target_language": None,
    }


def _exec_xlsx(
    *,
    text: str,
    filename: str,
    file_kind: str,
    understanding: dict[str, Any],
) -> dict[str, Any]:
    rows = _table_from_text(text)
    if not rows:
        # Fallback: one column of non-empty lines
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        rows = [["line", "value"]] + [[i + 1, ln] for i, ln in enumerate(lines[:200])]
    headers = [str(c) for c in rows[0]]
    body = [[c for c in r] for r in rows[1:]]
    blob = write_xlsx_bytes(sheet_name="Data", headers=headers, rows=body)
    # Mirror for QA entity checks
    mirror = "\n".join(["|".join(str(c) for c in headers)] + ["|".join(str(c) for c in r) for r in body])
    return {
        "ok": True,
        "action_id": "extract_data",
        "ext": "xlsx",
        "mime": MIME["xlsx"],
        "filename": artifact_filename(filename, "xlsx"),
        "bytes": blob,
        "quality_input_text": text,
        "quality_output_text": mirror,
        "translation_provider": None,
        "entities": [],
        "target_language": None,
        "row_count": len(body),
    }


def _table_from_text(text: str) -> list[list[str]]:
    lines = [ln.rstrip() for ln in (text or "").splitlines() if ln.strip()]
    if not lines:
        return []
    # CSV-ish
    if any("," in ln for ln in lines[:5]):
        import csv
        import io

        try:
            return [row for row in csv.reader(io.StringIO("\n".join(lines))) if row]
        except Exception:
            pass
    # TSV / multi-space
    rows: list[list[str]] = []
    for ln in lines:
        if "\t" in ln:
            rows.append([c.strip() for c in ln.split("\t")])
        elif "|" in ln:
            rows.append([c.strip() for c in ln.split("|") if c.strip()])
        elif re.search(r"\s{2,}", ln):
            rows.append([c.strip() for c in re.split(r"\s{2,}", ln) if c.strip()])
    if rows and max(len(r) for r in rows) >= 2:
        width = max(len(r) for r in rows)
        norm = [r + [""] * (width - len(r)) for r in rows]
        if not any(re.search(r"[A-Za-zÄÖÜäöüß]", c) for c in norm[0]):
            headers = [f"col_{i+1}" for i in range(width)]
            return [headers] + norm
        return norm
    return []
