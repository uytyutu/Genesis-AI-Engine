"""Script Generator — structure, narrator, caption, CTA, hashtags."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from modules.tiktok_horizon.models import IdeaDraft, ScriptDraft


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


_STRUCTURE_BY_STYLE = {
    "quick_tip": ["hook", "problem", "one_tip", "proof", "cta"],
    "myth_bust": ["hook_myth", "truth", "why_it_matters", "cta"],
    "before_after": ["hook", "before", "after", "lesson", "cta"],
    "checklist": ["hook", "item_1", "item_2", "item_3", "cta"],
    "owner_story": ["hook", "context", "turning_point", "result", "cta"],
    "contrast_cut": ["hook", "wrong_way", "better_way", "cta"],
}


class ScriptGenerator:
    def build(
        self,
        idea: IdeaDraft | dict[str, Any],
        *,
        trend: dict[str, Any] | None = None,
        language: str = "ru",
    ) -> ScriptDraft:
        if isinstance(idea, dict):
            idea = IdeaDraft(**{k: idea[k] for k in IdeaDraft.__dataclass_fields__ if k in idea})
        style = idea.style_variant or "quick_tip"
        structure = list(_STRUCTURE_BY_STYLE.get(style, _STRUCTURE_BY_STYLE["quick_tip"]))
        topic = idea.title.split(":", 1)[-1].strip() if ":" in idea.title else idea.title
        hook = _hook(style, topic, language)
        body = _body(style, topic, language)
        cta = {
            "ru": "Сохрани и напиши в комментариях свой кейс.",
            "de": "Speichern und im Kommentar deinen Fall schreiben.",
            "en": "Save this and comment your case.",
        }.get(language, "Сохрани и напиши в комментариях свой кейс.")
        narrator = f"{hook}\n\n{body}\n\n{cta}"
        caption = {
            "ru": f"{hook} — оригинал Virtus Core Horizon.",
            "de": f"{hook} — original von Virtus Core Horizon.",
            "en": f"{hook} — original Virtus Core Horizon.",
        }.get(language, f"{hook} — оригинал Virtus Core Horizon.")
        tags = list((trend or {}).get("hashtag_pattern") or [])[:4]
        if "virtuscore" not in [t.lower() for t in tags]:
            tags.append("virtuscore")
        return ScriptDraft(
            script_id=f"script-{uuid.uuid4().hex[:10]}",
            idea_id=idea.idea_id,
            structure=structure,
            narrator_text=narrator,
            caption=caption[:300],
            cta=cta,
            hashtags=[str(t).lstrip("#") for t in tags][:8],
            hook_seconds=hook[:120],
            style_variant=style,
            created_at=_now(),
        )


def _hook(style: str, topic: str, language: str) -> str:
    if language == "de":
        return {
            "quick_tip": f"Ein Tipp zu «{topic}», den viele übersehen.",
            "myth_bust": f"Mythos über «{topic}» — und was wirklich stimmt.",
            "before_after": f"«{topic}»: vorher chaotisch, nachher klar.",
            "checklist": f"3 Punkte zu «{topic}» vor dem nächsten Schritt.",
            "owner_story": f"Was ich bei «{topic}» falsch gemacht habe.",
            "contrast_cut": f"So macht man «{topic}» oft — und so besser.",
        }.get(style, f"Thema: {topic}")
    if language == "en":
        return {
            "quick_tip": f"One tip about «{topic}» most people miss.",
            "myth_bust": f"A myth about «{topic}» — and the real take.",
            "before_after": f"«{topic}»: messy before, clear after.",
            "checklist": f"3 checks for «{topic}» before you move on.",
            "owner_story": f"What I got wrong about «{topic}».",
            "contrast_cut": f"Common way to do «{topic}» vs a better way.",
        }.get(style, f"Topic: {topic}")
    return {
        "quick_tip": f"Один совет по «{topic}», который часто пропускают.",
        "myth_bust": f"Миф про «{topic}» — и как на самом деле.",
        "before_after": f"«{topic}»: было хаотично — стало ясно.",
        "checklist": f"3 пункта по «{topic}» перед следующим шагом.",
        "owner_story": f"Что я делал не так с «{topic}».",
        "contrast_cut": f"Как обычно делают «{topic}» — и как лучше.",
    }.get(style, f"Тема: {topic}")


def _body(style: str, topic: str, language: str) -> str:
    if language == "de":
        return (
            f"Wir nutzen das Muster «{topic}» nur als Inspiration. "
            "Eigene Formulierung, eigene Beispiele — keine Kopie fremder Clips."
        )
    if language == "en":
        return (
            f"We use the «{topic}» pattern as inspiration only. "
            "Own wording, own examples — never a frame-by-frame remake."
        )
    return (
        f"Паттерн «{topic}» — только вдохновение. "
        "Свои формулировки и примеры, без копирования чужих роликов."
    )
