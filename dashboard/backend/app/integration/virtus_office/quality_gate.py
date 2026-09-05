"""Virtus Office Quality Gate — content checks before completed."""

from __future__ import annotations

import io
import re
import zipfile
from typing import Any

from app.integration.virtus_office.translator import extract_entities

_CURRENCY_RE = re.compile(r"(€|eur|usd|\$|\d+[.,]\d{2})", re.I)
_DATE_RE = re.compile(r"\d{1,2}\.\d{1,2}\.\d{2,4}")

# Strong German Businessplan markers that must not remain after DE→EN
_GERMAN_RESIDUAL = (
    "geschäftsidee",
    "gründungsvorhaben",
    "gruendungsvorhaben",
    "inhaltsverzeichnis",
    "zusammenfassung",
    "finanzplanung",
    "risikomanagement",
    "zielgruppe",
    "rechtsform",
    "einzelunternehmen",
    "ausführungen zum",
    "ausfuehrungen zum",
    "leistungsangebot",
    "marktabgrenzung",
    "erfolgsfaktoren",
    "vertraulich",
    "keine rechts- oder steuerberatung",
    "umsatzwachstum",
    "betriebsergebnis",
    "betriebsausgaben",
    "kostenstruktur",
    "ertragsquelle",
    "buchfuehrung",
    "buchführung",
    "fazit",
    "anhang",
    "geschaeftsidee",
)


def _residual_german_hits(text: str) -> list[str]:
    low = (text or "").lower()
    return [m for m in _GERMAN_RESIDUAL if m in low]


