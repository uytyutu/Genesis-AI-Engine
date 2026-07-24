"""
Offline speech synthesizer — composes text ONLY from ThinkingBrief fields.

Used when no LLM is available. Not keyword templates — brief-driven composition.
"""

from __future__ import annotations

import re

from app.integration.genesis_brain.ai_identity import try_local_identity_reply
from app.integration.genesis_brain.public_brand import BRAND_NAME, STUDIO_NAME
from app.integration.public_truth_catalog import (
    MISSION1_LANDING_TIMELINE,
    studio_unavailable_message,
    unavailable_online_message,
)
from app.integration.genesis_brain.communication_gate import resolve_communication_gate
from app.integration.genesis_brain.layers.conversation_state import (
    ConversationState,
    strip_service_openers,
)
from app.integration.genesis_brain.layers.executive_brain import (
    ExecutiveDecision,
    GenesisExecutiveBrain,
    executive_reply,
)
from app.integration.genesis_brain.layers.emotional_intelligence import (
    EmotionalIntelligenceLayer,
)
from app.integration.genesis_brain.layers.product_mind import (
    compose as product_compose,
    should_handle as product_should_handle,
)
from app.integration.genesis_brain.layers.thinking_brief import ThinkingBrief
from app.integration.genesis_brain.user_text_normalizer import normalize_user_text
from app.integration.locale_service import localized_service_copy

_USER_MESSAGE_MARKER = "User message:\n"
_BRIEF_END_MARKER = "═══ END BRIEF ═══"


def extract_clean_user_text(text: str) -> str:
    """Strip Genesis Mind brief wrapper from LLM-bound user turns."""
    raw = (text or "").strip()
    if not raw:
        return ""
    if _USER_MESSAGE_MARKER in raw:
        return raw.split(_USER_MESSAGE_MARKER, 1)[-1].strip()
    if _BRIEF_END_MARKER in raw:
        tail = raw.split(_BRIEF_END_MARKER, 1)[-1].strip()
        if tail.lower().startswith("user message:"):
            return tail.split(":", 1)[-1].strip()
        return tail
    return raw


def clean_user_messages(messages: list[dict[str, str]] | None) -> list[dict[str, str]]:
    """Return messages with brief-wrapped user turns reduced to the real user text."""
    if not messages:
        return []
    cleaned: list[dict[str, str]] = []
    for msg in messages:
        role = msg.get("role")
        content = msg.get("content") or ""
        if role == "user":
            content = extract_clean_user_text(content)
            content = normalize_user_text(content)
        cleaned.append({"role": role or "user", "content": content})
    return cleaned


def _needs_uncertainty_voice(text: str, thinking: ThinkingBrief) -> bool:
    low = text.lower()
    medical = (
        "диагноз", "болит", "боль", "симптом", "лекарств", "таблетк",
        "давлен", "простуд", "бессон", "витамин", "голов", "серьёзн",
        "медитац",
    )
    unanswerable = (
        "точно будет", "предскаж", "предсказ", "гарантируешь",
        "докажи", "однозначно", "бог существует",
    )
    if any(m in low for m in medical) or any(u in low for u in unanswerable):
        return True
    return thinking.confidence < 0.55


def _uncertainty_voice() -> str:
    return (
        "Не могу утверждать наверняка — здесь есть несколько точек зрения.\n\n"
        "Могу рассказать, что обычно считают специалисты, "
        "но это не замена профессиональной консультации."
    )


