"""
Fuzzy NLP — understand meaning despite typos. Never correct the user in replies.
"""

from __future__ import annotations

import re
from difflib import get_close_matches

# Common Russian keyboard / spelling mistakes → canonical token (matching only)
_TYPO_MAP: dict[str, str] = {
    "хачу": "хочу",
    "хочю": "хочу",
    "надо": "нужно",
    "придкмай": "придумай",
    "придумай": "придумай",
    "придумать": "придумать",
    "аткрой": "открой",
    "открйо": "открой",
    "открою": "открою",
    "бизнес": "бизнес",
    "бизнесс": "бизнес",
    "сайт": "сайт",
    "сайтт": "сайт",
    "чатбот": "чатбот",
    "чат-бот": "чатбот",
    "телеграм": "telegram",
    "телеграмм": "telegram",
    "кофейн": "кофейня",
    "кофейню": "кофейня",
    "прилодение": "приложение",
    "приложене": "приложение",
    "продвижене": "продвижение",
    "грустно": "грустно",
    "грустна": "грустно",
    "привет": "привет",
    "привте": "привет",
    "здраствуй": "здравствуй",
    "здраствуйте": "здравствуйте",
}

_KEY_VOCAB = sorted(set(_TYPO_MAP.values()) | set(_TYPO_MAP.keys()) | {
    "хочу", "нужен", "нужно", "сайт", "бизнес", "приложение", "бот", "чатбот",
    "кофейня", "кафе", "магазин", "салон", "studio", "письмо", "наука", "физика",
    "квантов", "идея", "придумай", "открыть", "продвижение", "маркетинг",
    "грустно", "привет", "дела", "шутка", "объясни", "помоги",
})


def _fix_token(token: str) -> str:
    low = token.lower()
    if low in _TYPO_MAP:
        return _TYPO_MAP[low]
    # Do not fuzzy-corrupt long valid words (e.g. «успешным» → «дела»)
    if len(low) > 7:
        return token
    if len(low) < 4:
        return token
    matches = get_close_matches(low, _KEY_VOCAB, n=1, cutoff=0.88)
    if matches:
        return matches[0]
    return token


def normalize_for_intent(text: str) -> str:
    """Normalize user text for intent matching — original meaning preserved."""
    if not text.strip():
        return ""
    # Collapse repeated letters (хачууу → хачу)
    collapsed = re.sub(r"(.)\1{2,}", r"\1\1", text.strip())
    tokens = re.findall(r"[\wа-яёА-ЯЁ\-]+|[^\w\s]", collapsed, flags=re.UNICODE)
    fixed = [_fix_token(t) if re.match(r"[\wа-яёА-ЯЁ\-]+", t, re.I) else t for t in tokens]
    out = "".join(
        f" {t}" if t.isalnum() or re.match(r"[\wа-яё]", t, re.I) else t for t in fixed
    ).strip()
    out = re.sub(r"\s+", " ", out)
    return out.lower()


def contains_any(normalized: str, *patterns: str) -> bool:
    n = normalized.lower()
    return any(p in n for p in patterns)
