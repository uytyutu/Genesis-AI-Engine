"""Idea Generator — original concepts inspired by trend patterns (never copies videos)."""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any

from modules.tiktok_horizon.models import IdeaDraft

_STYLE_VARIANTS = (
    "quick_tip",
    "myth_bust",
    "before_after",
    "checklist",
    "owner_story",
    "contrast_cut",
)

_ANGLE_TEMPLATES = {
    "quick_tip": "Оригинальный угол: один практический совет по «{topic}» без копирования чужих кадров.",
    "myth_bust": "Оригинальный угол: развеять частый миф вокруг «{topic}» своими словами.",
    "before_after": "Оригинальный угол: до/после процесса, связанного с «{topic}» — собственный пример.",
    "checklist": "Оригинальный угол: короткий чек-лист по «{topic}» в уникальной формулировке.",
    "owner_story": "Оригинальный угол: личный опыт владельца по теме «{topic}».",
    "contrast_cut": "Оригинальный угол: контраст «как обычно делают» vs «как сделать лучше» для «{topic}».",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class IdeaGenerator:
    def generate_from_trends(
        self,
        trends: list[dict[str, Any]],
        *,
        limit: int = 5,
        language: str = "ru",
    ) -> list[IdeaDraft]:
        ideas: list[IdeaDraft] = []
        for i, trend in enumerate(trends[:limit]):
            topic = str(trend.get("topic_label") or "pattern")
            style = _STYLE_VARIANTS[i % len(_STYLE_VARIANTS)]
            idea_id = f"idea-{uuid.uuid4().hex[:10]}"
            # Stable originality fingerprint from trend + style (not a clone of any video id)
            fingerprint = hashlib.sha1(
                f"{trend.get('trend_id')}|{style}|{topic}".encode()
            ).hexdigest()[:8]
            title = {
                "ru": f"{_title_ru(style)}: {topic}",
                "de": f"{_title_de(style)}: {topic}",
                "en": f"{_title_en(style)}: {topic}",
            }.get(language, f"{_title_ru(style)}: {topic}")
            angle = _ANGLE_TEMPLATES[style].format(topic=topic)
            ideas.append(
                IdeaDraft(
                    idea_id=idea_id,
                    trend_id=str(trend.get("trend_id") or ""),
                    title=title[:160],
                    angle=angle,
                    style_variant=style,
                    originality_note=(
                        f"Original concept ({fingerprint}). Inspired by pattern "
                        f"«{topic}» — not a remake of any specific video."
                    ),
                    created_at=_now(),
                )
            )
        return ideas


def _title_ru(style: str) -> str:
    return {
        "quick_tip": "Быстрый совет",
        "myth_bust": "Миф vs факт",
        "before_after": "До и после",
        "checklist": "Чек-лист",
        "owner_story": "Из практики",
        "contrast_cut": "Контраст",
    }.get(style, "Идея")


def _title_de(style: str) -> str:
    return {
        "quick_tip": "Schnelltipp",
        "myth_bust": "Mythos vs Fakt",
        "before_after": "Vorher / Nachher",
        "checklist": "Checkliste",
        "owner_story": "Aus der Praxis",
        "contrast_cut": "Kontrast",
    }.get(style, "Idee")


def _title_en(style: str) -> str:
    return {
        "quick_tip": "Quick tip",
        "myth_bust": "Myth vs fact",
        "before_after": "Before / after",
        "checklist": "Checklist",
        "owner_story": "From practice",
        "contrast_cut": "Contrast",
    }.get(style, "Idea")
