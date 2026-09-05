"""Stage 2 brain: parse → language → type → structure → intent suggestions → confidence."""

from __future__ import annotations

from typing import Any

from app.integration.virtus_office.document_classify import classify_document_type
from app.integration.virtus_office.document_explain import build_document_explanation
from app.integration.virtus_office.document_parse import parse_office_file
from app.integration.virtus_office.language_catalog import language_label_de
from app.integration.virtus_office.language_detect import detect_source_language
from app.integration.virtus_office.office_job_ssot import OFFICE_PRICE_MATRIX_EUR

CHOICE_THRESHOLD = 0.62

# Customer-sellable only — summarize/explain stay in catalog as roadmap, not choice cards.
CUSTOMER_EXECUTABLE_ACTIONS = frozenset(
    {
        "translate",
        "convert_docx",
        "extract_data",
        "document_quality_check",
        "lebenslauf_create",
        "lebenslauf_improve",
        "bewerbungsschreiben",
        "bewerbung_paket",
    }
)

ROADMAP_ACTIONS = frozenset({"summarize", "explain"})

ACTION_CATALOG: tuple[dict[str, Any], ...] = (
    {
        "id": "document_quality_check",
        "label_de": "Dokument-Qualitätscheck",
        "icon": "quality",
        "needs_target_language": False,
        "default_output": "pdf",
        "price_key": "doc_quality",
        "customer_sellable": True,
    },
    {
        "id": "translate",
        "label_de": "Übersetzen",
        "icon": "translate",
        "needs_target_language": True,
        "default_output": "pdf",
        "price_key": "translate",
        "customer_sellable": True,
    },
    {
        "id": "summarize",
        "label_de": "Zusammenfassen",
        "icon": "summarize",
        "needs_target_language": False,
        "default_output": "pdf",
        "price_key": "doc_analysis",
        "customer_sellable": False,
    },
    {
        "id": "extract_data",
        "label_de": "Daten extrahieren",
        "icon": "extract",
        "needs_target_language": False,
        "default_output": "xlsx",
        "price_key": "excel_calc",
        "customer_sellable": True,
    },
    {
        "id": "convert_docx",
        "label_de": "In Word umwandeln",
        "icon": "docx",
        "needs_target_language": False,
        "default_output": "docx",
        "price_key": "document",
        "customer_sellable": True,
    },
    {
        "id": "explain",
        "label_de": "Dokument erklären",
        "icon": "explain",
        "needs_target_language": False,
        "default_output": "pdf",
        "price_key": "doc_analysis",
        "customer_sellable": False,
    },
    {
        "id": "lebenslauf_create",
        "label_de": "Lebenslauf erstellen",
        "icon": "cv",
        "needs_target_language": False,
        "default_output": "pdf",
        "price_key": "cv_bewerbung",
        "needs_profile": True,
        "customer_sellable": True,
    },
    {
        "id": "lebenslauf_improve",
        "label_de": "Lebenslauf verbessern",
        "icon": "cv_improve",
        "needs_target_language": False,
        "default_output": "pdf",
        "price_key": "cv_bewerbung",
        "needs_profile": True,
        "customer_sellable": True,
    },
    {
        "id": "bewerbungsschreiben",
        "label_de": "Bewerbungsschreiben",
        "icon": "cover",
        "needs_target_language": False,
        "default_output": "pdf",
        "price_key": "cv_bewerbung",
        "needs_profile": True,
        "customer_sellable": True,
    },
    {
        "id": "bewerbung_paket",
        "label_de": "Bewerbung-Paket",
        "icon": "paket",
        "needs_target_language": False,
        "default_output": "zip",
        "price_key": "large_pack",
        "needs_profile": True,
        "customer_sellable": True,
    },
)


def _price_for(action_id: str) -> float:
    for row in ACTION_CATALOG:
        if row["id"] == action_id:
            return float(OFFICE_PRICE_MATRIX_EUR.get(row["price_key"], 9.90))
    return float(OFFICE_PRICE_MATRIX_EUR.get("document", 9.90))


