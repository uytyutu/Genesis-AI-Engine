"""Multilingual source-language detection for Office (content-based, no filename hardcode)."""

from __future__ import annotations

import re
from typing import Any

# Marker bags — add languages without rewriting Job Engine.
_MARKERS: dict[str, tuple[str, ...]] = {
    "de": (
        "und",
        "der",
        "die",
        "das",
        "nicht",
        "mit",
        "für",
        "sie",
        "wird",
        "auch",
        "oder",
        "bei",
        "nach",
        "über",
        "vom",
        "zum",
        "einer",
        "einem",
        "werden",
        "können",
        "vertrag",
        "rechnung",
        "betrag",
        "datum",
        "seite",
        "arbeitgeber",
        "arbeitnehmer",
        "lebenslauf",
        "bewerbung",
        "bescheid",
        "straße",
        "strasse",
        "gmbh",
        "unternehmen",
        "geschäft",
        "geschaeft",
        "finanzierung",
        "umsatz",
        "markt",
        "kunden",
        "leistung",
        "deutschland",
        "dresden",
        "geschäftsidee",
        "geschaeftsidee",
        "zielgruppe",
        "wettbewerb",
    ),
    "en": (
        "the",
        "and",
        "with",
        "for",
        "this",
        "that",
        "from",
        "have",
        "will",
        "invoice",
        "contract",
        "employment",
        "amount",
        "please",
        "company",
        "resume",
        "curriculum",
        "business",
        "market",
        "customer",
        "summary",
        "roadmap",
    ),
    "uk": (
        "та",
        "про",
        "або",
        "договір",
        "рахунок",
        "резюме",
        "заява",
        "украї",
        "будь",
        "ласка",
        "компанія",
        "послуги",
    ),
    "ru": (
        "для",
        "это",
        "или",
        "договор",
        "счёт",
        "счет",
        "резюме",
        "заявление",
        "пожалуйста",
        "компания",
        "услуги",
        "который",
        "также",
    ),
    "pl": ("nie", "się", "oraz", "umowa", "faktura", "życiorys", "proszę", "firma"),
    "tr": ("bir", "için", "fatura", "sözleşme", "lütfen", "şirket", "ve"),
    "fr": ("pour", "avec", "facture", "contrat", "veuillez", "société", "dans", "une"),
    "es": ("para", "con", "factura", "contrato", "favor", "empresa", "una", "los"),
    "it": ("per", "con", "fattura", "contratto", "prego", "azienda", "una", "del"),
}

# Single-letter / ultra-common tokens that caused false RU hits ("и") — weight carefully
_WEAK_MARKERS = frozenset({"и", "i", "e", "y", "a", "o", "ve", "et", "und"})


def _letter_stats(text: str) -> dict[str, int]:
    cyr = 0
    latin = 0
    other = 0
    for ch in text:
        if not ch.isalpha():
            continue
        o = ord(ch)
        if 0x0400 <= o <= 0x04FF:
            cyr += 1
        elif ("a" <= ch.lower() <= "z") or ch in "äöüÄÖÜßàâçéèêëîïôùûüÿąćęłńóśźż":
            latin += 1
        else:
            other += 1
    return {"cyrillic": cyr, "latin": latin, "other": other, "alpha": cyr + latin + other}


def detect_source_language(text: str, *, filename: str = "") -> dict[str, Any]:
    blob = (text or "").strip()
    name = (filename or "").lower()
    stats = _letter_stats(blob)
    alpha = max(1, stats["alpha"])
    cyr_ratio = stats["cyrillic"] / alpha
    latin_ratio = stats["latin"] / alpha

    # Script gates — require meaningful share of letters, not a few stray glyphs
    # (Businessplan with ~29 Cyrillic chars among 10k+ Latin must NOT become Russian.)
    if re.search(r"[іїєґІЇЄҐ]", blob) and cyr_ratio >= 0.08:
        return {
            "code": "uk",
            "confidence": round(min(0.95, 0.7 + cyr_ratio), 3),
            "method": "script_uk",
            "letter_stats": stats,
        }
    if re.search(r"[\u0600-\u06FF]", blob) and (stats["other"] / alpha) >= 0.08:
        return {"code": "ar", "confidence": 0.9, "method": "script_ar", "letter_stats": stats}
    if re.search(r"[\u4e00-\u9fff]", blob) and (stats["other"] / alpha) >= 0.08:
        return {"code": "zh", "confidence": 0.88, "method": "script_zh", "letter_stats": stats}

    if cyr_ratio >= 0.18 and stats["cyrillic"] >= 40:
        # Substantial Cyrillic → RU (UK already handled above)
        return {
            "code": "ru",
            "confidence": round(min(0.94, 0.65 + cyr_ratio * 0.3), 3),
            "method": "script_cyrillic",
            "letter_stats": stats,
        }

    if not blob or stats["alpha"] < 12:
        if any(
            x in name
            for x in (
                "lebenslauf",
                "bewerbung",
                "rechnung",
                "bescheid",
                "vertrag",
                "businessplan",
                "geschäft",
                "geschaeft",
            )
        ):
            return {
                "code": "de",
                "confidence": 0.4,
                "method": "filename_hint_low_text",
                "letter_stats": stats,
            }
        return {
            "code": "unknown",
            "confidence": 0.15,
            "method": "empty",
            "letter_stats": stats,
        }

    lower = blob.lower()
    tokens = re.findall(
        r"[a-zäöüßàâçéèêëîïôùûüÿąćęłńóśźżіїєґа-яё]{2,}",
        lower,
        flags=re.I,
    )
    if not tokens:
        return {
            "code": "unknown",
            "confidence": 0.2,
            "method": "no_tokens",
            "letter_stats": stats,
        }

    scores: dict[str, float] = {k: 0.0 for k in _MARKERS}
    # Prefer larger sample on long docs (Businessplan ~35 pages)
    sample = tokens[:2500]
    for tok in sample:
        for lang, markers in _MARKERS.items():
            if tok in markers:
                scores[lang] += 0.35 if tok in _WEAK_MARKERS else 1.0

    if re.search(r"[äöüß]", lower):
        scores["de"] += 8.0
    if latin_ratio >= 0.7:
        # Slight preference among Latin languages when text is Latin-majority
        for lang in ("de", "en", "fr", "es", "it", "pl", "tr"):
            scores[lang] *= 1.05

    best = max(scores, key=scores.get)
    raw = scores[best]
    second = sorted(scores.values(), reverse=True)[1] if len(scores) > 1 else 0.0
    if raw <= 0:
        # Latin-majority fallback without markers
        if latin_ratio >= 0.6:
            return {
                "code": "de" if re.search(r"[äöüß]|gmbh|strasse|straße", lower) else "en",
                "confidence": 0.42,
                "method": "latin_majority_fallback",
                "letter_stats": stats,
                "scores": {k: round(v, 2) for k, v in scores.items() if v > 0},
            }
        return {
            "code": "unknown",
            "confidence": 0.25,
            "method": "no_markers",
            "letter_stats": stats,
        }

    margin = raw - second
    conf = min(0.96, 0.4 + raw / 40.0 + min(0.2, margin / 20.0))
    if best == "de" and re.search(r"[äöüß]", lower):
        conf = min(0.97, conf + 0.08)
    return {
        "code": best,
        "confidence": round(conf, 3),
        "method": "markers",
        "letter_stats": stats,
        "scores": {k: round(v, 2) for k, v in scores.items() if v > 0},
    }
