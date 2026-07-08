"""
Human Calibration — «Поняли ли человека, или ответила программа?»

If programmatic → mark for rewrite (LLM or brief synth second pass).
"""

from __future__ import annotations

import re

from app.integration.genesis_brain.layers.thinking_brief import ThinkingBrief
from app.integration.genesis_brain.types import CalibrationVerdict
from app.integration.genesis_brain.layers.conversation_type import (
    ConversationKind,
    allows_unsolicited_sales,
)

_PROGRAMMATIC_MARKERS = (
    "расскажите о задаче",
    "я — genesis",
    "что для вас сейчас важнее",
    "чем могу помочь",
    "продолжайте — я слушаю",
    "расскажите подробнее",
    "лучшее действие сейчас:",
    "пользователь хочет:",
    "перейдите в раздел",
    "перейдите на",
    "откройте /services",
    "откройте /products",
    "/services",
    "/products",
    "купите pro",
    "studio basic 49",
    "650–850",
    "studio basic",
    "factory",
)

_UNSOLICITED_SALES = (
    "6 страниц",
    "6–7 страниц",
    "650–850",
    "650–950",
    "studio basic",
    "49 €/мес",
    "genesis factory",
    "genesis studio",
    "под ключ — от",
    "под ключ",
    "запись клиентов через сайт",
    "рекомендую сайт",
    "crm",
    "лендинг",
)

_UNSOLICITED_SALES_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"(?:рекоменд|предлага|заказ|услуг|studio|crm|лендинг|под ключ).{0,80}автоматизац"
        r"|автоматизац.{0,80}(?:под ключ|заказать|бизнес)",
        re.I,
    ),
)


def text_has_unsolicited_sales(text: str) -> bool:
    low = (text or "").lower()
    if any(s in low for s in _UNSOLICITED_SALES):
        return True
    return any(p.search(low) for p in _UNSOLICITED_SALES_PATTERNS)


_GENERIC_OPENERS = re.compile(
    r"^(понял[.!]?|хорошо[.!]?|ок[.!]?|ясно[.!]?|отлично[.!]?)\s*$",
    re.I,
)

_MEDICAL_HINT = re.compile(
    r"диагноз|болит|боль|симптом|лекарств|таблетк|давлен|простуд|бессон|витамин|голов",
    re.I,
)
_UNCERTAINTY_OK = re.compile(
    r"не могу утверждать|наверняка|несколько точек зрения|не уверен|не уверена|"
    r"не замен|врач|специалист|сложно сказать",
    re.I,
)

_SMALL_TALK_KINDS = frozenset({"casual_conversation", "humor"})

_GREETING_USER = re.compile(
    r"^(привет|здравствуй|здравствуйте|hello|hi|hey|как\s+дела|как\s+ты|как\s+вы|"
    r"добрый\s+(?:день|вечер|утро)|доброе\s+утро)\b",
    re.I,
)


def _is_small_talk_turn(
    *,
    conversation_kind: ConversationKind | None,
    last_user: str,
    thinking: ThinkingBrief,
) -> bool:
    """Greetings and light chat — short human replies must pass calibration."""
    if conversation_kind in _SMALL_TALK_KINDS:
        return True
    low = (last_user or "").strip().lower()
    if low and _GREETING_USER.match(low) and len(low) < 60:
        return True
    rg = (thinking.real_goal or "").lower()
    if rg in ("человеческий контакт", "живой разговор", "small_talk"):
        return True
    if "контакт" in rg and thinking.recommended_action == "answer":
        return True
    return False


class HumanCalibrationLayer:
    """Pre-delivery gate: understood human vs programmatic reply."""

    def calibrate(
        self,
        answer: str,
        thinking: ThinkingBrief,
        *,
        messages: list[dict[str, str]] | None = None,
    ) -> tuple[str, bool]:
        """Returns (answer, needs_rewrite)."""
        verdict = self.evaluate(answer, thinking, messages=messages)
        return answer, verdict.needs_rewrite

    def evaluate(
        self,
        answer: str,
        thinking: ThinkingBrief,
        *,
        messages: list[dict[str, str]] | None = None,
        conversation_kind: ConversationKind | None = None,
    ) -> CalibrationVerdict:
        """Full calibration verdict with reasons — for Workforce Reality / Dev Mode."""
        text = (answer or "").strip()
        if not text:
            return CalibrationVerdict(
                passed=False,
                needs_rewrite=True,
                reasons=("пустой ответ",),
            )

        low = text.lower()
        reasons: list[str] = []

        last_user = ""
        if messages:
            for m in reversed(messages):
                if m.get("role") == "user":
                    last_user = m.get("content") or ""
                    break

        small_talk = _is_small_talk_turn(
            conversation_kind=conversation_kind,
            last_user=last_user,
            thinking=thinking,
        )

        for m in _PROGRAMMATIC_MARKERS:
            if m in low:
                reasons.append(f"шаблон: «{m}»")

        for a in thinking.avoid:
            if a in low:
                reasons.append(f"нарушение avoid: «{a[:40]}»")

        if _GENERIC_OPENERS.match(text):
            reasons.append("слишком короткий шаблонный ответ")

        if (
            len(text) < 25
            and thinking.recommended_action not in ("wait",)
            and not small_talk
        ):
            reasons.append("слишком короткий для контекста")

        if not small_talk and not self._addresses_need(text, thinking):
            reasons.append("не отражает implicit need / real goal")

        if _MEDICAL_HINT.search(last_user) and not _UNCERTAINTY_OK.search(text):
            reasons.append("медицинский вопрос без осторожности")

        if conversation_kind and not allows_unsolicited_sales(conversation_kind):
            if text_has_unsolicited_sales(text):
                reasons.append("навязчивая продажа вне бизнес-контекста")

        if reasons:
            return CalibrationVerdict(passed=False, needs_rewrite=True, reasons=tuple(reasons))
        return CalibrationVerdict(passed=True, needs_rewrite=False, reasons=("ответ прошёл калибровку",))

    @staticmethod
    def _addresses_need(text: str, thinking: ThinkingBrief) -> bool:
        """Heuristic: reply touches real_goal or implicit_need theme."""
        if not thinking.real_goal and not thinking.implicit_need:
            return True
        low = text.lower()
        needles = []
        for src in (thinking.real_goal, thinking.implicit_need, thinking.why):
            for word in src.lower().split():
                if len(word) > 5:
                    needles.append(word[:6])
        if not needles:
            return True
        hits = sum(1 for n in needles[:8] if n in low)
        return hits >= 1 or len(text) > 80
