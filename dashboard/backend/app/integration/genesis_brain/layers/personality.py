"""
Personality layer — tone, style, and post-processing only.

Profession and project journey live in core prompt and canon docs, not here.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Literal

from app.config import cloud_first_responses, cloud_proof_mode
from app.integration.genesis_brain.conversation_rhythm import compact_for_turn
from app.integration.genesis_brain.layers.conversation_state import strip_service_openers
from app.integration.genesis_brain.ai_identity import (
    scrub_identity_violations,
)
from app.integration.genesis_brain.language_constitution import apply_language_constitution
from app.integration.locale_service import effective_chat_locale
from app.integration.genesis_brain.layers.conversation_style import (
    ConversationStyleEngine,
)
from app.integration.genesis_brain.public_brand import (
    ASSISTANT_NAME,
    BRAND_NAME,
    scrub_public_brand_text,
)

PersonalityMode = Literal["public", "ceo"]

_VENDOR_PATTERNS = [
    re.compile(r"как\s+(?:большая\s+)?языковая\s+модель", re.I),
    re.compile(r"as\s+an?\s+ai\s+language\s+model", re.I),
    re.compile(r"i(?:'m|\s+am)\s+(?:chatgpt|claude|gemini|gpt)", re.I),
    re.compile(r"я\s+—\s*(?:chatgpt|claude|gemini|gpt|openai|anthropic)", re.I),
    re.compile(r"openai|anthropic|google\s+gemini|deepseek", re.I),
]

_QUESTIONNAIRE = re.compile(
    r"вопрос\s*\d|следующий\s+шаг|заполните\s+форму|сколько\s+страниц\s+нужно",
    re.I,
)

_TY_RE = re.compile(r"\bты\b", re.I)


@dataclass(frozen=True)
class PublicProfile:
    name: str = ASSISTANT_NAME


class GenesisPersonalityLayer:
    """Public tone/style + CEO owner mode; finalize pipeline for language polish."""

    def __init__(self, mode: PersonalityMode = "public") -> None:
        self._mode = mode
        self._style = ConversationStyleEngine()

    @property
    def mode(self) -> PersonalityMode:
        return self._mode

    def personality_block(self) -> str:
        if self._mode == "ceo":
            return self._ceo_block()
        return self._public_block()

    def _public_block(self) -> str:
        return """# Тон и стиль ответа

Спокойный · уважительный · честный · естественный.

## Голос
- На «Вы»; «ты» — только если пользователь стабильно пишет неформально
- Не всезнайка: «не могу утверждать», когда не уверены
- Полезность важнее правоты; ошибку признайте коротко
- Лёгкий юмор допустим; без снисхождения и унижения
- Язык ответа — как у пользователя

## Ритм
- 2–6 предложений в обычном ответе
- Не повторяйте одни и те же приветствия дословно
- На «как дела» / привет — живо, без шаблона «на связи» и без «расскажите конкретнее»
- После первого хода — без «Добрый день, рад снова видеть Вас»
- Если человек сказал «нет» — признайте, не «уточните, пожалуйста»

## Память в речи (если упоминаете)
- Через выводы («Вам важно время с семьёй»), не сухие поля («возраст: 27»)

## Эмпатия
- Если человеку тяжело — короткая поддержка, затем дело"""

    def _ceo_block(self) -> str:
        return f"""# {ASSISTANT_NAME} — CEO mode (только владелец)

Ты — **{ASSISTANT_NAME}**, исполнительный партнёр владельца на платформе **{BRAND_NAME}**. Не пассивный помощник.

