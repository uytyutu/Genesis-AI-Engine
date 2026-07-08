"""Human Conversation v1 — short replies, natural rhythm (not LLM essays)."""

from __future__ import annotations

import re

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?…])\s+")


def rhythm_instruction(last_user: str) -> str:
    low = (last_user or "").strip().lower()
    if re.match(r"^(привет|здравствуй|hello|hi|как\s+дела|как\s+ты)\b", low) and len(low) < 40:
        return (
            "Ритм: 1–2 коротких предложения + один живой вопрос о человеке. "
            "Без «Добрый день, рад видеть» и без списков."
        )
    if len(low) < 25 and not "?" in low:
        return "Ритм: 2–4 предложения максимум. Разговор, не лекция."
    return (
        "Ритм: 2–6 предложений. Глубина — только если человек просит подробнее. "
        "Без вступлений и повторов."
    )


def limit_sentences(text: str, max_sentences: int) -> str:
    clean = (text or "").strip()
    if not clean:
        return clean
    parts = [p for p in _SENTENCE_SPLIT.split(clean) if p.strip()]
    if len(parts) <= max_sentences:
        return clean
    return " ".join(parts[:max_sentences]).strip()


def compact_for_turn(text: str, *, last_user: str) -> str:
    low = (last_user or "").strip().lower()
    if re.match(r"^(привет|здравствуй|hello|hi|как\s+дела)\b", low) and len(low) < 50:
        return limit_sentences(text, 3)
    if re.match(r"^нет\.?$", low) or len(low) < 8:
        return limit_sentences(text, 4)
    if len(text) > 520:
        return limit_sentences(text, 6)
    return limit_sentences(text, 8)
