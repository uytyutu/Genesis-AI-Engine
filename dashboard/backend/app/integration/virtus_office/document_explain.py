"""Deterministic document explanation for Virtus Office proposals.

Never invents names, dates, case numbers, or legal facts.
Only reports signals found via heuristics / regex on extracted text.
"""

from __future__ import annotations

import re
from typing import Any


def _has(text: str, *markers: str) -> bool:
    blob = text.lower()
    return any(m.lower() in blob for m in markers)


def _first_match(text: str, pattern: str, flags: int = re.I) -> str | None:
    m = re.search(pattern, text, flags)
    if not m:
        return None
    val = (m.group(1) if m.lastindex else m.group(0)).strip()
    return val[:120] if val else None


def _count_line_items(text: str) -> int | None:
    if not text:
        return None
    money_rows = 0
    numbered = 0
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        if re.search(r"\d+[.,]\d{2}\s*(€|eur|euro)?\b", s, re.I):
            money_rows += 1
        if re.match(r"^(\d{1,3}[\.\)]\s+|[Pp]os\.?\s*\d+)", s):
            numbered += 1
    n = max(money_rows, numbered)
    if n >= 2:
        return min(n, 80)
    return None


# Section probes: (section_id, markers) — only emit when markers found in text
_BUSINESSPLAN_SECTIONS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("executive_summary", ("executive summary", "zusammenfassung", "kurzüberblick", "kurzueberblick")),
    ("founding", ("gründungsvorhaben", "gruendungsvorhaben", "gründung", "gruendung")),
    ("business_idea", ("geschäftsidee", "geschaeftsidee", "leistungsangebot", "produkte", "dienstleistungen")),
    ("motivation", ("motivation", "leidenschaft")),
    ("business_model", ("business model canvas", "geschäftsmodell", "geschaeftsmodell")),
    ("swot", ("swot", "stärken", "schwaechen", "chancen", "risiken")),
    ("roadmap", ("roadmap", "zeitplan", "meilenstein")),
    ("market", ("marktabgrenzung", "marktanalyse", "markt", "zielgruppe")),
    ("competition", ("wettbewerb", "wettbewerber", "konkurrenz")),
    ("marketing", ("marketing", "vertrieb")),
    ("organization", ("organisation", "personal", "standort")),
    ("technology", ("technology stack", "technologie", "plattform")),
    ("finance", ("finanzplanung", "finanzierung", "umsatz", "kosten", "liquidität", "liquiditaet", "investition")),
    ("risks", ("risikomanagement", "risiken")),
    ("kpi", ("kpi", "kennzahlen", "ziele")),
    ("legal", ("legal", "rechtliche", "steuerberatung")),
)


def _detect_sections(text: str) -> list[dict[str, str]]:
    lower = text.lower()
    out: list[dict[str, str]] = []
    for sid, markers in _BUSINESSPLAN_SECTIONS:
        if any(m in lower for m in markers):
            out.append({"id": sid})
    return out


def _key_facts_businessplan(text: str) -> list[dict[str, Any]]:
    facts: list[dict[str, Any]] = []
    brand = _first_match(
        text,
        r"(?:Marke|Brand)\s*[:|]\s*([^\n|]{2,80})",
    )
    if brand:
        facts.append({"id": "brand", "value": brand.strip(), "confidence": "high"})
    elif _has(text, "virtus core"):
        facts.append({"id": "brand", "value": "Virtus Core", "confidence": "high"})

    customer = _first_match(
        text,
        r"(?:Kunde|Client|Auftraggeber)\s*[:|]\s*([^\n]{3,80})",
    )
    if customer:
        facts.append({"id": "customer", "value": customer.strip(), "confidence": "high"})

    founder = _first_match(
        text,
        r"Businessplan\s+([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)+)",
    )
    if founder and "virtus" not in founder.lower():
        facts.append({"id": "founder", "value": founder.strip(), "confidence": "medium"})

    location = _first_match(
        text,
        r"\b(Dresden|Berlin|Hamburg|München|Munich|Leipzig)\b",
    )
    if location:
        facts.append({"id": "location", "value": location, "confidence": "high"})

    legal_form = None
    if _has(text, "einzelunternehmen"):
        legal_form = "Einzelunternehmen"
    elif _has(text, "gmbh"):
        legal_form = "GmbH"
    elif _has(text, "ug ("):
        legal_form = "UG"
    if legal_form:
        facts.append({"id": "legal_form", "value": legal_form, "confidence": "high"})

    version = _first_match(text, r"Version\s*[:|]?\s*([^\n]{2,80})")
    if version:
        facts.append({"id": "document_version", "value": version.strip(), "confidence": "high"})
    docstand = _first_match(text, r"Dokumentstand\s*[:|]?\s*([^\n]{2,40})")
    if docstand:
        facts.append({"id": "document_date", "value": docstand.strip(), "confidence": "high"})

    if _has(text, "finanz", "umsatz", "kosten", "investition", "liquidität", "liquiditaet"):
        facts.append({"id": "finance_sections", "confidence": "high"})
    if _has(text, "€", " eur", "euro"):
        facts.append({"id": "currency_eur", "confidence": "high"})

    return facts


