"""
Conversation Style Engine — stable voice helpers (no greeting pools).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from app.integration.genesis_brain.public_brand import ASSISTANT_NAME, PUBLIC_WELCOME

_STABLE_GREETING = (
    f"Привет! Я {ASSISTANT_NAME}.\n\n"
    "Опишите задачу — помогу довести до результата."
)

_STABLE_SMALL_TALK = (
    "Всё хорошо, спасибо что спросили.\n\n"
    "Расскажите, чем заняты — помогу с задачей."
)


@dataclass(frozen=True)
class StyleContext:
    visit_count: int = 0
    name: str | None = None
    visitor_id: str = "anonymous"
    hour: int = 12


class ConversationStyleEngine:
    """Detection helpers only — phrasing lives in LLM + brief_speech."""

    def pick_small_talk(self, ctx: StyleContext, message: str = "") -> str:
        return _STABLE_SMALL_TALK

    def pick_greeting(self, ctx: StyleContext) -> str:
        if ctx.visit_count <= 1:
            return PUBLIC_WELCOME or _STABLE_GREETING
        if ctx.name:
            return (
                f"Снова на связи, {ctx.name}.\n\n"
                "Продолжим проект или новая задача?"
            )
        return _STABLE_GREETING

    def pick_closing(self, ctx: StyleContext) -> str | None:
        return None

    def enrich_context(self, profile: dict[str, Any]) -> StyleContext:
        visits = int(profile.get("visit_count") or 0)
        name = profile.get("name") or profile.get("owner_name")
        vid = str(profile.get("visitor_id") or "anonymous")
        hour = datetime.now(timezone.utc).hour
        return StyleContext(visit_count=visits, name=name, visitor_id=vid, hour=hour)

    def build_context(self, profile: dict[str, Any], visitor_id: str = "anonymous") -> StyleContext:
        visits = int(profile.get("visit_count") or 0)
        name = profile.get("name") or profile.get("owner_name")
        hour = datetime.now(timezone.utc).hour
        return StyleContext(
            visit_count=visits,
            name=name,
            visitor_id=(visitor_id or "anonymous")[:64],
            hour=hour,
        )

    @staticmethod
    def is_greeting_message(text: str) -> bool:
        low = (text or "").strip().lower()
        if not low or len(low) > 120:
            return False
        markers = (
            "привет",
            "здравств",
            "hello",
            "hi ",
            " hi",
            "hallo",
            "добрый",
            "доброе утро",
            "добрый день",
            "добрый вечер",
            "хай",
            "hey",
            "салют",
            "здарова",
            "здаров",
            "здрасти",
            "дарова",
            "прив",
        )
        return any(m in low for m in markers)

    @staticmethod
    def is_small_talk_message(text: str) -> bool:
        low = (text or "").strip().lower()
        if not low or len(low) > 80:
            return False
        markers = (
            "как дела",
            "как ты",
            "как вы",
            "как сам",
            "что нового",
            "как жизнь",
            "как настроение",
            "how are you",
        )
        return any(m in low for m in markers)
