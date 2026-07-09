"""
Genesis Self-Critique — «Would ChatGPT answer better?» gate before user sees reply.

Rule-based for Local Mind; strips templates and forces variation without LLM.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any

from app.integration.genesis_brain.layers.intent import IntentBrief
from app.integration.genesis_brain.response_variation import ResponseVariationEngine, _POOLS

_BANNED = (
    "расскажите о задаче",
    "я — genesis",
    "что для вас сейчас важнее",
    "что для вас важнее всего",
    "я вас не понял",
    "универсальный искусственный интеллект",
    "notallowederror",
    "permission denied",
    "чем могу помочь",
    "чем ещё",
    "что ещё",
    "на связи. давайте поговорим",
    "расскажите чуть конкретнее",
)

_UNSOLICITED_SALES = (
    "6 страниц",
    "6–7 страниц",
    "650–850",
    "650–950",
    "studio basic",
    "49 €/мес",
    "factory",
    "genesis factory",
    "под ключ — от",
    "запись клиентов через сайт",
)

_TEMPLATE_FILLERS = (
    "продолжайте — я слушаю",
    "расскажите подробнее",
    "расскажите чуть подробнее",
)

_GENERIC_ONLY = re.compile(
    r"^(понял[.!]?|хорошо[.!]?|ок[.!]?|ясно[.!]?)\s*$",
    re.I,
)


class GenesisSelfCritiqueLayer:
    """Polish or rewrite weak answers before delivery."""

    def __init__(self) -> None:
        self._variation = ResponseVariationEngine()

    def polish(
        self,
        answer: str,
        *,
        intent: IntentBrief,
        messages: list[dict[str, str]] | None = None,
        visitor_id: str = "anonymous",
        provider_id: str = "",
        cloud_llm_used: bool = False,
    ) -> str:
        text = (answer or "").strip()
        if not text:
            if cloud_llm_used:
                return text
            return self._fallback(intent, visitor_id)

        if intent.turn_index > 0:
            text = self._strip_reintro(text)

        if cloud_llm_used:
            low = text.lower()
            if any(b in low for b in _BANNED):
                text = self._strip_reintro(text)
            return text.strip()

        low = text.lower()
        if any(b in low for b in _BANNED):
            text = self._fallback(intent, visitor_id)

        if intent.intent in (
            "personal_reflection",
            "emotion",
            "philosophy",
            "small_talk",
            "general",
        ) or getattr(intent, "intent", "") == "personal_reflection":
            if any(s in low for s in _UNSOLICITED_SALES + _TEMPLATE_FILLERS):
                text = self._fallback(intent, visitor_id)

        # Final scrub — curiosity/LLM may re-introduce banned phrases
        low = text.lower()
        if any(b in low for b in _BANNED):
            text = self._fallback(intent, visitor_id)

        if _GENERIC_ONLY.match(text):
            text = self._fallback(intent, visitor_id)

        prev_assistant = self._previous_assistant(messages)
        if prev_assistant and self._too_similar(text, prev_assistant):
            text = self._variation.vary(text, intent.intent, visitor_id, salt="retry")

        if provider_id == "genesis-local" and self._looks_template(text):
            text = self._variation.vary(text, intent.intent, visitor_id, salt=intent.normalized[:40])

        if len(text) < 12 and intent.intent != "greeting":
            text = self._fallback(intent, visitor_id)

        return text.strip()

    def _fallback(self, intent: IntentBrief, visitor_id: str) -> str:
        if intent.intent in (
            "personal_reflection",
            "emotion",
            "philosophy",
            "small_talk",
            "general",
        ):
            pool = _POOLS.get(intent.intent) or _POOLS["general"]
            return pool[int(hashlib.sha256(f"{visitor_id}:{intent.intent}".encode()).hexdigest(), 16) % len(pool)]
        return self._variation.pick(intent.intent, visitor_id, intent.normalized)

    @staticmethod
    def _strip_reintro(text: str) -> str:
        out = re.sub(r"Я\s*[—\-]\s*\*?\*?Genesis\*?\*?[.!]?\s*", "", text, flags=re.I)
        out = re.sub(
            r"Расскажите\s+(?:подробнее\s+)?о\s+задач[еу][^.\n]*[.]?\s*",
            "",
            out,
            flags=re.I,
        )
        return out.strip() or text

    @staticmethod
    def _previous_assistant(messages: list[dict[str, str]] | None) -> str:
        if not messages:
            return ""
        for m in reversed(messages):
            if m.get("role") == "assistant":
                return (m.get("content") or "").strip()
        return ""

    @staticmethod
    def _too_similar(a: str, b: str) -> bool:
        na = re.sub(r"\s+", " ", a.lower().strip())
        nb = re.sub(r"\s+", " ", b.lower().strip())
        if na == nb:
            return True
        # Jaccard on words
        wa, wb = set(na.split()), set(nb.split())
        if not wa or not wb:
            return False
        return len(wa & wb) / len(wa | wb) > 0.85

    @staticmethod
    def _looks_template(text: str) -> bool:
        markers = ("**1.**", "ориентир", "650–850", "650–950", "от **250")
        hits = sum(1 for m in markers if m in text)
        return hits >= 2 and text.count("\n") > 4