class BriefSpeechSynthesizer:
    """Last-resort speech from brief semantics — LLM is preferred."""

    def _finalize_body(self, text: str) -> str:
        return strip_service_openers((text or "").strip())

    def speak(
        self,
        thinking: ThinkingBrief,
        decision: ExecutiveDecision,
        *,
        state: ConversationState,
        visitor_id: str,
        turn_index: int,
        last_user: str = "",
        messages: list[dict[str, str]] | None = None,
    ) -> str:
        clean_messages = clean_user_messages(messages)
        last_user = extract_clean_user_text(last_user)
        if not last_user and clean_messages:
            for msg in reversed(clean_messages):
                if msg.get("role") == "user":
                    last_user = (msg.get("content") or "").strip()
                    break

        action = decision.action

        identity_reply = try_local_identity_reply(
            last_user,
            visitor_id=visitor_id,
            turn_index=turn_index,
            messages=clean_messages,
        )
        if identity_reply:
            return self._finalize_body(identity_reply)

        if action == "wait":
            return self._finalize_body(
                "Рад был помочь.\n\n"
                "Если захотите вернуться — продолжим с того места, где остановились."
            )

        if action == "ask_one_question" and decision.optional_question:
            ack = self._ack(state)
            return self._finalize_body(f"{ack}{decision.optional_question}".strip())

        gate = resolve_communication_gate(last_user, clean_messages, state)

        if gate.product_mind and product_should_handle(last_user, state, thinking):
            return self._finalize_body(
                product_compose(last_user, state, thinking, clean_messages)
            )

        emotional = EmotionalIntelligenceLayer().analyze(last_user)
        exec_brief = GenesisExecutiveBrain().decide(
            state=state,
            last_user=last_user,
            messages=clean_messages,
            turn_index=turn_index,
            emotional=emotional,
        )
        routed = executive_reply(
            exec_brief,
            state,
            last_user,
            visitor_id=visitor_id,
            turn_index=turn_index,
            messages=clean_messages,
        )
        if routed:
            return self._finalize_body(routed)

        body = self._body_from_brief(
            thinking,
            decision,
            state,
            last_user,
            messages=clean_messages,
            commercial=gate.product_mind,
        )
        if not body:
            return self._finalize_body(
                localized_service_copy("error_fallback", "ru")
            )

        return self._finalize_body(body)

    @staticmethod
    def _ack(state: ConversationState) -> str:
        if state.budget_display():
            return f"Бюджет **{state.budget_display()}** — принял. "
        if state.country:
            return f"{state.country} — учту. "
        if state.user_age:
            return f"{state.user_age} лет — принял. "
        return ""

    def _body_from_brief(
        self,
        thinking: ThinkingBrief,
        decision: ExecutiveDecision,
        state: ConversationState,
        last_user: str,
        messages: list[dict[str, str]] | None = None,
        *,
        commercial: bool = False,
    ) -> str:
        action = decision.action
        strategy = thinking.best_response_strategy
        low = last_user.lower()

        if re.search(r"сколько\s+мне\s+лет|какой\s+(?:у\s+меня\s+)?возраст", low):
            if state.user_age:
                return (
                    f"Вам {state.user_age} — я это запомнил из нашего разговора.\n\n"
                    "Если что-то изменилось — поправьте меня."
                )
            return "Вы ещё не говорили свой возраст — сколько Вам лет?"

        if _needs_uncertainty_voice(low, thinking):
            return _uncertainty_voice()

        if thinking.confidence < 0.55:
            return _uncertainty_voice()

        if state.goal in ("open_business", "ai_company"):
            from app.integration.genesis_brain.reasoned_reply import reasoned_business_reply

            routed = reasoned_business_reply(
                state,
                last_user,
                messages=messages,
            )
            if routed:
                return routed

        if not commercial:
            return self._non_commercial_body(thinking, decision, state, last_user)

        if product_should_handle(last_user, state, thinking):
            return product_compose(last_user, state, thinking, messages)

        if "поздрав" in strategy.lower():
            return (
                "Поздравляю! Это заслуженный шаг — приятно, когда усилия замечают."
            )

        if (
            "factory" in thinking.conversation_goal.lower()
            or "объяснить factory" in strategy.lower()
        ):
            return (
                f"**Factory** — продуктовый отдел {BRAND_NAME}: лендинги под ключ (Mission 1).\n\n"
                "Сейчас онлайн — заказ лендинга на /order. Virtus Studio пока в разработке."
            )

        if re.search(r"\bпочему\b", low):
            return self._explain_body(state)

        if "потому" in strategy.lower() or action == "teach":
            return self._explain_body(state)

        if action == "comfort":
            return (
                f"Слышу {thinking.emotional_state} — это нормально.\n\n"
                "Я не могу обещать результат, но могу быть честным: "
                "успех чаще строится годами маленьких шагов, а не одним прыжком."
            )

        if action == "advise" and (
            "финансов" in thinking.real_goal
            or "изменить жизнь" in thinking.conversation_goal
        ):
            age_note = ""
            if state.user_age and state.user_age <= 30:
                age_note = (
                    f"\n\nВ {state.user_age} у Вас ещё длинный горизонт — "
                    "время на эксперименты без спешки «уже поздно»."
                )
            return (
                "Стать миллионером возможно — но деньги обычно следствие, а не цель.\n\n"
                "Они приходят, когда долго создаёте ценность: продукт, компанию, экспертизу. "
                f"Цифра на счёте — итог, а не руль.{age_note}"
            )

        if "сомнение" in thinking.emotional_state or "поддержку" in thinking.real_goal:
            return (
                "Думаю, шансы есть — но не потому, что кто-то может это пообещать.\n\n"
                "Успех почти никогда не приходит одним прыжком. "
                "Чаще это годы ошибок и упрямого «ещё раз попробую». "
                "Гораздо важнее система, которая каждый день приближает Вас к тому, "
                "что для Вас значит успех."
            )

        if state.user_age and "время уходит" in thinking.real_goal:
            return (
                f"{state.user_age} — хороший возраст, чтобы сомневаться и всё равно пробовать.\n\n"
                "Имеет смысл думать не «получится ли разом», "
                "а «что я готов строить 5–10 лет»."
            )

        if state.user_age and thinking.thread.mentioned_wealth:
            return (
                f"Записал: Вам {state.user_age}.\n\n"
                "На фоне разговора о будущем это важная деталь — "
                "ещё много итераций, чтобы найти своё дело."
            )

        if state.user_age:
            return (
                f"{state.user_age} — принял.\n\n"
                "Если хотите — свяжем это с тем, о чём говорили."
            )

        if "извиниться" in thinking.implicit_need or "поняли" in thinking.implicit_need:
            return (
                "Спасибо, что поправили — пересмотрю рекомендацию.\n\n"
                "Расскажите, что именно не сходится — я подстрою совет под вашу ситуацию."
            )

        if state.needs_app and re.search(r"приложен|\bapp\b", low):
            return unavailable_online_message("Мобильное приложение")

        if re.search(r"интернет-магазин", low):
            return unavailable_online_message("Интернет-магазин")

        if state.needs_website and re.search(r"сайт|лендинг", low):
            from app.integration.genesis_brain.product_consultant import (
                try_product_consultant_reply,
            )

            pc = try_product_consultant_reply(last_user, clean_messages, state)
            if pc:
                return pc.answer
            return (
                f"Сайт для {state.business_type or 'бизнеса'}.\n\n"
                "Пакеты: **Basic · Business · Premium** (350 / 650 / 1200 €) на /order.\n\n"
                f"Срок — {MISSION1_LANDING_TIMELINE}. Следующий шаг — выбрать пакет или оформить заказ."
            )

        if state.needs_marketing and re.search(r"продвижен|реклам|маркетинг", low):
            return (
                "Для локального бизнеса обычно работают карты, отзывы и простой лендинг.\n\n"
                "Могу набросать план на первые 2 недели."
            )

        if state.wants_studio and "studio" in low:
            return studio_unavailable_message()

        if action == "explore" or (low.strip() in ("нет", "нет.") and state.goal == "open_business"):
            loc = state.country or "вашем регионе"
            return (
                f"Понял — меняем направление. Три варианта для {loc}:\n\n"
                "**1. Локальный сервис с записью**\n\n"
                "**2. Coffee to go / небольшое кафе**\n\n"
                "**3. Онлайн-услуга или digital**"
            )

        if state.life_goal == "family_time" and state.goal == "open_business":
            return (
                "С учётом цели — больше времени с семьёй — смотрим lean-модели без 24/7 присутствия.\n\n"
                "**1. Онлайн-услуга или digital** — гибкий график.\n\n"
                "**2. Coffee to go** — короткая смена, предсказуемый режим.\n\n"
                "**3. Локальный сервис с записью** — клиенты по расписанию.\n\n"
                "Следующий шаг — выбрать формат под ваш график."
            )

        if state.ready_for_business_advice():
            return self._business_advice(state)

        if state.has_budget() and state.uncertain_niche:
            ack = self._ack(state)
            return (
                f"{ack}Следующий шаг — выбрать формат: офлайн-точка или онлайн-услуга."
            ).strip()

        if state.goal == "open_business" and not state.has_country() and not state.has_budget():
            loc = state.country or "вашем регионе"
            return (
                f"Я бы предложил три направления для {loc}, которые часто хорошо стартуют.\n\n"
                "**1. Локальный сервис с записью** — салон, ремонт, мастер на дом.\n\n"
                "**2. Coffee to go / небольшое кафе** — если нравится офлайн.\n\n"
                "**3. Онлайн-услуга или digital** — консультации, SMM, микро-SaaS.\n\n"
                "Если захотите — потом уточним детали под ваш бюджет и город."
            )

        if state.goal == "open_business" and not state.has_country():
            return (
                "Давайте подберём бизнес, который реально может приносить прибыль.\n\n"
                "В какой стране планируете открываться?"
            )

        if state.goal == "open_business":
            loc = state.country or "вашем регионе"
            bd = state.budget_display()
            return (
                f"Я бы предложил три направления для {loc}"
                + (f" с бюджетом **{bd}**" if bd else "")
                + ".\n\n"
                "**1. Локальный сервис с записью** — salon, ремонт, мастer на dom.\n\n"
                "**2. Coffee to go / небольшое кафе** — если нравится офлайн.\n\n"
                "**3. Онлайн-услуга или digital** — консультации, SMM, микро-SaaS.\n\n"
                "Если захотите — уточним детали."
            )

        if state.goal == "ai_company":
            loc = state.city or state.country or ""
            bd = state.budget_display() or "от 0 €"
            return (
                f"AI-компания{' в ' + loc if loc else ''} — реальный путь с бюджетом **{bd}**.\n\n"
                "**1. Micro-SaaS** — узкая автоматизация для одной ниши.\n\n"
                "**2. AI-агентство** — боты и консалтинг для локального бизнеса.\n\n"
                "**3. Продукт + подписка** — свой инструмент с recurring revenue."
            )

        return self._general_body(last_user, thinking)

    def _non_commercial_body(
        self,
        thinking: ThinkingBrief,
        decision: ExecutiveDecision,
        state: ConversationState,
        last_user: str,
    ) -> str:
        """General conversation offline — no CRM, Studio, sites, or sales stacks."""
        strategy = thinking.best_response_strategy
        low = last_user.lower()
        action = decision.action

        if re.search(r"(?:что\s+такое|что\s+это|расскажи\s+про|объясни)\s+factory\b", low):
            return (
                f"**Factory** — продуктовый отдел {BRAND_NAME}: сайты, боты, приложения.\n\n"
                "Строит цифровые продукты: от идеи до превью и публикации."
            )

        if "поздрав" in strategy.lower():
            return (
                "Поздравляю! Это заслуженный шаг — приятно, когда усилия замечают."
            )

        if action == "comfort":
            return (
                f"Слышу {thinking.emotional_state} — это нормально.\n\n"
                "Я не могу обещать результат, но могу быть честным: "
                "успех чаще строится годами маленьких шагов, а не одним прыжком."
            )

        if ("миллион" in low) or (
            action == "advise"
            and (
                "финансов" in thinking.real_goal
                or "изменить жизнь" in thinking.conversation_goal
            )
        ):
            age_note = ""
            if state.user_age and state.user_age <= 30:
                age_note = (
                    f"\n\nВ {state.user_age} у Вас ещё длинный горизонт — "
                    "время на эксперименты без спешки «уже поздно»."
                )
            return (
                "Стать миллионером возможно — но деньги обычно следствие, а не цель.\n\n"
                "Они приходят, когда долго создаёте ценность: продукт, компанию, экспертизу. "
                f"Цифра на счёте — итог, а не руль.{age_note}"
            )

        if "сомнение" in thinking.emotional_state or "поддержку" in thinking.real_goal:
            return (
                "Думаю, шансы есть — но не потому, что кто-то может это пообещать.\n\n"
                "Успех почти никогда не приходит одним прыжком. "
                "Чаще это годы ошибок и упрямого «ещё раз попробую». "
                "Гораздо важнее система, которая каждый день приближает Вас к тому, "
                "что для Вас значит успех."
            )

        if state.user_age and "время уходит" in thinking.real_goal:
            return (
                f"{state.user_age} — хороший возраст, чтобы сомневаться и всё равно пробовать.\n\n"
                "Имеет смысл думать не «получится ли разом», "
                "а «что я готов строить 5–10 лет»."
            )

        if state.user_age and thinking.thread.mentioned_wealth:
            return (
                f"Записал: Вам {state.user_age}.\n\n"
                "На фоне разговора о будущем это важная деталь — "
                "ещё много итераций, чтобы найти своё дело."
            )

        if state.user_age:
            return (
                f"{state.user_age} — принял.\n\n"
                "Если хотите — свяжем это с тем, о чём говорили."
            )

        if "извиниться" in thinking.implicit_need or "поняли" in thinking.implicit_need:
            return (
                "Спасибо, что поправили — пересмотрю рекомендацию.\n\n"
                "Расскажите, что именно не сходится — я подстрою совет под вашу ситуацию."
            )

        return self._general_body(last_user, thinking)

    def _general_body(self, last_user: str, thinking: ThinkingBrief) -> str:
        """Offline fallback — never expose thinking.why to the user."""
        low = last_user.lower()

        if re.search(r"как\s+дела|как\s+ты|как\s+вы", low):
            return (
                "Всё хорошо, спасибо что спросили.\n\n"
                "Расскажите, чем заняты — помогу с задачей."
            )
        if re.match(r"^(привет|здравств|hello|hi)\b", low):
            return (
                "Привет! Рад на связи.\n\n"
                "О чём думаете — готов помочь с задачей."
            )

        if thinking.confidence < 0.55 or _needs_uncertainty_voice(low, thinking):
            return _uncertainty_voice()

        topic_hints: list[tuple[tuple[str, ...], str]] = [
            (
                ("погод", "weather", "дожд", "солнц", "прогноз"),
                "У меня нет актуальных live-данных о погоде в реальном времени.\n\n"
                "Могу подсказать типичный сезонный климат для региона или как быстро проверить "
                "прогноз в надёжном сервисе.",
            ),
            (
                ("здоров", "болит", "болезн", "беспоко"),
                "Понимаю, что здоровье волнует — это важная тема.\n\n"
                "Я не врач и не могу поставить диагноз, но могу помочь разложить мысли "
                "или подсказать, когда имеет смысл обратиться к специалисту.",
            ),
            (
                ("депресс", "тяжело", "пустот", "не хочется", "стыдно"),
                "Слышу, что сейчас непросто — это важно, что Вы об этом говорите.\n\n"
                "Я не врач и не заменяю поддержку близких, но могу быть рядом в разговоре. "
                "Если состояние держится неделями — имеет смысл обратиться к специалисту.",
            ),
            (
                ("отношен", "партн", "друг", "довер", "ссор"),
                "Отношения редко чинятся одной фразой — обычно нужны время и честный разговор.\n\n"
                "Могу помочь разложить ситуацию по шагам: что произошло, чего Вы хотите, "
                "и какой маленький шаг возможен уже сейчас.",
            ),
            (
                ("мотива", "прокраст", "бросить", "не получается начать"),
                "Мотивация часто приходит после маленького действия, а не до него.\n\n"
                "Попробуйте сократить задачу до 10–15 минут — иногда этого достаточно, "
                "чтобы сдвинуться с места.",
            ),
            (
                ("программ", "python", "javascript", "код", "frontend", "backend"),
                "Для старта в программировании обычно работает связка: маленький проект + "
                "регулярная практика + разбор ошибок.",
            ),
            (
                ("космос", "чёрн", "черн", "вселен", "марс", "звезд"),
                "Космос — область, где многое ещё открыто.\n\n"
                "Могу объяснить идею простыми словами и отметить, где наука уверена, "
                "а где пока гипотезы.",
            ),
            (
                ("философ", "смысл жизни", "свобода воли", "смерт"),
                "На такие вопросы нет одного ответа для всех — есть несколько точек зрения.\n\n"
                "Могу честно разложить основные подходы, без притворства, что знаю «истину».",
            ),
            (
                ("фильм", "кино", "сериал"),
                "Хороший фильм часто цепляет не сюжетом, а тем, что он отражает в нас.",
            ),
            (
                ("музык", "гитар", "мелоди"),
                "Музыка сильно влияет на ритм и настроение — это работает и в обучении, и в отдыхе.\n\n"
                "Для практики обычно лучше короткие ежедневные сессии, чем редкие длинные.",
            ),
            (
                ("игр", "гейм", "steam", "indie"),
                "Игры — и отдых, и искусство, и иногда профессия.\n\n"
                "Если цель — расслабиться, лучше короткие сессии без «ещё один уровень до утра».",
            ),
            (
                ("путешеств", "поездк", "trip", "европ"),
                "Первое solo-путешествие лучше делать простым: короткий маршрут, понятный язык, "
                "запас денег на непредвиденное.",
            ),
            (
                ("бизнес", "маркетинг", "клиент", "продаж", "стартап"),
                "На старте обычно выигрывает не «идеальный план», а быстрая проверка спроса.\n\n"
                "Один маленький эксперимент с реальными людьми часто честнее месяца размышлений.",
            ),
            (
                ("учит", "экзамен", "обучен", "язык"),
                "Эффективное обучение — это повторение + обратная связь + сон.",
            ),
            (
                ("финанс", "деньг", "инвест", "ипотек", "инфляц"),
                "С деньгами важна не одна «волшебная схема», а запас прочности и понятные правила.\n\n"
                "Не могу дать персональный финсовет, но могу объяснить принципы без лишнего риска.",
            ),
            (
                ("быт", "квартир", "сосед", "порядок", "продукт"),
                "Бытовые задачи проще, когда разбить их на 15-минутные блоки.\n\n"
                "Могу предложить конкретный порядок действий под Вашу ситуацию.",
            ),
            (
                ("истор", "импер", "войн", "древн"),
                "История полезна не датами, а паттернами — что люди повторяют, когда меняются условия.\n\n"
                "Могу рассказать связную картину без упрощения «до одной причины».",
            ),
            (
                ("юмор", "анекдот", "смешн", "шут"),
                "Юмор — способ разрядить напряжение, если он не бьёт по людям.\n\n"
                "Могу подкинуть лёгкую мысль или формат шутки — без пошлости и без злости.",
            ),
        ]

        for keys, body in topic_hints:
            if any(k in low for k in keys):
                return body

        return localized_service_copy("error_fallback", "ru")

    @staticmethod
    def _explain_body(state: ConversationState) -> str:
        if (
            state.country == "Россия"
            and state.budget_amount
            and state.budget_amount <= 50000
            and state.budget_currency == "RUB"
        ):
            return (
                "Потому что при бюджете около **10–50 тыс. ₽** в Москве аренда и оборудование "
                "для полноценной кофейни обычно превышают эту сумму уже в первый месяц.\n\n"
                "Я предложил форматы, которые реально укладываются в такой старт."
            )
        bd = state.budget_display() or "не указан"
        loc = state.country or "регион"
        return (
            f"Коротко: я опираюсь на то, что уже знаю — {loc}, бюджет {bd}.\n\n"
            "Если логика не сходится — поправьте меня, и я пересчитаю."
        )

    @staticmethod
    def _business_advice(state: ConversationState) -> str:
        loc = state.city or state.country or "вашем регионе"
        bd = state.budget_display()
        if (
            state.country == "Россия"
            and state.budget_amount
            and state.budget_amount <= 50000
            and state.budget_currency == "RUB"
        ):
            city_note = f" в {state.city}" if state.city else ""
            return (
                f"Теперь картина понятна: {loc}, бюджет около **{bd}**.\n\n"
                f"Честно: классическую кофейню{city_note} на такую сумму открыть практически невозможно.\n\n"
                "Но есть варианты на **10–50 тыс. ₽**: coffee to go, доставка, услуги с записью, digital.\n\n"
                "Следующий шаг — выбрать формат: офлайн с минимальной точкой или старт онлайн."
            )
        if state.business_type == "coffee" and bd:
            return (
                f"Кофейня в {loc} с бюджетом **{bd}** — реалистичный старт.\n\n"
                "Формат «кофе с собой» или небольшой зал."
            )
        return (
            f"{loc}, бюджет **{bd}** — хорошая отправная точка.\n\n"
            "Три направления: локальный сервис · небольшое кафе · онлайн-услуга.\n\n"
            "Следующий шаг — выбрать формат: офлайн или онлайн."
        )
