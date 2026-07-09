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
            return self._scrub_banned(text).strip()

        original = text
        text = self._scrub_banned(text)
        low = text.lower()

        if intent.intent in (
            "personal_reflection",
            "emotion",
            "philosophy",
            "small_talk",
            "general",
        ) or getattr(intent, "intent", "") == "personal_reflection":
            if any(s in low for s in _UNSOLICITED_SALES + _TEMPLATE_FILLERS):
                text = self._strip_unsolicited_sales(text)
                low = text.lower()

        if not text.strip():
            return self._fallback(intent, visitor_id)

        if _GENERIC_ONLY.match(text):
            return self._fallback(intent, visitor_id)

        if len(text) < 12 and intent.intent != "greeting":
            return self._fallback(intent, visitor_id)

        prev_assistant = self._previous_assistant(messages)
        if prev_assistant and self._too_similar(text, prev_assistant) and len(text) < 40:
            text = self._light_rephrase(text, visitor_id)

        return text.strip() or original.strip()

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

    def _scrub_banned(self, text: str) -> str:
        out = (text or "").strip()
        if not out:
            return out
        original = out
        for phrase in _BANNED:
            if phrase in out.lower():
                out = re.sub(
                    rf"[^.!?\n]*{re.escape(phrase)}[^.!?\n]*[.!?]?\s*",
                    "",
                    out,
                    flags=re.I,
                )
        out = self._strip_reintro(out)
        out = re.sub(r"\n{3,}", "\n\n", out).strip()
        return out or original

    @staticmethod
    def _strip_unsolicited_sales(text: str) -> str:
        lines = []
        for line in text.splitlines():
            low = line.lower()
            if any(s in low for s in _UNSOLICITED_SALES):
                continue
            lines.append(line)
        out = "\n".join(lines).strip()
        return out or text.strip()

    @staticmethod
    def _light_rephrase(text: str, visitor_id: str) -> str:
        """Minor opener tweak — never swap the whole answer for a template pool."""
        openers = ("Понял.", "Хорошо.", "Ясно.", "Слушаю.")
        idx = int(hashlib.sha256(f"{visitor_id}:rephrase".encode()).hexdigest(), 16) % len(openers)
        body = text.strip()
        for opener in openers:
            if body.lower().startswith(opener.lower()):
                body = body[len(opener) :].lstrip()
                break
        return f"{openers[idx]} {body}".strip()

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