def run_quality_gate(
    *,
    action_id: str,
    input_text: str,
    output_text: str,
    artifact_bytes: bytes,
    artifact_ext: str,
    artifact_mime: str,
    target_language: str | None,
    translation_provider: str | None = None,
    expected_entities: list[str] | None = None,
    job_id: str,
    artifact_job_id: str,
    profile_facts: dict[str, Any] | None = None,
    photo_placed: bool = False,
    document_type: str | None = None,
    source_page_count: int | None = None,
    source_image_count: int | None = None,
    delivery_mode: str | None = None,
    ocr_financial_qa: dict[str, Any] | None = None,
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    def add(cid: str, ok: bool, detail: str = "") -> None:
        checks.append({"id": cid, "ok": ok, "detail": detail})

    # Document Quality Check — validate report integrity (READY/NOT_READY both deliverable)
    if action_id == "document_quality_check":
        from app.integration.virtus_office.document_quality_check import (
            validate_quality_report_artifact,
        )

        report = None
        # Prefer structured report if executor attached it via quality_output preamble
        try:
            import json as _json

            if (artifact_ext or "").lower().lstrip(".") == "json" and artifact_bytes:
                report = _json.loads(artifact_bytes.decode("utf-8"))
        except Exception:
            report = None
        checks.extend(
            validate_quality_report_artifact(
                report=report if isinstance(report, dict) else None,
                artifact_bytes=artifact_bytes or b"",
                artifact_ext=artifact_ext or "",
                quality_output_text=output_text or "",
            )
        )
        add("artifact_job_match", artifact_job_id == job_id, "job binding")
        failed = [c for c in checks if not c.get("ok")]
        return {
            "passed": len(failed) == 0,
            "failed": failed,
            "checks": checks,
        }

    # TEXT
    add("input_non_empty", bool((input_text or "").strip()), f"chars={len(input_text or '')}")
    add("output_non_empty", bool((output_text or "").strip()), f"chars={len(output_text or '')}")
    if (input_text or "").strip() and (output_text or "").strip():
        ratio = len(output_text) / max(1, len(input_text))
        add("no_obvious_truncation", ratio >= 0.25, f"ratio={ratio:.2f}")
    else:
        add("no_obvious_truncation", False, "missing text")

    if action_id == "translate" and target_language:
        tgt = target_language.lower()
        long_doc = len(input_text or "") >= 2500
        # Soft-beta / commercial: offline_glossary is never a PASS translator
        # unless OFFICE_ALLOW_OFFLINE_TRANSLATE=1 (unit-test stubs only).
        import os as _os

        offline_allowed = _os.getenv("OFFICE_ALLOW_OFFLINE_TRANSLATE", "").strip().lower() in {
            "1",
            "true",
            "yes",
        }
        live_ok = translation_provider not in {None, "", "none", "offline_glossary"} or (
            translation_provider == "offline_glossary" and offline_allowed
        )
        add(
            "live_translator_required",
            live_ok if not offline_allowed else True,
            f"provider={translation_provider} offline_allowed={offline_allowed}",
        )

        if translation_provider == "offline_glossary" and not offline_allowed:
            add("expected_language", False, f"target={tgt} provider=offline_forbidden")
            add("no_????_artifacts", False, "offline_glossary forbidden")
            add("cyrillic_present", False, "offline_forbidden")
            add("no_residual_source_language", False, "offline_forbidden")
        elif translation_provider == "offline_glossary" and offline_allowed:
            sample = output_text or ""
            lang_ok = f"({tgt})" in sample.lower() or tgt in sample.lower()
            if tgt in {"uk", "ru"}:
                lang_ok = lang_ok or bool(re.search(r"[\u0400-\u04FF]", sample))
            add("expected_language", lang_ok, f"target={tgt} provider=offline_test")
            add("no_????_artifacts", True, "offline_test_skip")
            add("cyrillic_present", True, "offline_test_skip")
            add("no_residual_source_language", True, "offline_test_skip")
        else:
            sample = output_text or ""
            add(
                "expected_language",
                sample.strip() != (input_text or "").strip(),
                f"target={tgt} provider={translation_provider}",
            )
            add(
                "no_????_artifacts",
                "????" not in sample and "\ufffd" not in sample,
                "replacement/placeholder scan",
            )
            if tgt in {"uk", "ru"}:
                add(
                    "cyrillic_present",
                    bool(re.search(r"[\u0400-\u04FF]", sample)),
                    f"target={tgt}",
                )
            else:
                add("cyrillic_present", True, "n/a")
            # DE → EN: residual German section vocabulary must not remain
            if tgt == "en":
                residual = _residual_german_hits(sample)
                # Long / businessplan docs: zero section markers; short: allow tiny leftovers
                limit = 0 if long_doc or (document_type or "") == "businessplan" else 1
                add(
                    "no_residual_source_language",
                    len(residual) <= limit,
                    f"hits={residual[:8]}" if residual else "ok",
                )
            else:
                add("no_residual_source_language", True, "n/a")
    else:
        add("live_translator_required", True, "n/a")
        add("no_residual_source_language", True, "n/a")
        add("no_????_artifacts", True, "n/a")
        add("cyrillic_present", True, "n/a")

    # DATA — preserve entities (translation/convert); Bewerbung uses dedicated checks
    if action_id not in {
        "lebenslauf_create",
        "lebenslauf_improve",
        "bewerbungsschreiben",
        "bewerbung_paket",
    }:
        ents = expected_entities if expected_entities is not None else extract_entities(input_text)
        # Prefer brand permanence when present
        if "Virtus Core" in (input_text or "") and "Virtus Core" not in (output_text or ""):
            add("brand_preserved", False, "Virtus Core missing")
        else:
            add("brand_preserved", True, "ok")
        missing = [e for e in ents if e and e not in (output_text or "")]
        add(
            "entities_preserved",
            len(missing) == 0 or not ents,
            f"missing={missing[:5]}" if missing else "ok",
        )
        if _DATE_RE.search(input_text or ""):
            add(
                "dates_preserved",
                bool(_DATE_RE.search(output_text or "")) or not missing,
                "date pattern",
            )
        else:
            add("dates_preserved", True, "no dates in input")
        if _CURRENCY_RE.search(input_text or ""):
            add(
                "currency_preserved",
                bool(_CURRENCY_RE.search(output_text or "")) or "€" in (output_text or ""),
                "currency",
            )
        else:
            add("currency_preserved", True, "no currency in input")
    else:
        add("brand_preserved", True, "bewerbung")
        add("entities_preserved", True, "bewerbung uses profile fact checks")
        add("dates_preserved", True, "bewerbung uses profile fact checks")
        add("currency_preserved", True, "n/a")

    # FINANCIAL OCR / invoice honesty — never green-pass garbled money fields
    _financial_quality_checks(
        add,
        action_id=action_id,
        input_text=input_text or "",
        output_text=output_text or "",
        ocr_financial_qa=ocr_financial_qa,
        document_type=document_type,
    )

    # STRUCTURE (light)
    if action_id in {"translate", "convert_docx", "summarize", "explain"}:
        paras_in = [p for p in re.split(r"\n\s*\n", input_text or "") if p.strip()]
        paras_out = [p for p in re.split(r"\n\s*\n", output_text or "") if p.strip()]
        add(
            "paragraph_structure",
            len(paras_out) >= max(1, min(2, len(paras_in))),
            f"in={len(paras_in)} out={len(paras_out)}",
        )
    if action_id == "extract_data":
        add("table_rows_present", "\n" in (output_text or "") or "|" in (output_text or ""), "rows")

    # ARTIFACT
    add("artifact_non_empty", bool(artifact_bytes) and len(artifact_bytes) > 32, f"size={len(artifact_bytes)}")
    add("artifact_job_match", artifact_job_id == job_id, "job binding")
    ext = (artifact_ext or "").lower().lstrip(".")
    mime = (artifact_mime or "").lower()
    mime_ok = False
    artifact_pages = None
    artifact_images = 0
    if ext == "pdf":
        mime_ok = "pdf" in mime and artifact_bytes[:4] == b"%PDF"
        add("file_opens", mime_ok and b"%%EOF" in artifact_bytes[-2048:], "pdf")
        artifact_pages, artifact_images = _pdf_stats(artifact_bytes)
    elif ext == "docx":
        mime_ok = "wordprocessingml" in mime or "openxmlformats" in mime or mime.endswith("document")
        add("file_opens", _zip_ok(artifact_bytes, need="word/document.xml"), "docx zip")
    elif ext == "xlsx":
        mime_ok = "spreadsheetml" in mime or "sheet" in mime or "openxmlformats" in mime
        add("file_opens", _zip_ok(artifact_bytes, need="xl/worksheets/sheet1.xml"), "xlsx zip")
    elif ext == "csv":
        mime_ok = "csv" in mime or "text" in mime
        add("file_opens", True, "csv")
    elif ext == "zip":
        mime_ok = "zip" in mime or mime in {"application/octet-stream", "application/x-zip-compressed"}
        add("file_opens", _zip_has_entries(artifact_bytes), "bewerbung paket zip")
    else:
        add("file_opens", False, f"unknown ext={ext}")
    add("mime_correct", mime_ok, mime)
    add("extension_correct", ext in {"pdf", "docx", "xlsx", "csv", "txt", "zip"}, ext)

    # Layout fidelity — text-rebuild PDF must not pretend to be a presentation original
    _layout_fidelity_checks(
        add,
        action_id=action_id,
        document_type=document_type,
        delivery_mode=delivery_mode,
        source_page_count=source_page_count,
        source_image_count=source_image_count,
        artifact_ext=ext,
        artifact_pages=artifact_pages,
        artifact_images=artifact_images,
        output_text=output_text or "",
    )

    # Stage 5 Bewerbung checks
    if action_id in {
        "lebenslauf_create",
        "lebenslauf_improve",
        "bewerbungsschreiben",
        "bewerbung_paket",
    }:
        _bewerbung_checks(
            add,
            action_id=action_id,
            output_text=output_text or "",
            profile_facts=profile_facts,
            photo_placed=bool(photo_placed),
        )

    failed = [c for c in checks if not c["ok"]]
    return {
        "passed": len(failed) == 0,
        "checks": checks,
        "failed": [c["id"] for c in failed],
    }


def _financial_quality_checks(
    add,
    *,
    action_id: str,
    input_text: str,
    output_text: str,
    ocr_financial_qa: dict[str, Any] | None,
    document_type: str | None,
) -> None:
    from app.integration.virtus_office.financial_fields import (
        financial_output_preserves_critical,
        looks_like_financial_document,
        validate_financial_fields,
    )

    dtype = (document_type or "").lower()
    financial = (
        dtype == "invoice"
        or bool((ocr_financial_qa or {}).get("is_financial"))
        or (
            looks_like_financial_document(input_text)
            and dtype not in {"businessplan", "cv_lebenslauf", "cover_letter"}
        )
    )
    if not financial:
        add("financial_fields_ok", True, "n/a")
        add("financial_critical_preserved", True, "n/a")
        return

    # Critical money-field honesty applies to translate (esp. OCR→translate).
    # convert_docx / extract may carry invoice snippets without a full field set.
    if action_id != "translate":
        add("financial_fields_ok", True, f"n/a for {action_id}")
        add("financial_critical_preserved", True, "n/a")
        return

    qa = ocr_financial_qa if isinstance(ocr_financial_qa, dict) else None
    if not qa:
        qa = validate_financial_fields(input_text)

    add(
        "financial_fields_ok",
        bool(qa.get("passed")),
        ",".join(qa.get("issues") or [])[:160] or "ok",
    )

    preserv = financial_output_preserves_critical(input_text, output_text)
    add(
        "financial_critical_preserved",
        bool(preserv.get("passed")),
        f"missing={preserv.get('missing')}" if preserv.get("missing") else "ok",
    )


def _layout_fidelity_checks(
    add,
    *,
    action_id: str,
    document_type: str | None,
    delivery_mode: str | None,
    source_page_count: int | None,
    source_image_count: int | None,
    artifact_ext: str,
    artifact_pages: int | None,
    artifact_images: int,
    output_text: str,
) -> None:
    dtype = (document_type or "").lower()
    mode = (delivery_mode or "").lower()
    src_pages = int(source_page_count or 0)
    src_imgs = int(source_image_count or 0)
    out_pages = int(artifact_pages or 0)

    # Rich layout docs = multi-page presentations / businessplans with embedded media.
    # A single scan/photo (images=1, pages=1) is OCR input — not a layout-preserve case.
    rich = dtype == "businessplan" or src_pages >= 8 or (src_imgs >= 1 and src_pages >= 2)
    if action_id != "translate" or not rich:
        add("layout_fidelity", True, "n/a")
        add("source_images_preserved", True, "n/a")
        add("pagination_consistent", True, "n/a")
        add("toc_pagination_stale", True, "n/a")
        return

    # Text-rebuild cannot claim layout-preserving presentation quality
    if mode in {"presentation_rebuild"}:
        pages_ok = True
        if src_pages >= 8 and out_pages > 0:
            pages_ok = out_pages >= int(src_pages * 0.95)
        imgs_ok = True
        if src_imgs > 0:
            imgs_ok = artifact_images >= max(1, int(src_imgs * 0.8))
        add(
            "layout_fidelity",
            pages_ok and imgs_ok,
            f"presentation_rebuild pages={out_pages}/{src_pages} images={artifact_images}/{src_imgs}",
        )
    elif mode in {"", "text_rebuild", "text_rebuild_pdf", "plain_pdf"}:
        add(
            "layout_fidelity",
            False,
            f"delivery_mode={mode or 'text_rebuild'} cannot preserve presentation layout",
        )
    else:
        add("layout_fidelity", True, mode)

    if src_imgs > 0:
        add(
            "source_images_preserved",
            artifact_images >= max(1, int(src_imgs * 0.8)) if artifact_ext == "pdf" else False,
            f"source_images={src_imgs} artifact_images={artifact_images}",
        )
    else:
        add("source_images_preserved", True, "no source images")

    if src_pages >= 8 and artifact_ext == "pdf" and out_pages > 0:
        ratio = out_pages / max(1, src_pages)
        add(
            "pagination_consistent",
            ratio >= 0.95 if mode == "presentation_rebuild" else ratio >= 0.85,
            f"source_pages={src_pages} artifact_pages={out_pages} ratio={ratio:.2f}",
        )
    else:
        add("pagination_consistent", True, f"pages src={src_pages} out={out_pages}")

    # Stale TOC page markers from a longer original (e.g. confidential 28)
    if src_pages >= 8 and out_pages and out_pages < src_pages:
        stale = re.search(rf"confidential\s*{src_pages}\b", output_text, re.I) or re.search(
            rf"vertraulich\s*{src_pages}\b", output_text, re.I
        )
        if stale:
            add("toc_pagination_stale", False, f"still references page {src_pages}")
        else:
            add("toc_pagination_stale", True, "ok")
    else:
        add("toc_pagination_stale", True, "n/a")


def _pdf_stats(data: bytes) -> tuple[int | None, int]:
    try:
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(data))
        pages = len(reader.pages)
        imgs = 0
        for page in reader.pages:
            res = page.get("/Resources")
            if not res:
                continue
            res = res.get_object() if hasattr(res, "get_object") else res
            xo = res.get("/XObject") if res else None
            if not xo:
                continue
            xo = xo.get_object() if hasattr(xo, "get_object") else xo
            for key in xo:
                obj = xo[key].get_object()
                if obj.get("/Subtype") == "/Image":
                    imgs += 1
        return pages, imgs
    except Exception:
        return None, 0


