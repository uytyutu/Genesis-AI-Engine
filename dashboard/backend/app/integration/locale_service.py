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
        "he",
        "hi",
        "zh-Hans",
        "zh-Hant",
        "ja",
        "ko",
    }
)

CEO_PACK_LOCALES = frozenset({"ru", "en", "de", "uk"})
DEFAULT_LOCALE = "ru"
FALLBACK_LOCALE = "en"


def normalize_order_ui_lang(raw: str | None, *, market_code: str | None = None) -> str:
    """Language stored on the order — CEO packs only (de/en/ru/uk)."""
    if raw:
        loc = resolve_locale(raw)
        if loc in CEO_PACK_LOCALES:
            return loc
        if loc.split("-")[0] in CEO_PACK_LOCALES:
            return loc.split("-")[0]
    if market_code:
        try:
            from app.factory.market_delivery import market_ui_lang

            m = market_ui_lang(market_code)
            if m in CEO_PACK_LOCALES:
                return m
        except Exception:
            pass
    return FALLBACK_LOCALE


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
    """Rule-based assistant: full templates for ru/en/de/uk; others → en until LLM stage."""
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
        "uk": (
            f"Пишіть відповідь українською як {assistant_name}: живо, без шаблонів, "
            "без цитування brief."
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
        "uk": 'Вибачте, зараз не вдалося сформувати відповідь. Спробуйте переформулювати — я тут, щоб допомогти.',

    },
    "attachment_ack": {
        "ru": "Спасибо, я вижу ваши файлы.\n\n",
        "en": "Thanks, I see your files.\n\n",
        "de": "Danke, ich sehe Ihre Dateien.\n\n",
        "uk": 'Дякую, я бачу ваші файли.\n\n',

    },
    "attachment_ack_stored_only": {
        "ru": (
            "Файл(ы) получены: {{files}}.\n"
            "Содержимое пока **не анализируется** — я вижу только имя файла. "
            "Опишите, что важно, текстом в сообщении.\n\n"
        ),
        "en": (
            "File(s) received: {{files}}.\n"
            "Content is **not analyzed yet** — I only see the file name. "
            "Please describe what matters in your message.\n\n"
        ),
        "de": (
            "Datei(en) erhalten: {{files}}.\n"
            "Der Inhalt wird **noch nicht analysiert** — ich sehe nur den Dateinamen. "
            "Beschreiben Sie bitte das Wichtige in Ihrer Nachricht.\n\n"
        ),
        "uk": 'Файл(и) отримано: {{files}}.\nВміст поки **не аналізується** — я бачу лише ім’я файлу. Опишіть, що важливо, текстом у повідомленні.\n\n',

    },
    "attachment_ack_parsed": {
        "ru": "Прочитал: {{files}}.\n\n",
        "en": "Read: {{files}}.\n\n",
        "de": "Gelesen: {{files}}.\n\n",
        "uk": 'Прочитав: {{files}}.\n\n',

    },
    "attachment_brain_legacy": {
        "ru": "Клиент прикрепил файлы:",
        "en": "Client attached files:",
        "de": "Kunde hat Dateien angehängt:",
        "uk": 'Клієнт прикріпив файли:',

    },
    "attachment_brain_stored_header": {
        "ru": (
            "Вложения (только имена файлов — содержимое НЕ доступно). "
            "Не утверждай, что читал документ. Попроси описать суть словами."
        ),
        "en": (
            "Attachments (file names only — content NOT available). "
            "Do not claim you read the document. Ask the user to describe it."
        ),
        "de": (
            "Anhänge (nur Dateinamen — Inhalt NICHT verfügbar). "
            "Behaupte nicht, das Dokument gelesen zu haben."
        ),
        "uk": 'Вкладення (лише імена файлів — вміст НЕ доступний). Не стверджуй, що читав документ. Попроси описати суть словами.',

    },
    "attachment_brain_parsed_header": {
        "ru": "Вложения (часть содержимого доступна ниже):",
        "en": "Attachments (some content available below):",
        "de": "Anhänge (ein Teil des Inhalts unten):",
        "uk": 'Вкладення (частина вмісту доступна нижче):',

    },
    "attachment_brain_stored_only": {
        "ru": "сохранено, содержимое не прочитано",
        "en": "stored only, content not read",
        "de": "nur gespeichert, Inhalt nicht gelesen",
        "uk": 'збережено, вміст не прочитано',

    },
    "attachment_brain_parsed": {
        "ru": "содержимое извлечено",
        "en": "content extracted",
        "de": "Inhalt extrahiert",
        "uk": 'вміст витягнуто',

    },
    "files_only_prompt_transparency": {
        "ru": (
            "Клиент прикрепил файлы без текста. Содержимое файлов недоступно — "
            "только имена. Попроси кратко описать задачу словами."
        ),
        "en": (
            "Client attached files without text. File content is unavailable — "
            "names only. Ask them to describe the task in words."
        ),
        "de": (
            "Kunde hat Dateien ohne Text angehängt. Inhalt nicht verfügbar — "
            "nur Namen. Bitte um eine kurze Beschreibung."
        ),
        "uk": 'Клієнт прикріпив файли без тексту. Вміст файлів недоступний — лише імена. Попроси коротко описати задачу словами.',

    },
    "intake_pdf_brain_rules": {
        "ru": (
            "РЕЖИМ ДОКУМЕНТА (PDF). Отвечай ТОЛЬКО по тексту PDF ниже — не из общих знаний.\n"
            "Если ответа нет в документе — скажи: «Я не нашёл этого в документе.»\n"
            "Уверенность: прямое цитирование → «В документе указано…»; "
            "вывод → «Похоже, что…»; сомнение → «Не могу однозначно определить по этому PDF.»"
        ),
        "en": (
            "DOCUMENT MODE (PDF). Answer ONLY from the PDF text below — not general knowledge.\n"
            "If the answer is not in the document — say: «I did not find that in the document.»\n"
            "Confidence: direct quote → «The document states…»; inference → «It appears that…»; "
            "uncertain → «I cannot determine this clearly from the PDF.»"
        ),
        "de": (
            "DOKUMENTMODUS (PDF). Antworten NUR aus dem PDF-Text unten — kein Allgemeinwissen.\n"
            "Wenn die Antwort nicht im Dokument steht — sagen: «Das habe ich im Dokument nicht gefunden.»\n"
            "Sicherheit: direktes Zitat → «Im Dokument steht…»; Schlussfolgerung → «Es scheint, dass…»; "
            "unsicher → «Das lässt sich aus dem PDF nicht eindeutig bestimmen.»"
        ),
        "uk": 'РЕЖИМ ДОКУМЕНТА (PDF). Відповідай ТІЛЬКИ за текстом PDF нижче — не з загальних знань.\nЯкщо відповіді немає в документі — скажи: «Я не знайшов цього в документі.»\nВпевненість: пряме цитування → «У документі зазначено…»; висновок → «Схоже, що…»; сумнів → «Не можу однозначно визначити за цим PDF.»',

    },
    "attachment_ack_pdf_read": {
        "ru": (
            "Прочитал PDF: {{files}} (первые {{pages}} из {{total}} стр.).\n"
            "Отвечаю по содержимому документа.\n\n"
        ),
        "en": (
            "Read PDF: {{files}} (first {{pages}} of {{total}} pages).\n"
            "Answering from the document content.\n\n"
        ),
        "de": (
            "PDF gelesen: {{files}} (erste {{pages}} von {{total}} Seiten).\n"
            "Antwort basiert auf dem Dokument.\n\n"
        ),
        "uk": 'Прочитав PDF: {{files}} (перші {{pages}} з {{total}} стор.).\nВідповідаю за вмістом документа.\n\n',

    },
}


def localized_service_copy(key: str, locale: str | None) -> str:
    loc = resolve_locale(locale)
    if loc not in CEO_PACK_LOCALES:
        loc = FALLBACK_LOCALE
    return _SERVICE_COPY[key][loc]