## Обязательно
- Кратко: факты → вывод → предложение действия
- Цифры, когда есть данные; честно, когда нет
- Сам инициируй: слабые места, рост, Factory, Sales, Marketing Lab, Wallet, подписки
- Не «чем могу помочь» — «вот что произошло, вот что предлагаю»
- Уважай время владельца"""

    def wrap_system(
        self,
        *,
        base_system: str,
        knowledge_block: str = "",
        memory_block: str = "",
        reasoning_hint: str = "",
        emotional_hint: str = "",
    ) -> str:
        parts = [self.personality_block(), ""]
        if knowledge_block.strip():
            parts.extend([f"## Знания {BRAND_NAME}", knowledge_block.strip(), ""])
        if memory_block.strip():
            parts.extend(["## Память", memory_block.strip(), ""])
        hints = " ".join(h for h in (reasoning_hint, emotional_hint) if h.strip())
        if hints:
            parts.extend(["## Внутренний контекст (не показывать)", hints, ""])
        parts.extend(["---", base_system])
        return "\n".join(parts)

    def finalize(
        self,
        draft: str,
        *,
        messages: list[dict[str, str]] | None = None,
        memory: dict[str, Any] | None = None,
        visitor_id: str = "anonymous",
        user_uses_ty: bool = False,
        cloud_llm_used: bool = False,
        llm_draft_from_provider: bool = False,
        response_style: str | None = None,
    ) -> str:
        if self._mode == "ceo":
            return self._finalize_ceo(draft, messages=messages, memory=memory)

        use_llm_draft = (
            cloud_proof_mode()
            or llm_draft_from_provider
            or (cloud_llm_used and cloud_first_responses())
        )
        if use_llm_draft:
            text = self._clean_vendor(draft) or (draft or "").strip()
            last_user = self._last_user_message(messages)
            if text and text[0].islower():
                text = text[0].upper() + text[1:]
            text = self._enforce_vy(text, user_uses_ty)
            text = self._strip_questionnaire(text)
            turn_index = sum(1 for m in (messages or []) if m.get("role") == "user")
            if turn_index > 0 and last_user and not self._style.is_greeting_message(last_user):
                text = self._suppress_repeat_intro(text)
            user_locale = effective_chat_locale("ru", last_user or "")
            text = scrub_identity_violations(text)
            text = apply_language_constitution(
                text, user_message=last_user or "", ui_locale=user_locale
            )
            return compact_for_turn(
                strip_service_openers(text), last_user=last_user, style=response_style
            )

        # No template pools — only polish a usable LLM draft if present
        last_user = self._last_user_message(messages)
        cleaned = self._clean_vendor(draft) or (draft or "").strip()
        if self._usable_draft(cleaned):
            text = cleaned
            if text and text[0].islower():
                text = text[0].upper() + text[1:]
            text = self._enforce_vy(text, user_uses_ty)
            text = self._strip_questionnaire(text)
            user_locale = effective_chat_locale("ru", last_user or "")
            text = scrub_identity_violations(text)
            text = apply_language_constitution(
                text, user_message=last_user or "", ui_locale=user_locale
            )
            return compact_for_turn(
                strip_service_openers(text), last_user=last_user, style=response_style
            )
        return cleaned

    @staticmethod
    def _substantive_draft(draft: str) -> bool:
        d = (draft or "").strip()
        if len(d) < 32:
            return False
        low = d.lower()
        return "\n\n" in d or "продолжим" in low or "рад был" in low or "**1." in d

    @staticmethod
    def _usable_draft(draft: str) -> bool:
        """True when offline/LLM draft should survive finalize — not swapped for template pools."""
        d = (draft or "").strip()
        if not d:
            return False
        if GenesisPersonalityLayer._substantive_draft(d):
            return True
        if len(d) < 12:
            return False
        low = d.lower()
        template_only = (
            "на связи. давайте поговорим",
            "чем могу помочь",
            "расскажите о задаче",
            "универсальный искусственный интеллект",
        )
        if any(marker in low for marker in template_only) and len(d) < 96:
            return False
        return True

    @staticmethod
    def _is_natural_close(text: str) -> bool:
        low = (text or "").lower()
        return "рад был помочь" in low or "продолжим именно" in low

    def _finalize_ceo(
        self,
        draft: str,
        *,
        messages: list[dict[str, str]] | None = None,
        memory: dict[str, Any] | None = None,
    ) -> str:
        last_user = self._last_user_message(messages).lower()
        name = (memory or {}).get("name") or "Рамиш"

        if not draft.strip() or self._is_morning_ping(last_user):
            return self._ceo_morning_brief(name)

        text = self._clean_vendor(draft)
        if "?" not in text and "предлагаю" not in text.lower():
            text += "\n\nПредлагаю определить приоритет на сегодня — что берём в работу?"
        return text.strip()

    def _ceo_morning_brief(self, name: str) -> str:
        return (
            f"Доброе утро, {name}.\n\n"
            "За ночь (данные обновляются по мере подключения аналитики):\n"
            "• Посетители и диалоги — в отчёте Public Launch\n"
            "• Factory — статус проектов в песочнице\n"
            "• Заказы и оплаты — Wallet / Finance\n\n"
            "Как только метрики полностью подключены, этот бриф будет с конкретными цифрами.\n\n"
            "Предлагаю сегодня: проверить конверсию страницы Studio и один канал Marketing Lab."
        )

    @staticmethod
    def _is_morning_ping(text: str) -> bool:
        return any(
            w in text
            for w in ("доброе утро", "утренний бриф", "что нового", "отчёт", "отчет", "сводка")
        )

    def _clean_vendor(self, text: str) -> str:
        out = (text or "").strip()
        for pat in _VENDOR_PATTERNS:
            out = pat.sub(ASSISTANT_NAME, out)
        out = re.sub(r"\bChatGPT\b", ASSISTANT_NAME, out, flags=re.I)
        out = re.sub(r"\bClaude\b", ASSISTANT_NAME, out, flags=re.I)
        out = re.sub(r"\bGPT-4[o]?\b", ASSISTANT_NAME, out, flags=re.I)
        return scrub_public_brand_text(out)

    def _suppress_repeat_intro(self, text: str) -> str:
        """After first turn — never re-introduce assistant or ask 'tell me your task'."""
        out = text.strip()
        out = re.sub(
            rf"Я\s*[—\-]\s*\*?\*?{re.escape(ASSISTANT_NAME)}\*?\*?[.!]?\s*",
            "",
            out,
            flags=re.I,
        )
        out = re.sub(
            r"Я\s*[—\-]\s*\*?\*?Genesis\*?\*?[.!]?\s*",
            "",
            out,
            flags=re.I,
        )
        out = re.sub(
            r"универсальный искусственный интеллект[.!]?\s*",
            "",
            out,
            flags=re.I,
        )
        out = re.sub(
            r"Расскажите\s+(?:подробнее\s+)?о\s+задач[еу][^.\n]*[.]?\s*",
            "",
            out,
            flags=re.I,
        )
        out = re.sub(
            r"и предложу лучший путь[^.\n]*[.]?\s*",
            "",
            out,
            flags=re.I,
        )
        out = re.sub(r"NotAllowedError[^\n]*", "", out, flags=re.I)
        out = re.sub(r"Permission denied[^\n]*", "", out, flags=re.I)
        out = re.sub(r"\n{3,}", "\n\n", out).strip()
        return out or "Понял. Продолжим — о чём поговорим?"

    def _strip_questionnaire(self, text: str) -> str:
        return text

    @staticmethod
    def _enforce_vy(text: str, user_uses_ty: bool) -> str:
        if user_uses_ty:
            return text
        # Light touch: common informal patterns → Вы
        text = re.sub(r"\bтебя\b", "Вас", text, flags=re.I)
        text = re.sub(r"\bтебе\b", "Вам", text, flags=re.I)
        text = re.sub(r"\bтвой\b", "Ваш", text, flags=re.I)
        text = re.sub(r"\bтвоя\b", "Ваша", text, flags=re.I)
        text = re.sub(r"\bтвоё\b", "Ваше", text, flags=re.I)
        return text

    @staticmethod
    def _last_user_message(messages: list[dict[str, str]] | None) -> str:
        if not messages:
            return ""
        for m in reversed(messages):
            if m.get("role") == "user":
                return (m.get("content") or "").strip()
        return ""

    def user_uses_ty(self, messages: list[dict[str, str]] | None) -> bool:
        for m in messages or []:
            if m.get("role") == "user" and _TY_RE.search(m.get("content") or ""):
                return True
        return False

    # Back-compat alias
    def shape_response(
        self,
        draft: str,
        *,
        messages: list[dict[str, str]] | None = None,
        memory: dict[str, Any] | None = None,
        visitor_id: str = "anonymous",
    ) -> str:
        return self.finalize(
            draft,
            messages=messages,
            memory=memory,
            visitor_id=visitor_id,
            user_uses_ty=self.user_uses_ty(messages),
        )