def _bewerbung_checks(
    add,
    *,
    action_id: str,
    output_text: str,
    profile_facts: dict[str, Any] | None,
    photo_placed: bool,
) -> None:
    from app.integration.virtus_office.bewerbung_ssot import BEWERBUNG_FORBIDDEN_PHRASES

    facts = profile_facts or {}
    out_l = output_text.lower()

    # No job-guarantee marketing
    banned = [p for p in BEWERBUNG_FORBIDDEN_PHRASES if p in out_l]
    add("no_job_guarantee_claims", len(banned) == 0, f"banned={banned[:2]}")

    # Contacts
    contacts = list(facts.get("contacts") or [])
    if action_id == "bewerbungsschreiben":
        # Cover letter must name the candidate; email/phone optional in body
        name = next((c for c in contacts if c and "@" not in str(c) and not str(c).startswith("+")), None)
        name_ok = (not name) or (str(name) in output_text) or (str(name).lower() in out_l)
        add("contacts_present", name_ok, f"name={name}")
    else:
        contact_ok = True
        missing_c = []
        for c in contacts:
            if c and str(c) not in output_text:
                ascii_c = "".join(ch for ch in str(c) if ord(ch) < 128)
                if len(ascii_c) >= 3 and ascii_c.lower() not in out_l:
                    contact_ok = False
                    missing_c.append(str(c)[:40])
        add("contacts_present", contact_ok or not contacts, f"missing={missing_c[:3]}")

    if action_id in {"lebenslauf_create", "lebenslauf_improve", "bewerbung_paket"}:
        for label, key in (("employers_present", "employers"), ("schools_present", "schools")):
            items = [str(x) for x in (facts.get(key) or []) if x]
            missing_i = [x for x in items if x not in output_text and x.lower() not in out_l]
            add(label, len(missing_i) == 0 or not items, f"missing={missing_i[:3]}")

        dates = [str(x) for x in (facts.get("dates") or []) if x]
        missing_d = [d for d in dates if d not in output_text]
        add("work_dates_present", len(missing_d) == 0 or not dates, f"missing={missing_d[:3]}")

        langs = list(facts.get("languages") or [])
        lang_ok = True
        for entry in langs:
            lang = str(entry).split(":")[0].strip()
            if lang and lang.lower() not in out_l:
                lang_ok = False
        add("languages_declared_only", lang_ok or not langs, "declared languages in output")
    else:
        add("employers_present", True, "n/a anschreiben")
        add("schools_present", True, "n/a anschreiben")
        add("work_dates_present", True, "n/a anschreiben")
        add("languages_declared_only", True, "n/a anschreiben")

    # German section headers for CV actions
    if action_id in {"lebenslauf_create", "lebenslauf_improve", "bewerbung_paket"}:
        need = ["persönliche daten", "berufserfahrung"] if facts.get("employers") else ["persönliche daten"]
        if facts.get("schools"):
            need.append("ausbildung")
        headers_ok = all(n in out_l for n in need)
        add("german_cv_headers", headers_ok, f"need={need}")

    if action_id in {"bewerbungsschreiben", "bewerbung_paket"}:
        vac_company = facts.get("vacancy_company")
        vac_title = facts.get("vacancy_title")
        align = True
        if vac_company and str(vac_company).lower() not in out_l:
            align = False
        if vac_title and str(vac_title).lower() not in out_l:
            align = False
        add("vacancy_alignment", align, "company/title")

    if facts.get("has_photo") and action_id in {
        "lebenslauf_create",
        "lebenslauf_improve",
        "bewerbung_paket",
    }:
        add("photo_placement", photo_placed, "photo_material set → placed in PDF")
    else:
        add("photo_placement", True, "no photo required")

    add(
        "no_obvious_cut_markers",
        "???" not in output_text and "\x00" not in output_text,
        "truncation markers",
    )

    # CC-4 — placeholder / demo leftovers (fabrication / template residue)
    placeholder_hits = _placeholder_hits(output_text, profile_facts=facts)
    add(
        "no_placeholders",
        len(placeholder_hits) == 0,
        f"hits={placeholder_hits[:4]}" if placeholder_hits else "ok",
    )


