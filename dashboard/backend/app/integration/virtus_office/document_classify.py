"""Document type classification — weighted content/structure signals (no filename hardcode)."""

from __future__ import annotations

import re
from typing import Any

# (type_id, label_de, markers with weights, exclusive boost markers)
_TYPE_RULES: tuple[tuple[str, str, tuple[tuple[str, float], ...]], ...] = (
    (
        "businessplan",
        "Businessplan / Geschäftsplan",
        (
            ("businessplan", 4.0),
            ("geschäftsplan", 4.0),
            ("geschaeftsplan", 4.0),
            ("business plan", 3.5),
            ("unternehmensbeschreibung", 2.5),
            ("geschäftsidee", 3.0),
            ("geschaeftsidee", 3.0),
            ("leistungsangebot", 2.5),
            ("zielgruppe", 2.5),
            ("marktanalyse", 3.0),
            ("marktabgrenzung", 2.5),
            ("wettbewerbsanalyse", 2.5),
            ("wettbewerb", 1.5),
            ("swot", 2.0),
            ("business model canvas", 3.0),
            ("finanzplanung", 3.0),
            ("finanzierung", 2.0),
            ("umsatzplanung", 2.5),
            ("kostenplanung", 2.5),
            ("liquiditäts", 2.0),
            ("liquiditaets", 2.0),
            ("investition", 1.5),
            ("gründungsvorhaben", 3.0),
            ("gruendungsvorhaben", 3.0),
            ("executive summary", 2.0),
            ("roadmap", 1.5),
            ("erfolgsfaktoren", 2.0),
            ("risikomanagement", 2.0),
            ("inhaltsverzeichnis", 1.0),
            ("kpi", 1.2),
        ),
    ),
    (
        "employment_contract",
        "Arbeitsvertrag",
        (
            ("arbeitsvertrag", 4.0),
            ("employment contract", 3.5),
            ("probezeit", 2.5),
            ("arbeitgeber", 1.5),
            ("arbeitnehmer", 1.5),
            ("kündigungsfrist", 2.0),
        ),
    ),
    (
        "invoice",
        "Rechnung",
        (
            ("rechnungsnr", 3.5),
            ("rechnungsnummer", 3.5),
            ("rechnung", 2.0),
            ("invoice number", 3.0),
            ("invoice", 1.5),
            ("ust-id", 2.5),
            ("gesamtbetrag", 2.0),
            ("faktura", 2.5),
            ("rechnungsdatum", 3.0),
            ("rechnungsempfänger", 3.0),
        ),
    ),
    (
        "cv_lebenslauf",
        "Lebenslauf / CV",
        (
            ("lebenslauf", 4.0),
            ("curriculum vitae", 4.0),
            ("berufserfahrung", 3.0),
            ("schulbildung", 2.5),
            ("resume", 2.0),
            ("arbeitserfahrung", 2.0),
        ),
    ),
    (
        "bank_statement",
        "Kontoauszug",
        (
            ("kontoauszug", 5.0),
            ("bank statement", 4.5),
            ("kontostand", 3.0),
            ("buchungstext", 3.0),
            ("buchungsdatum", 3.0),
            ("anfangssaldo", 3.5),
            ("endsaldo", 3.5),
            ("valuta", 1.5),
            ("iban", 1.2),
            ("bic", 1.0),
            ("buchung", 1.0),
            ("saldo", 1.2),
        ),
    ),
    (
        "official_notice",
        "Bescheid / Amtliches Schreiben",
        (
            ("bescheid", 4.0),
            ("aktenzeichen", 3.5),
            ("jobcenter", 3.0),
            ("ausländerbehörde", 3.0),
            ("auslaenderbehoerde", 3.0),
            ("widerspruch", 2.5),
            ("widerspruchsfrist", 3.0),
        ),
    ),
    (
        "cover_letter",
        "Bewerbungsschreiben",
        (
            ("bewerbungsschreiben", 4.0),
            ("anschreiben", 2.5),
            ("cover letter", 3.5),
            ("bewerbung um", 3.0),
        ),
    ),
    (
        "contract",
        "Vertrag",
        (
            ("vertragspartei", 3.0),
            ("vertragslaufzeit", 3.0),
            ("kündigungsfrist", 2.0),
            ("vertrag", 1.2),
            ("agreement", 1.2),
        ),
    ),
    (
        "letter",
        "Brief / Schreiben",
        (
            ("sehr geehrte", 2.5),
            ("mit freundlichen grüßen", 3.0),
            ("mit freundlichen gruessen", 3.0),
            ("dear sir", 2.5),
        ),
    ),
    (
        "form",
        "Formular",
        (
            ("formular", 3.0),
            ("bitte ausfüllen", 3.0),
            ("bitte ausfuellen", 3.0),
            ("application form", 3.0),
            ("unterschrift", 1.5),
            ("antrag", 1.2),
        ),
    ),
)


