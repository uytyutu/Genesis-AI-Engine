"""Locale detection and resolution for Genesis assistant + UI."""

from __future__ import annotations

import re

SUPPORTED = frozenset(
    {
        "ru",
        "en",
        "de",
        "uk",
        "fr",
        "es",
        "it",
        "pt",
        "pl",
        "tr",
        "ar",
        "fa",
        "hi",
        "zh-Hans",
        "zh-Hant",
        "ja",
        "ko",
    }
)

CEO_PACK_LOCALES = frozenset({"ru", "en", "de"})
DEFAULT_LOCALE = "ru"
FALLBACK_LOCALE = "en"


def resolve_locale(raw: str | None) -> str:
    if not raw:
        return DEFAULT_LOCALE
    norm = raw.strip().replace("_", "-")
    if norm in SUPPORTED:
        return norm
    base = norm.split("-")[0]
    if base in SUPPORTED:
        return base
    return FALLBACK_LOCALE


def detect_locale_from_text(text: str) -> str | None:
    sample = text.strip()[:400]
    if not sample:
        return None

    if re.search(r"[\u0600-\u06FF]", sample):
        return "ar"
    if re.search(r"[\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]", sample):
        return "fa"
    if re.search(r"[\u3040-\u30FF\u31F0-\u31FF]", sample):
        return "ja"
    if re.search(r"[\uAC00-\uD7AF]", sample):
        return "ko"
    if re.search(r"[\u0900-\u097F]", sample):
        return "hi"
    if re.search(r"[\u4E00-\u9FFF]", sample):
        return "zh-Hant" if re.search(r"[體國臺灣萬與為說這]", sample) else "zh-Hans"
    if re.search(r"[\u0400-\u04FF]", sample):
        return "uk" if re.search(r"[іїєґІЇЄҐ]", sample) else "ru"

    lower = sample.lower()
    if re.search(r"\b(der|die|das|und|ich|nicht|wie|was|hallo|guten)\b", lower):
        return "de"
    if re.search(r"\b(the|what|how|hello|status|please)\b", lower):
        return "en"
    if re.search(r"(что|как|привет|статус|дальше|задач)", lower):
        return "ru"
    return None


def effective_chat_locale(ui_locale: str | None, user_message: str) -> str:
    detected = detect_locale_from_text(user_message)
    if detected:
        return resolve_locale(detected)
    return resolve_locale(ui_locale)


def assistant_response_locale(requested: str | None, question: str) -> str:
    """Rule-based assistant: full templates for ru/en/de; others → en until LLM stage."""
    locale = effective_chat_locale(requested, question)
    if locale in CEO_PACK_LOCALES:
        return locale
    return FALLBACK_LOCALE


def resolve_assistant_locale(
    assistant_locale: str | None,
    *,
    ui_locale: str | None = None,
    legacy_locale: str | None = None,
) -> str:
    """Explicit assistant locale from client; legacy `locale` field as fallback."""
    if assistant_locale:
        return resolve_locale(assistant_locale)
    if legacy_locale:
        return resolve_locale(legacy_locale)
    if ui_locale:
        return resolve_locale(ui_locale)
    return DEFAULT_LOCALE


def assistant_llm_language_hint(locale: str, assistant_name: str, brand_name: str) -> str:
    loc = resolve_locale(locale)
    if loc not in CEO_PACK_LOCALES:
        loc = FALLBACK_LOCALE
    hints = {
        "ru": (
            f"Пишите ответ на русском как {assistant_name}: живо, без шаблонов, "
            "без цитирования brief."
        ),
        "en": (
            f"Write your reply in English as {assistant_name}: lively, no templates, "
            "do not quote the brief."
        ),
        "de": (
            f"Schreiben Sie Ihre Antwort auf Deutsch als {assistant_name}: lebendig, "
            "ohne Vorlagen, ohne Zitat des Briefs."
        ),
    }
    return hints[loc]


_SERVICE_COPY: dict[str, dict[str, str]] = {
    "error_fallback": {
        "ru": (
            "Извините, сейчас не удалось сформировать ответ. "
            "Попробуйте переформулировать — я здесь, чтобы помочь."
        ),
        "en": (
            "Sorry, I couldn't form a reply right now. "
            "Try rephrasing — I'm here to help."
        ),
        "de": (
            "Entschuldigung, gerade konnte ich keine Antwort formulieren. "
            "Formulieren Sie es anders — ich bin für Sie da."
        ),
    },
    "attachment_ack": {
        "ru": "Спасибо, я вижу ваши файлы.\n\n",
        "en": "Thanks, I see your files.\n\n",
        "de": "Danke, ich sehe Ihre Dateien.\n\n",
    },
}


def localized_service_copy(key: str, locale: str | None) -> str:
    loc = resolve_locale(locale)
    if loc not in CEO_PACK_LOCALES:
        loc = FALLBACK_LOCALE
    return _SERVICE_COPY[key][loc]