_PLACEHOLDER_PATTERNS = (
    re.compile(r"\[NAME\]", re.I),
    re.compile(r"\[ADDRESS\]", re.I),
    re.compile(r"\[DATE\]", re.I),
    re.compile(r"lorem ipsum", re.I),
    re.compile(r"\bTODO\b"),
    re.compile(r"\bINSERT\b"),
    re.compile(r"\bPLACEHOLDER\b", re.I),
)

# Demo-street / demo-name only fail when not present in customer facts
_DEMO_NAME_RE = re.compile(r"Max Mustermann", re.I)
_DEMO_STREET_RE = re.compile(r"Musterstraße", re.I)


def _placeholder_hits(text: str, *, profile_facts: dict[str, Any] | None = None) -> list[str]:
    hits: list[str] = []
    for pat in _PLACEHOLDER_PATTERNS:
        if pat.search(text or ""):
            hits.append(pat.pattern)
    facts = profile_facts or {}
    declared = " ".join(str(c) for c in (facts.get("contacts") or [])).lower()
    # If customer really is Max Mustermann, allow it; else treat as leftover demo text
    if _DEMO_NAME_RE.search(text or "") and "max mustermann" not in declared:
        hits.append("Max Mustermann")
    if _DEMO_STREET_RE.search(text or "") and "musterstraße" not in declared and "musterstrasse" not in declared:
        hits.append("Musterstraße")
    return hits


def _zip_has_entries(data: bytes) -> bool:
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            return bool(zf.namelist()) and zf.testzip() is None
    except Exception:
        return False


def _zip_ok(data: bytes, *, need: str) -> bool:
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            names = zf.namelist()
            return need in names and zf.testzip() is None
    except Exception:
        return False