def _suggest_actions(
    *,
    doc_type: dict[str, Any],
    file_kind: str,
    text_detected: bool,
    tables: int,
    explanation: dict[str, Any] | None = None,
) -> list[str]:
    type_id = str(doc_type.get("id") or "")
    ui = list((explanation or {}).get("suggested_ui_actions") or [])
    # Sellable only — never offer summarize/explain as paid choice cards
    actions = ui or ["document_quality_check", "translate", "extract_data", "convert_docx"]
    if file_kind in {"xlsx", "csv"} or type_id == "spreadsheet" or tables > 0:
        actions = ["document_quality_check", "extract_data", "translate", "convert_docx"]
    if type_id == "invoice":
        actions = ["document_quality_check", "extract_data", "translate", "convert_docx"]
    if type_id == "businessplan":
        actions = ["document_quality_check", "translate", "extract_data", "convert_docx"]
    if type_id == "bank_statement":
        actions = ["document_quality_check", "extract_data", "translate", "convert_docx"]
    if type_id == "official_notice":
        actions = ["document_quality_check", "translate", "convert_docx", "extract_data"]
    if type_id in {"cv_lebenslauf", "cover_letter"}:
        actions = [
            "document_quality_check",
            "lebenslauf_improve",
            "lebenslauf_create",
            "bewerbungsschreiben",
            "bewerbung_paket",
            "translate",
            "convert_docx",
        ]
    if file_kind == "image" and not text_detected:
        actions = ["document_quality_check", "translate", "convert_docx", "extract_data"]
    # Always offer quality check when missing
    if "document_quality_check" not in actions:
        actions = ["document_quality_check", *actions]
    # Preserve order, unique, sellable only
    out: list[str] = []
    for a in actions:
        if a in CUSTOMER_EXECUTABLE_ACTIONS and a not in out:
            out.append(a)
    return out


