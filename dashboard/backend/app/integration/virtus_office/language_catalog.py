"""Expandable target/source language catalog for Virtus Office (no DE/RU hardcode)."""

from __future__ import annotations

from typing import Any

# Languages accepted by the translation executor (LLM path + offline labeled path).
# Only list languages we actually accept as target/source codes.
OFFICE_LANGUAGE_CATALOG: tuple[dict[str, str], ...] = (
    {"code": "de", "label_de": "Deutsch", "label_en": "German", "native": "Deutsch"},
    {"code": "en", "label_de": "Englisch", "label_en": "English", "native": "English"},
    {"code": "uk", "label_de": "Ukrainisch", "label_en": "Ukrainian", "native": "Українська"},
    {"code": "ru", "label_de": "Russisch", "label_en": "Russian", "native": "Русский"},
    {"code": "pl", "label_de": "Polnisch", "label_en": "Polish", "native": "Polski"},
    {"code": "fr", "label_de": "Französisch", "label_en": "French", "native": "Français"},
    {"code": "es", "label_de": "Spanisch", "label_en": "Spanish", "native": "Español"},
    {"code": "it", "label_de": "Italienisch", "label_en": "Italian", "native": "Italiano"},
    {"code": "pt", "label_de": "Portugiesisch", "label_en": "Portuguese", "native": "Português"},
    {"code": "nl", "label_de": "Niederländisch", "label_en": "Dutch", "native": "Nederlands"},
    {"code": "tr", "label_de": "Türkisch", "label_en": "Turkish", "native": "Türkçe"},
    {"code": "cs", "label_de": "Tschechisch", "label_en": "Czech", "native": "Čeština"},
    {"code": "sk", "label_de": "Slowakisch", "label_en": "Slovak", "native": "Slovenčina"},
    {"code": "hu", "label_de": "Ungarisch", "label_en": "Hungarian", "native": "Magyar"},
    {"code": "ro", "label_de": "Rumänisch", "label_en": "Romanian", "native": "Română"},
    {"code": "bg", "label_de": "Bulgarisch", "label_en": "Bulgarian", "native": "Български"},
    {"code": "el", "label_de": "Griechisch", "label_en": "Greek", "native": "Ελληνικά"},
    {"code": "hr", "label_de": "Kroatisch", "label_en": "Croatian", "native": "Hrvatski"},
    {"code": "sr", "label_de": "Serbisch", "label_en": "Serbian", "native": "Srpski"},
    {"code": "sl", "label_de": "Slowenisch", "label_en": "Slovenian", "native": "Slovenščina"},
    {"code": "sv", "label_de": "Schwedisch", "label_en": "Swedish", "native": "Svenska"},
    {"code": "da", "label_de": "Dänisch", "label_en": "Danish", "native": "Dansk"},
    {"code": "no", "label_de": "Norwegisch", "label_en": "Norwegian", "native": "Norsk"},
    {"code": "fi", "label_de": "Finnisch", "label_en": "Finnish", "native": "Suomi"},
    {"code": "et", "label_de": "Estnisch", "label_en": "Estonian", "native": "Eesti"},
    {"code": "lv", "label_de": "Lettisch", "label_en": "Latvian", "native": "Latviešu"},
    {"code": "lt", "label_de": "Litauisch", "label_en": "Lithuanian", "native": "Lietuvių"},
    {"code": "ar", "label_de": "Arabisch", "label_en": "Arabic", "native": "العربية"},
    {"code": "he", "label_de": "Hebräisch", "label_en": "Hebrew", "native": "עברית"},
    {"code": "zh", "label_de": "Chinesisch", "label_en": "Chinese", "native": "中文"},
    {"code": "ja", "label_de": "Japanisch", "label_en": "Japanese", "native": "日本語"},
    {"code": "ko", "label_de": "Koreanisch", "label_en": "Korean", "native": "한국어"},
    {"code": "hi", "label_de": "Hindi", "label_en": "Hindi", "native": "हिन्दी"},
)

OFFICE_OUTPUT_FORMATS: tuple[dict[str, str], ...] = (
    {"code": "pdf", "label_de": "PDF"},
    {"code": "docx", "label_de": "Word (DOCX)"},
    {"code": "xlsx", "label_de": "Excel (XLSX)"},
    {"code": "txt", "label_de": "Text"},
)


def list_office_languages() -> list[dict[str, str]]:
    return [dict(row) for row in OFFICE_LANGUAGE_CATALOG]


def list_output_formats() -> list[dict[str, str]]:
    return [dict(row) for row in OFFICE_OUTPUT_FORMATS]


def is_known_language(code: str | None) -> bool:
    c = (code or "").strip().lower().split("-")[0]
    if c in {"auto", ""}:
        return True
    return any(row["code"] == c for row in OFFICE_LANGUAGE_CATALOG)


def language_label_de(code: str | None) -> str:
    c = (code or "").strip().lower().split("-")[0]
    if c in {"", "auto", "unknown"}:
        return "Unbekannt / Auto"
    for row in OFFICE_LANGUAGE_CATALOG:
        if row["code"] == c:
            return row["label_de"]
    return c.upper()


def catalog_public() -> dict[str, Any]:
    return {
        "source_default": "auto",
        "target_default": None,
        "languages": list_office_languages(),
        "output_formats": list_output_formats(),
        "note": "Listed languages are accepted translation targets/sources for the Office executor.",
    }
