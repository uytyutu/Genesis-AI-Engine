"""
Communication style presets — one Vector, adjustable manner.

Manual preset disables auto-detection for that request.
Memory preferred_depth nudges auto mode only.
"""

from __future__ import annotations

import re
from typing import Any, Literal

from app.integration.genesis_brain.colloquial_ru import is_colloquial_register

CommunicationStyle = Literal[
    "auto",
    "professional",
    "friendly",
    "casual",
    "concise",
    "mentor",
]

EffectiveStyle = Literal["professional", "friendly", "casual", "concise", "mentor"]

VALID_STYLES = frozenset(
    {"auto", "professional", "friendly", "casual", "concise", "mentor"}
)

_BUSINESS_RE = re.compile(
    r"коммерческ|предложени|договор|сч[её]т|invoice|proposal|бюджет|"
    r"официальн|деловой|контракт|согласован|юридическ|отч[её]т",
    re.I,
)
_MENTOR_RE = re.compile(
    r"объясни|объясните|научи|научите|как\s+работает|почему\s+так|"
    r"разбери|пошагово|подробн",
    re.I,
)


def normalize_style_request(raw: str | None) -> CommunicationStyle:
    key = (raw or "auto").strip().lower()
    if key in VALID_STYLES:
        return key  # type: ignore[return-value]
    return "auto"


def detect_auto_style(last_user: str) -> EffectiveStyle:
    low = (last_user or "").strip()
    if not low:
        return "friendly"
    if _BUSINESS_RE.search(low):
        return "professional"
    if _MENTOR_RE.search(low):
        return "mentor"
    if is_colloquial_register(low):
        return "casual"
    return "friendly"


def resolve_effective_style(
    requested: str | None,
    last_user: str,
    memory_inferences: dict[str, Any] | None = None,
) -> EffectiveStyle:
    req = normalize_style_request(requested)
    inf = memory_inferences or {}

    if req != "auto":
        return req  # type: ignore[return-value]

    base = detect_auto_style(last_user)
    return apply_style_memory(base, inf)


def apply_style_memory(base: EffectiveStyle, inf: dict[str, Any]) -> EffectiveStyle:
    """Soft nudges from stored habits — business/mentor per-turn signals stay in detect_auto_style."""
    if base in ("professional", "mentor"):
        return base

    pref = inf.get("communication_style_preference")
    depth = inf.get("preferred_depth")

    if pref == "casual" and base == "friendly":
        base = "casual"

    if depth == "brief" and base in ("friendly", "casual"):
        return "concise"
    if depth == "detailed" and base == "friendly":
        return "mentor"
    return base


def style_memory_hint(
    requested: str | None,
    memory_inferences: dict[str, Any] | None,
) -> str:
    if normalize_style_request(requested) != "auto":
        return ""
    inf = memory_inferences or {}
    parts: list[str] = []
    pref = inf.get("communication_style_preference")
    depth = inf.get("preferred_depth")
    if pref == "casual":
        parts.append("пользователь обычно пишет разговорно")
    elif pref == "friendly":
        parts.append("пользователь предпочитает спокойный тон")
    if depth == "brief":
        parts.append("часто пишет коротко — уместны краткие ответы")
    elif depth == "detailed":
        parts.append("иногда просит развёрнутые объяснения")
    if not parts:
        return ""
    return (
        "[Память стиля] "
        + "; ".join(parts)
        + ". Мягкое предпочтение: деловой или явный запрос важнее."
    )


def style_llm_block(effective: EffectiveStyle) -> str:
    blocks: dict[EffectiveStyle, str] = {
        "professional": (
            "Стиль: 💼 Professional. Деловой, точный, спокойный. "
            "На «Вы», без сленга и лишних эмоций. Структура ясная."
        ),
        "friendly": (
            "Стиль: 🙂 Friendly. Тёплый, человечный, уважительный. "
            "На «Вы», без канцелярита и давления."
        ),
        "casual": (
            "Стиль: 😎 Casual. Современный, лёгкий, живой. "
            "Можно «ты», если пользователь так пишет. Допускаются разговорные обороты в ответе."
        ),
        "concise": (
            "Стиль: ⚡ Concise. Максимально коротко: 1–3 предложения. "
            "Без вступлений и списков, если не просят подробнее."
        ),
        "mentor": (
            "Стиль: 🎓 Mentor. Объясняй и обучай: шаги, примеры, проверка понимания. "
            "Дружелюбно, но содержательно."
        ),
    }
    return blocks[effective]


def rhythm_for_style(effective: EffectiveStyle, last_user: str) -> str:
    if effective == "concise":
        return "Ритм: 1–3 коротких предложения. Без воды."
    if effective == "casual":
        return (
            "Ритм: 2–4 предложения, разговорно. Без «Добрый день, рад видеть» и канцелярита."
        )
    if effective == "professional":
        return "Ритм: 2–5 предложений, деловой тон. Факты и ясные выводы."
    if effective == "mentor":
        return "Ритм: 3–6 предложений с объяснением; шаги — если уместно."
    return "Ритм: 2–5 предложений, тёплый разговорный тон."