def classify_document_type(
    *,
    text: str,
    filename: str = "",
    file_kind: str = "",
) -> dict[str, Any]:
    # Content-first: filename is a weak bonus only (never sole reason for type).
    body = (text or "").lower()
    name = (filename or "").lower()
    blob = f"{body}\n{name}"

    if file_kind in {"xlsx", "csv"} or name.endswith((".xlsx", ".csv")):
        return {
            "id": "spreadsheet",
            "label_de": "Tabelle / Excel",
            "confidence": 0.8,
            "method": "file_kind",
        }

    if file_kind == "image" and not (text or "").strip():
        if any(x in name for x in ("cv", "lebenslauf", "foto", "portrait", "passfoto")):
            return {
                "id": "photo_portrait",
                "label_de": "Foto (ggf. für CV)",
                "confidence": 0.5,
                "method": "filename_image",
            }
        return {
            "id": "scanned_document",
            "label_de": "Scan / Foto eines Dokuments",
            "confidence": 0.4,
            "method": "image_no_text",
        }

    scores: dict[str, float] = {}
    labels: dict[str, str] = {}
    hit_detail: dict[str, list[str]] = {}

    for type_id, label, markers in _TYPE_RULES:
        score = 0.0
        hits: list[str] = []
        for marker, weight in markers:
            # Count occurrences in body (strong) + single filename bonus (weak)
            body_hits = body.count(marker)
            name_hit = 1 if marker in name else 0
            if body_hits:
                score += weight * min(body_hits, 6)
                hits.append(marker)
            elif name_hit:
                score += weight * 0.35
                hits.append(f"{marker}(filename)")
        # Bank statement needs stronger evidence than a lone IBAN/Saldo in a Businessplan
        if type_id == "bank_statement":
            strong = any(
                k in body
                for k in (
                    "kontoauszug",
                    "bank statement",
                    "buchungstext",
                    "anfangssaldo",
                    "endsaldo",
                    "kontostand",
                )
            )
            if not strong and score < 6.0:
                score *= 0.25
        # Invoice: lone "rechnung" as German word for invoice concept in prose is weak
        if type_id == "invoice" and "rechnungsnr" not in body and "rechnungsnummer" not in body:
            if body.count("rechnung") <= 1 and "invoice" not in body:
                score *= 0.4
        scores[type_id] = score
        labels[type_id] = label
        hit_detail[type_id] = hits

    if not scores or max(scores.values()) <= 0.5:
        if (text or "").strip():
            return {
                "id": "general_document",
                "label_de": "Allgemeines Dokument",
                "confidence": 0.45,
                "method": "text_present",
            }
        return {
            "id": "unknown",
            "label_de": "Unbekanntes Dokument",
            "confidence": 0.2,
            "method": "none",
        }

    ranked = sorted(scores.items(), key=lambda x: -x[1])
    best_id, best_score = ranked[0]
    second = ranked[1][1] if len(ranked) > 1 else 0.0

    if best_score < 1.5:
        return {
            "id": "general_document",
            "label_de": "Allgemeines Dokument",
            "confidence": 0.48,
            "method": "weak_markers",
            "scores": {k: round(v, 2) for k, v in ranked[:5] if v > 0},
        }

    margin = best_score - second
    conf = min(0.97, 0.45 + best_score / 25.0 + min(0.2, margin / 15.0))
    return {
        "id": best_id,
        "label_de": labels[best_id],
        "confidence": round(conf, 3),
        "method": "weighted_markers",
        "marker_hits": len(hit_detail.get(best_id) or []),
        "hit_markers": (hit_detail.get(best_id) or [])[:12],
        "scores": {k: round(v, 2) for k, v in ranked[:6] if v > 0},
        "runner_up": ranked[1][0] if len(ranked) > 1 and second > 0.5 else None,
    }


def count_tables_heuristic(text: str) -> int:
    if not text:
        return 0
    hits = 0
    for line in text.splitlines():
        if line.count("\t") >= 2 or line.count("|") >= 2 or re.search(r"\s{2,}\S+\s{2,}\S+", line):
            hits += 1
    if hits >= 3:
        return max(1, hits // 5)
    return 0