def build_understanding(
    *,
    data: bytes,
    filename: str,
    file_kind: str,
    content_type: str = "",
    service_preset: str | None = None,
    extra_pages: list[tuple[bytes, str]] | None = None,
) -> dict[str, Any]:
    parsed = parse_office_file(
        data=data,
        filename=filename,
        file_kind=file_kind,
        content_type=content_type,
        extra_pages=extra_pages,
    )
    text = str(parsed.get("text") or "")
    lang = detect_source_language(text, filename=filename)
    ocr_lang = ((parsed.get("ocr") or {}).get("language") or "")
    if isinstance(ocr_lang, str) and ocr_lang.strip() and float(lang.get("confidence") or 0) < 0.55:
        code = ocr_lang.strip().lower().split("-")[0]
        lang = {
            "code": code,
            "confidence": max(float(lang.get("confidence") or 0), 0.6),
            "method": "ocr_hint",
        }
    doc_type = classify_document_type(text=text, filename=filename, file_kind=file_kind)

    ocr_meta = parsed.get("ocr") or {}
    layout = parsed.get("layout") or {}
    financial_qa = parsed.get("financial_qa") or ocr_meta.get("financial_qa")
    structure = {
        "pages": parsed.get("page_count"),
        "pages_included": parsed.get("pages_included"),
        "tables": int(parsed.get("tables") or 0),
        "images": int(parsed.get("images") or 0),
        "text_blocks": int(parsed.get("text_blocks") or 0),
        "sheet_count": parsed.get("sheet_count"),
        "text_detected": bool(parsed.get("text_detected")),
        "ocr_status": parsed.get("ocr_status") or "not_needed",
        "ocr_provider": ocr_meta.get("provider"),
        "ocr_confidence": ocr_meta.get("confidence"),
        "layout_lines": len(layout.get("lines") or []),
        "layout_blocks": len(layout.get("blocks") or []),
        "layout_tables": len(layout.get("tables") or []),
        "parse_strategy": parsed.get("parse_strategy"),
        "parse_ok": bool(parsed.get("parse_ok")),
        "financial_qa": financial_qa,
        "ocr_needs_review": bool(
            (financial_qa or {}).get("needs_review") or ocr_meta.get("needs_review")
        ),
        "ocr_review_warning_de": (financial_qa or {}).get("warning_de")
        or ocr_meta.get("review_warning_de"),
    }

    explanation = build_document_explanation(
        text=text,
        doc_type=doc_type,
        lang=lang,
        structure=structure,
        filename=filename,
    )

    suggested = _suggest_actions(
        doc_type=doc_type,
        file_kind=file_kind,
        text_detected=structure["text_detected"],
        tables=structure["tables"],
        explanation=explanation,
    )

    # Confidence = blend of lang + type + parse quality
    conf = (
        0.35 * float(lang.get("confidence") or 0)
        + 0.4 * float(doc_type.get("confidence") or 0)
        + (0.2 if structure["text_detected"] else 0.05)
        + (0.05 if structure["parse_ok"] else 0.0)
    )
    if structure["ocr_status"] == "failed":
        conf = min(conf, 0.35)
    elif structure["ocr_status"] == "done":
        conf = min(0.98, conf + 0.08 * float(structure.get("ocr_confidence") or 0.5))
        if structure.get("ocr_needs_review"):
            conf = min(conf, 0.55)
    elif structure["ocr_status"] == "pending":
        conf = min(conf, 0.48)

    preset = (service_preset or "").strip().lower() or None
    intent: dict[str, Any] | None = None
    needs_choice = True
    if preset == "translate":
        intent = {
            "id": "translate",
            "source_language": "auto",
            "detected_source_language": lang.get("code"),
            "target_language": None,
            "output_format": "pdf",
            "locked": True,
            "label_de": "Übersetzen",
        }
        needs_choice = False
        conf = max(conf, 0.7)
    elif preset in {
        "lebenslauf_create",
        "lebenslauf_improve",
        "bewerbungsschreiben",
        "bewerbung_paket",
    }:
        meta = next((a for a in ACTION_CATALOG if a["id"] == preset), None)
        intent = {
            "id": preset,
            "source_language": "de",
            "detected_source_language": lang.get("code") or "de",
            "target_language": "de",
            "output_format": (meta or {}).get("default_output") or "pdf",
            "locked": True,
            "label_de": (meta or {}).get("label_de") or preset,
        }
        needs_choice = False
        conf = max(conf, 0.72)
    elif conf >= CHOICE_THRESHOLD and suggested:
        # High confidence still asks for action unless preset — Smart Office
        needs_choice = True

    choice_options = [
        {
            "id": a["id"],
            "label_de": a["label_de"],
            "needs_target_language": a["needs_target_language"],
            "default_output": a["default_output"],
            "price_eur": _price_for(a["id"]),
        }
        for a in ACTION_CATALOG
        if a["id"] in suggested and a.get("customer_sellable", True)
    ]

    return {
        "filled": True,
        "stage": "understood",
        "document_type": doc_type.get("id"),
        "document_type_label_de": doc_type.get("label_de"),
        "document_type_confidence": doc_type.get("confidence"),
        "language": lang.get("code"),
        "language_label_de": language_label_de(str(lang.get("code"))),
        "language_confidence": lang.get("confidence"),
        "language_method": lang.get("method"),
        "page_count": structure["pages"],
        "confidence": round(min(0.98, conf), 3),
        "needs_user_choice": needs_choice,
        "choice_options": choice_options,
        "suggested_intent": intent["id"] if intent else (suggested[0] if suggested else None),
        "suggested_output_format": (intent or {}).get("output_format")
        or (choice_options[0]["default_output"] if choice_options else "pdf"),
        "suggested_price_eur": _price_for((intent or {}).get("id") or (suggested[0] if suggested else "document")),
        "intent": intent,
        "structure": structure,
        "summary_de": (
            f"{doc_type.get('label_de') or 'Dokument'} · "
            f"{language_label_de(str(lang.get('code')))} · "
            f"{structure['pages'] or '?'} Seite(n)"
        ),
        "explanation": explanation,
        # Keep excerpt short for future Stage 3 — not shown as chat
        "text_excerpt_chars": len(text),
        "parse_notes": list(parsed.get("notes") or []),
        "layout_summary": {
            "lines": structure.get("layout_lines"),
            "blocks": structure.get("layout_blocks"),
            "tables": structure.get("layout_tables"),
            "ocr_provider": structure.get("ocr_provider"),
            "ocr_status": structure.get("ocr_status"),
        },
    }


