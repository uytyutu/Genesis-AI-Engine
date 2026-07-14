"""
Self-critique — strip banned chatbot phrases; no template pool substitution.
"""

from __future__ import annotations

import re

from app.integration.genesis_brain.layers.intent import IntentBrief

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
    "расскажите подробнее",
    "с чего начнём",
    "готовы попробовать",
    "просто поболтаем",
    "слушаю вас — расскажите",
    "чем займёмся",
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

_GENERIC_ONLY = re.compile(
    r"^(понял[.!]?|хорошо[.!]?|ок[.!]?|ясно[.!]?|отлично[.!]?)\s*$",
    re.I,
)


class GenesisSelfCritiqueLayer:
    """Strip weak chatbot phrasing — never replace with another template pool."""

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
            return ""

        if intent.turn_index > 0:
            text = self._strip_reintro(text)

        if cloud_llm_used:
            return self._scrub_banned(text).strip()

        text = self._scrub_banned(text)
        if not text.strip():
            return ""

        if _GENERIC_ONLY.match(text):
            return ""

        if len(text) < 12 and intent.intent != "greeting":
            return ""

        if intent.intent in (
            "personal_reflection",
            "emotion",
            "philosophy",
            "small_talk",
            "general",
        ):
            low = text.lower()
            if any(s in low for s in _UNSOLICITED_SALES):
                text = self._strip_unsolicited_sales(text)

        return text.strip()

    def _scrub_banned(self, text: str) -> str:
        out = (text or "").strip()
        if not out:
            return out
        original = out
        for phrase in _BANNED:
            if phrase in out.lower():
                out = re.sub(re.escape(phrase), "", out, flags=re.I)
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
    def _strip_reintro(text: str) -> str:
        out = re.sub(r"Я\s*[—\-]\s*\*?\*?Genesis\*?\*?[.!]?\s*", "", text, flags=re.I)
        out = re.sub(
            r"Расскажите\s+(?:подробнее\s+)?о\s+задач[еу][^.\n]*[.]?\s*",
            "",
            out,
            flags=re.I,
        )
        return out.strip() or text
