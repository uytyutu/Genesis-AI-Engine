"""
Colloquial Russian — expand slang / chat speech for understanding only.

Never surface corrections to the user. Used inside User Text Normalizer.
"""

from __future__ import annotations

import re

# Whole-word slang → standard form (intent / LLM understanding).
_COLLOQUIAL_TOKENS: dict[str, str] = {
    "здарова": "привет",
    "здаров": "привет",
    "здрасти": "привет",
    "здрасьте": "здравствуйте",
    "дарова": "привет",
    "прив": "привет",
    "привки": "привет",
    "салют": "привет",
    "хай": "привет",
    "хеллоу": "привет",
    "hello": "привет",
    "hi": "привет",
    "го": "давай",
    "погнали": "давай",
    "харош": "хорошо",
    "хорош": "хорошо",
    "хоршо": "хорошо",
    "изи": "легко",
    "izi": "легко",
    "easy": "легко",
    "рил": "правда",
    "рили": "правда",
    "реал": "правда",
    "really": "правда",
    "кринж": "неловко",
    "кринжово": "неловко",
    "cringe": "неловко",
    "вайб": "атмосфера",
    "вайбы": "атмосфера",
    "vibe": "атмосфера",
    "ща": "сейчас",
    "щас": "сейчас",
    "спс": "спасибо",
    "спасиб": "спасибо",
    "пасиб": "спасибо",
    "thx": "спасибо",
    "thanks": "спасибо",
    "окей": "ок",
    "okay": "ок",
    "оки": "ок",
    "лан": "ладно",
    "лол": "смешно",
    "имхо": "по-моему",
    "норм": "нормально",
    "нормас": "нормально",
    "агась": "да",
    "неа": "нет",
    "че": "что",
    "чё": "что",
    "чо": "что",
    "шо": "что",
}

_COLLOQUIAL_PHRASES: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bч[еёо]\s+как\b", re.I), "как дела"),
    (re.compile(r"\bкак\s+сам\b", re.I), "как дела"),
    (re.compile(r"\bкак\s+дела\b", re.I), "как дела"),
)

# Markers on raw user text — register detection (style hint for LLM).
_COLLOQUIAL_MARKERS: tuple[str, ...] = (
    "здарова",
    "здаров",
    "че как",
    "чё как",
    "чо как",
    "го ",
    " го",
    "харош",
    "изи",
    "рил",
    "кринж",
    "вайб",
    "ща",
    "спс",
    "лан",
    "лол",
    "норм",
    "брат",
    "братан",
    "бро",
)

_WORD_RE = re.compile(r"[\wа-яёА-ЯЁ]+", re.UNICODE)


def _preserve_case(original: str, replacement: str) -> str:
    if not original or not replacement:
        return replacement
    if original.isupper():
        return replacement.upper()
    if original[0].isupper():
        return replacement[0].upper() + replacement[1:]
    return replacement


def expand_colloquial_ru(text: str) -> str:
    """Map conversational tokens/phrases to standard Russian for understanding."""
    out = (text or "").strip()
    if not out:
        return ""

    for pattern, repl in _COLLOQUIAL_PHRASES:
        out = pattern.sub(repl, out)

    parts: list[str] = []
    pos = 0
    for match in _WORD_RE.finditer(out):
        start, end = match.span()
        parts.append(out[pos:start])
        token = match.group(0)
        low = token.lower()
        if low in _COLLOQUIAL_TOKENS:
            parts.append(_preserve_case(token, _COLLOQUIAL_TOKENS[low]))
        else:
            parts.append(token)
        pos = end
    parts.append(out[pos:])
    return re.sub(r"\s+", " ", "".join(parts)).strip()


def is_colloquial_register(text: str) -> bool:
    """True when user message looks conversational / slang-heavy."""
    low = (text or "").strip().lower()
    if not low:
        return False
    if any(m in low for m in _COLLOQUIAL_MARKERS):
        return True
    if re.search(r"\b[а-яё]{1,2}\b", low) and len(low) < 40:
        return True
    return False


def colloquial_understanding_hint() -> str:
    """LLM hint — understand slang; never correct the user aloud."""
    return (
        "[Разговорная речь]\n"
        "Пользователь может писать сленгом, сокращениями или с опечатками. "
        "Понимай смысл; не цитируй и не исправляй его формулировки. "
        "Не говори «Вы имели в виду…». Отвечай естественно — без зеркалирования сленга, "
        "если тон не требует обратного."
    )