def build_proposal_from_understanding(
    understanding: dict[str, Any],
    *,
    filename: str,
    intent_override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    intent = intent_override or understanding.get("intent")
    configure_translate = bool(
        intent
        and intent.get("id") == "translate"
        and not intent.get("target_language")
    )
    action_id = (intent or {}).get("id") or understanding.get("suggested_intent")
    price = _price_for(str(action_id or "document"))
    if intent and intent.get("id"):
        price = _price_for(str(intent["id"]))

    includes = [
        "Dokument verstanden (Typ, Sprache, Struktur)",
        "Vorschlag ohne Chat",
        "Vorschau vor Zahlung — vollständiges Ergebnis erst nach Zahlung",
    ]
    ocr_st = (understanding.get("structure") or {}).get("ocr_status")
    if ocr_st == "done":
        if (understanding.get("structure") or {}).get("ocr_needs_review"):
            includes.append(
                (understanding.get("structure") or {}).get("ocr_review_warning_de")
                or "OCR-Finanzfelder unsicher — bitte vor Zahlung prüfen"
            )
        else:
            includes.append(
                "OCR aus Scan/Foto — bei unklarer Vorlage Ergebnis bitte prüfen"
            )
    elif ocr_st == "failed":
        includes.append(
            "OCR fehlgeschlagen — klareres Foto oder Text-PDF empfohlen"
        )
    elif ocr_st == "pending":
        includes.append("OCR ausstehend — Ergebnis hängt von Bildqualität ab")

    has_complete_intent = False
    if intent and intent.get("id"):
        if intent.get("id") == "translate":
            has_complete_intent = bool(intent.get("target_language"))
        elif intent.get("id") in {
            "lebenslauf_create",
            "lebenslauf_improve",
            "bewerbungsschreiben",
            "bewerbung_paket",
        }:
            has_complete_intent = False  # set by profile submit
        else:
            has_complete_intent = True

    next_step = "select_action"
    if configure_translate:
        next_step = "configure_translate"
    elif intent and intent.get("id") in {
        "lebenslauf_create",
        "lebenslauf_improve",
        "bewerbungsschreiben",
        "bewerbung_paket",
    }:
        next_step = "complete_profile"
    elif has_complete_intent:
        next_step = "awaiting_stage3"

    low_confidence = float(understanding.get("confidence") or 0) < CHOICE_THRESHOLD
    show_choices = next_step == "select_action"

    explanation = understanding.get("explanation") if isinstance(
        understanding.get("explanation"), dict
    ) else {}

    return {
        "filled": True,
        "title_de": "Wir haben Ihr Dokument verstanden",
        "filename": filename,
        "detected": {
            "document_type": understanding.get("document_type"),
            "document_type_label_de": understanding.get("document_type_label_de"),
            "language": understanding.get("language"),
            "language_label_de": understanding.get("language_label_de"),
            "pages": understanding.get("page_count"),
            "tables": (understanding.get("structure") or {}).get("tables"),
            "images": (understanding.get("structure") or {}).get("images"),
            "text_detected": (understanding.get("structure") or {}).get("text_detected"),
            "ocr_status": (understanding.get("structure") or {}).get("ocr_status"),
        },
        "explanation": explanation,
        "task": (intent or {}).get("id"),
        "task_label_de": (intent or {}).get("label_de"),
        "result_format": (intent or {}).get("output_format")
        or understanding.get("suggested_output_format"),
        "source_language": "auto",
        "target_language": (intent or {}).get("target_language"),
        "price_eur": price,
        "includes": includes,
        "low_confidence": low_confidence,
        "show_choice_cards": show_choices,
        "choice_options": understanding.get("choice_options") or [],
        "confidence": understanding.get("confidence"),
        "next_step": next_step,
        "payment_enabled": False,
        "stage3_ready": next_step == "awaiting_stage3",
        "continue_label_de": "Weiter",
        "continue_hint_de": (
            "Bitte fehlende Profildaten ergänzen — nichts wird erfunden."
            if next_step == "complete_profile"
            else (
                "Vorschau / Auftrag prüfen — Ausführung und Download erst nach Zahlung."
                if next_step == "awaiting_stage3"
                else "Bitte Aufgabe wählen oder Einstellungen speichern."
            )
        ),
        "missing_fields": [],
        "profile_ready": False,
    }
