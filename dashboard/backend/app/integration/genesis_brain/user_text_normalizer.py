"""
User Text Normalizer — invisible spelling / keyboard repair before classification.

Pipeline position: User → Text Normalizer → Conversation Classifier → Brain → Provider.
Never surfaces corrections to the user («Вы имели в виду…» forbidden).
"""

from __future__ import annotations

import re
from difflib import get_close_matches

from app.integration.genesis_brain.colloquial_ru import expand_colloquial_ru

_TOKEN_RE = re.compile(r"[\wа-яёА-ЯЁ]+|[^\w\s]", re.UNICODE)

# Exact token replacements — high-confidence typos only (not a giant dictionary).
_EXACT_TYPO: dict[str, str] = {
    "погола": "погода",
    "пагода": "погода",
    "рашифровать": "расшифровать",
    "рашифруй": "расшифруй",
    "рашифруйте": "расшифруйте",
    "генезес": "virtus core",
    "генезис": "virtus core",
    "дженезис": "virtus core",
    "женезис": "virtus core",
    "виртус": "virtus",
    "виртуз": "virtus",
    "вирус кор": "virtus core",
    "вирус коре": "virtus core",
    "вектар": "vector",
    "векторр": "vector",
    "можеш": "можешь",
    "памаги": "помоги",
    "памоги": "помоги",
    "помаги": "помоги",
    "зделай": "сделай",
    "зделать": "сделать",
    "ашибку": "ошибку",
    "ашибка": "ошибка",
    "програма": "программа",
    "програму": "программу",
    "преграму": "программу",
    "преграма": "программа",
    "кагда": "когда",
    "пожалуста": "пожалуйста",
    "пожалуйстаа": "пожалуйста",
    "вссё": "всё",
    "вссe": "всё",
    "серввер": "сервер",
    "хачу": "хочу",
    "хочю": "хочу",
    "придкмай": "придумай",
    "аткрой": "открой",
    "открйо": "открой",
    "привте": "привет",
    "здраствуй": "здравствуй",
    "здраствуйте": "здравствуйте",
    "прилодение": "приложение",
    "приложене": "приложение",
    "продвижене": "продвижение",
    "бизнесс": "бизнес",
    "сайтт": "сайт",
    "телеграмм": "telegram",
    "кофейн": "кофейня",
}

# Fuzzy vocabulary — frequent conversational / task words (canonical forms).
_FUZZY_VOCAB: tuple[str, ...] = tuple(
    sorted(
        {
            *_EXACT_TYPO.values(),
            "погода",
            "расшифровать",
            "программа",
            "сервер",
            "можешь",
            "когда",
            "пожалуйста",
            "всё",
            "хочу",
            "нужно",
            "нужен",
            "помоги",
            "помогите",
            "объясни",
            "расскажи",
            "напиши",
            "создай",
            "сделай",
            "придумай",
            "открой",
            "бизнес",
            "сайт",
            "приложение",
            "бот",
            "чатбот",
            "код",
            "ошибка",
            "игра",
            "данные",
            "анализ",
            "документ",
            "автоматизация",
            "разработка",
            "привет",
            "здравствуй",
            "здравствуйте",
            "грустно",
            "поговорим",
            "шутка",
            "наука",
            "физика",
            "квантов",
            "идея",
            "маркетинг",
            "продвижение",
            "virtus",
            "core",
            "vector",
            "вектор",
            "магазин",
            "салон",
            "дела",
        }
    )
)

_PHRASE_FIXES: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\brest\s+api\b", re.I), "REST API"),
    (re.compile(r"\bии-модулями\b", re.I), "ИИ-модулями"),
    (re.compile(r"\bии\s+модулями\b", re.I), "ИИ-модулями"),
    (re.compile(r"\bвиртус\s+кор(?:е)?\b", re.I), "virtus core"),
    (re.compile(r"\bвирус\s+кор(?:е)?\b", re.I), "virtus core"),
)