def build_document_explanation(
    *,
    text: str,
    doc_type: dict[str, Any],
    lang: dict[str, Any],
    structure: dict[str, Any],
    filename: str = "",
) -> dict[str, Any]:
    type_id = str(doc_type.get("id") or "unknown")
    type_conf = float(doc_type.get("confidence") or 0)
    lang_code = str(lang.get("code") or "") or None
    lang_conf = float(lang.get("confidence") or 0)
    pages = structure.get("pages")
    tables = int(structure.get("tables") or 0)
    text_detected = bool(structure.get("text_detected"))
    ocr_status = str(structure.get("ocr_status") or "")
    raw = text or ""
    text_chars = len(raw.strip())

    findings: list[dict[str, Any]] = []
    uncertain: list[dict[str, Any]] = []
    sections: list[dict[str, str]] = []
    key_facts: list[dict[str, Any]] = []
    about_signals: list[str] = []

    content_kind = "text"
    if ocr_status in {"done", "pending", "failed"} and not text_detected:
        content_kind = "scanned"
    elif tables > 0:
        content_kind = "text_and_tables"
    elif text_detected:
        content_kind = "text"

    if pages is not None:
        findings.append({"id": "pages", "count": int(pages)})
    if lang_code and lang_conf >= 0.45:
        findings.append({"id": "language", "code": lang_code})
    elif raw.strip():
        uncertain.append({"id": "language"})

    if tables > 0:
        findings.append({"id": "tables", "count": tables})
    if text_chars:
        findings.append({"id": "text_chars", "count": text_chars})

    about_id = "general"
    if type_id == "businessplan":
        about_id = "businessplan"
        sections = _detect_sections(raw)
        key_facts = _key_facts_businessplan(raw)
        for s in sections:
            about_signals.append(s["id"])
        if sections:
            findings.append({"id": "sections_found", "count": len(sections)})
        if _has(raw, "inhaltsverzeichnis", "executive summary", "geschäftsidee", "geschaeftsidee"):
            findings.append({"id": "toc_or_structure"})
        if any(s["id"] == "finance" for s in sections):
            findings.append({"id": "finance_block"})
        if any(s["id"] == "market" for s in sections):
            findings.append({"id": "market_block"})
    elif type_id == "invoice":
        about_id = "invoice"
        if _has(raw, "lieferant", "verkäufer", "absender", "from:", "vendor", "supplier"):
            findings.append({"id": "supplier_block"})
        if _has(raw, "rechnungsempfänger", "kunde", "bill to", "empfänger", "buyer", "an:"):
            findings.append({"id": "client_block"})
        inv = _first_match(
            raw,
            r"(?:rechnungsnr\.?|rechnungsnummer|invoice\s*(?:no\.?|number|#)|faktura)\s*[:#]?\s*([A-Za-z0-9\-\/]+)",
        )
        if inv:
            findings.append({"id": "invoice_number", "value": inv})
            key_facts.append({"id": "invoice_number", "value": inv, "confidence": "high"})
        elif _has(raw, "rechnungsnr", "rechnungsnummer", "invoice no", "invoice number"):
            findings.append({"id": "invoice_number"})
        date = _first_match(
            raw,
            r"(?:rechnungsdatum|datum|date|invoice date)\s*[:.]?\s*(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})",
        )
        if date:
            findings.append({"id": "date", "value": date})
            key_facts.append({"id": "date", "value": date, "confidence": "high"})
        elif _has(raw, "rechnungsdatum", "datum", "invoice date"):
            findings.append({"id": "date"})
        items = _count_line_items(raw)
        if items:
            findings.append({"id": "line_items", "count": items})
        if _has(raw, "netto", "net amount", "net sum", "zwischensumme"):
            findings.append({"id": "netto"})
        if _has(raw, "mwst", "ust", "vat", "umsatzsteuer", "mehrwertsteuer"):
            findings.append({"id": "mwst"})
            rate = _first_match(
                raw, r"(?:mwst|ust|vat|umsatzsteuer)[^\d%]{0,12}(\d{1,2}(?:[.,]\d+)?)\s*%"
            )
            if rate:
                findings.append({"id": "mwst_rate", "value": f"{rate}%"})
        if _has(raw, "brutto", "gesamtbetrag", "total", "summe"):
            findings.append({"id": "brutto"})
    elif type_id == "official_notice":
        about_id = "official"
        if _has(raw, "jobcenter", "behörde", "amt", "ausländerbehörde", "finanzamt", "institution"):
            findings.append({"id": "institution"})
        if _has(raw, "sehr geehrte", "an:", "herr ", "frau ", "adressat"):
            findings.append({"id": "addressee"})
        az = _first_match(
            raw,
            r"(?:aktenzeichen|az\.?|geschäftszeichen|reference|ref\.?)\s*[:.]?\s*([A-Za-z0-9\-\/\.]+)",
        )
        if az:
            findings.append({"id": "aktenzeichen", "value": az})
            key_facts.append({"id": "aktenzeichen", "value": az, "confidence": "high"})
        elif _has(raw, "aktenzeichen", "geschäftszeichen"):
            findings.append({"id": "aktenzeichen"})
        if re.search(r"\d{1,2}[./-]\d{1,2}[./-]\d{2,4}", raw):
            findings.append({"id": "dates"})
        if _has(raw, "frist", "bis zum", "spätestens", "deadline", "antwort"):
            findings.append({"id": "deadline"})
        if _has(raw, "aufforderung", "mitteilung", "bescheid", "widerspruch", "antrag"):
            findings.append({"id": "requirements"})
    elif type_id in {"cv_lebenslauf", "cover_letter"}:
        about_id = "cv" if type_id == "cv_lebenslauf" else "cover"
        if _has(raw, "berufserfahrung", "experience", "arbeitgeber"):
            findings.append({"id": "experience"})
        if _has(raw, "schulbildung", "ausbildung", "education", "studium"):
            findings.append({"id": "education"})
        if _has(raw, "kenntnisse", "skills", "sprachen", "languages"):
            findings.append({"id": "skills"})
        if _has(raw, "sehr geehrte", "bewerbung um", "stelle"):
            findings.append({"id": "application_intent"})
    elif type_id == "spreadsheet":
        about_id = "spreadsheet"
        sheets = structure.get("sheet_count")
        if sheets:
            findings.append({"id": "sheets", "count": int(sheets)})
        findings.append({"id": "tabular_data"})
    elif type_id in {"scanned_document", "photo_portrait"}:
        about_id = "scan"
        if ocr_status == "done" and text_detected:
            findings.append({"id": "ocr_text"})
        elif ocr_status == "failed":
            uncertain.append({"id": "ocr_quality"})
        elif not text_detected:
            uncertain.append({"id": "ocr_quality"})
    elif type_id == "employment_contract":
        about_id = "contract"
        if _has(raw, "arbeitgeber", "employer"):
            findings.append({"id": "employer_party"})
        if _has(raw, "arbeitnehmer", "employee"):
            findings.append({"id": "employee_party"})
        if _has(raw, "probezeit", "kündigung", "gehalt", "salary"):
            findings.append({"id": "contract_terms"})
    elif type_id == "bank_statement":
        about_id = "bank"
        if _has(raw, "iban"):
            findings.append({"id": "iban"})
        if _has(raw, "saldo", "balance", "kontostand"):
            findings.append({"id": "balance"})
        if _has(raw, "buchung", "buchungstext", "umsatz"):
            findings.append({"id": "transactions"})
        period = _first_match(
            raw,
            r"(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})\s*[-–bis]+\s*(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})",
        )
        if period:
            key_facts.append({"id": "period", "value": period, "confidence": "medium"})
    else:
        if text_detected and len(raw.strip()) > 40:
            findings.append({"id": "text_content"})
        elif not text_detected:
            uncertain.append({"id": "content"})

    if type_conf < 0.55 or type_id in {"unknown", "general_document"}:
        uncertain.append({"id": "document_type"})

    suggested_ui = _suggested_ui_actions(type_id, tables=tables, text_detected=text_detected)

    return {
        "kind": type_id,
        "about_id": about_id,
        "type_label_de": doc_type.get("label_de"),
        "type_confidence": round(type_conf, 3),
        "language_code": lang_code,
        "language_confidence": round(lang_conf, 3) if lang_code else None,
        "pages": pages,
        "content_kind": content_kind,
        "text_chars": text_chars,
        "findings": findings,
        "sections": sections,
        "key_facts": key_facts,
        "about_signals": about_signals,
        "uncertain": uncertain,
        "suggested_ui_actions": suggested_ui,
        "honesty": "no_invention",
        "type_scores": doc_type.get("scores"),
        "lang_method": lang.get("method"),
    }


def _suggested_ui_actions(type_id: str, *, tables: int, text_detected: bool) -> list[str]:
    if type_id == "businessplan":
        return ["translate", "extract_data", "convert_docx"]
    if type_id == "invoice":
        return ["extract_data", "translate", "convert_docx"]
    if type_id == "official_notice":
        return ["translate", "convert_docx", "extract_data"]
    if type_id == "bank_statement":
        return ["extract_data", "translate", "convert_docx"]
    if type_id in {"cv_lebenslauf", "cover_letter"}:
        return [
            "lebenslauf_improve",
            "translate",
            "convert_docx",
            "bewerbungsschreiben",
            "bewerbung_paket",
        ]
    if type_id == "spreadsheet" or tables > 0:
        return ["extract_data", "translate", "convert_docx"]
    if type_id in {"scanned_document", "photo_portrait"} and not text_detected:
        return ["convert_docx", "translate", "extract_data"]
    return ["translate", "extract_data", "convert_docx"]