_NAME_FIXES: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bтомас\s+шелби\b", re.I), "Томас Шелби"),
    (re.compile(r"\bthomas\s+shelby\b", re.I), "Thomas Shelby"),
)

_TECH_CONTEXT = re.compile(
    r"програм|код|api|баз|данн|deploy|backend|frontend|server|сервер|хостинг",
    re.I,
)


def _fix_server_in_tech_context(text: str) -> str:
    if not _TECH_CONTEXT.search(text):
        return text
    return re.sub(r"\bсевер\b", "сервер", text, flags=re.I)


_LATIN_TO_CYR = str.maketrans(
    {
        "a": "а",
        "A": "А",
        "b": "в",
        "B": "В",
        "c": "с",
        "C": "С",
        "e": "е",
        "E": "Е",
        "h": "н",
        "H": "Н",
        "k": "к",
        "K": "К",
        "m": "м",
        "M": "М",
        "o": "о",
        "O": "О",
        "p": "р",
        "P": "Р",
        "t": "т",
        "T": "Т",
        "x": "х",
        "X": "Х",
        "y": "у",
        "Y": "У",
    }
)


def _collapse_repeats(text: str) -> str:
    return re.sub(r"(.)\1{2,}", r"\1\1", text)


def _normalize_punctuation(text: str) -> str:
    out = text.replace("…", "...")
    out = re.sub(r"[ \t]+", " ", out)
    out = re.sub(r"\s+([,.!?;:])", r"\1", out)
    return out.strip()


def _cyrillic_ratio(word: str) -> float:
    if not word:
        return 0.0
    letters = [c for c in word if c.isalpha()]
    if not letters:
        return 0.0
    cyr = sum(1 for c in letters if "\u0400" <= c <= "\u04FF" or c in "ёЁ")
    return cyr / len(letters)


def _fix_mixed_script_token(token: str) -> str:
    if not token or not re.search(r"[A-Za-z]", token) or not re.search(r"[а-яёА-ЯЁ]", token, re.I):
        return token
    if _cyrillic_ratio(token) >= 0.55:
        return token.translate(_LATIN_TO_CYR)
    return token


def _preserve_case(original: str, replacement: str) -> str:
    if not original or not replacement:
        return replacement
    if original.isupper():
        return replacement.upper()
    if original[0].isupper():
        return replacement[0].upper() + replacement[1:]
    return replacement


def _fuzzy_fix_token(token: str) -> str:
    low = token.lower()
    if low in _EXACT_TYPO:
        return _preserve_case(token, _EXACT_TYPO[low])
    if len(low) < 4 or len(low) > 24:
        return token
    if low in _FUZZY_VOCAB:
        return token
    matches = get_close_matches(low, _FUZZY_VOCAB, n=1, cutoff=0.84)
    if not matches:
        return token
    return _preserve_case(token, matches[0])


def _fix_ii_token(token: str) -> str:
    if token.lower() in {"ии", "ii"}:
        return "ИИ"
    return token


def normalize_user_text(text: str) -> str:
    """Repair common typos invisibly — output is for understanding, not meta-correction."""
    raw = (text or "").strip()
    if not raw:
        return ""

    out = _collapse_repeats(raw)
    out = _normalize_punctuation(out)

    for pattern, repl in _PHRASE_FIXES:
        out = pattern.sub(repl, out)
    for pattern, repl in _NAME_FIXES:
        out = pattern.sub(repl, out)

    parts: list[str] = []
    for piece in re.split(r"(\s+)", out):
        if not piece or piece.isspace():
            parts.append(piece)
            continue
        for token in _TOKEN_RE.findall(piece):
            if not re.match(r"[\wа-яёА-ЯЁ]+", token, re.I):
                parts.append(token)
                continue
            fixed = _fix_mixed_script_token(token)
            fixed = _fuzzy_fix_token(fixed)
            fixed = _fix_ii_token(fixed)
            parts.append(fixed)

    result = "".join(parts)
    result = re.sub(r"\s+", " ", result).strip()
    result = _fix_server_in_tech_context(result)
    return expand_colloquial_ru(result)
