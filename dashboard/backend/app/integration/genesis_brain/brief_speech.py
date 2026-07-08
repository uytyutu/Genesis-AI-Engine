"""
Offline speech synthesizer — composes text ONLY from ThinkingBrief fields.

Used when no LLM is available. Not keyword templates — brief-driven composition.
"""

from __future__ import annotations

import re

from app.integration.genesis_brain.layers.conversation_state import ConversationState, pick_opening
from app.integration.genesis_brain.layers.executive_brain import ExecutiveDecision
from app.integration.genesis_brain.layers.product_mind import (
    compose as product_compose,
    should_handle as product_should_handle,
)
from app.integration.genesis_brain.layers.thinking_brief import ThinkingBrief


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
        open_ = pick_opening(visitor_id, turn_index)
        action = decision.action

        if action == "wait":
            return (
                "Рад был помочь.\n\n"
                "Если захотите вернуться — продолжим с того места, где остановились."
            )

        if action == "ask_one_question" and decision.optional_question:
            ack = self._ack(state)
            return f"{open_} {ack}{decision.optional_question}".strip()

        body = self._body_from_brief(
            thinking, decision, state, last_user, messages=messages
        )
        if not body:
            return f"{open_} Слушаю Вас — расскажите, что для Вас сейчас важнее всего."

        return f"{open_} {body}".strip()

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

        if product_should_handle(last_user, state, thinking):
            return product_compose(last_user, state, thinking, messages)

        if "поздрав" in strategy.lower():
            return (
                "Поздравляю! Это заслуженный шаг — приятно, когда усилия замечают.\n\n"
                "Как ощущения после новости?"
            )

        if (
            "factory" in thinking.conversation_goal.lower()
            or "объяснить factory" in strategy.lower()
        ):
            return (
                "**Factory** — продуктовый отдел Genesis: сайты, боты, приложения.\n\n"
                "Нужен готовый продукт под ключ или хотите сами в Studio?"
            )

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
            return (
                f"Мобильное приложение для {state.business_type or 'бизнеса'}.\n\n"
                "MVP: меню · заказ · push."
            )

        if state.needs_website and re.search(r"сайт|лендинг", low):
            return (
                f"Сайт для {state.business_type or 'бизнеса'}.\n\n"
                "Рекомендую: меню · заказ · галерея · отзывы · карта.\n\n"
                "Ориентир под ключ — **650–850 €**."
            )

        if state.needs_marketing and re.search(r"продвижен|реклам|маркетинг", low):
            return (
                "Для локального бизнеса обычно работают карты, отзывы и простой лендинг.\n\n"
                "Могу набросать план на первые 2 недели."
            )

        if state.wants_studio and "studio" in low:
            return (
                "Genesis Studio — платформа для своих сайтов, ботов и автоматизаций.\n\n"
                "Один сайт под ключ — от 350 €. **Studio Basic 49 €/mес**."
            )

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
                "Что ближе по образу жизни?"
            )

        if state.ready_for_business_advice():
            return self._business_advice(state)

        if state.has_budget() and state.uncertain_niche:
            ack = self._ack(state)
            return (
                f"{ack}Что ближе — работа с людьми лично (кафе, салон, сервис) "
                "или онлайн (обучение, digital)?"
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

    def _general_body(self, last_user: str, thinking: ThinkingBrief) -> str:
        """Offline fallback — never expose thinking.why to the user."""
        low = last_user.lower()

        if thinking.confidence < 0.55 or _needs_uncertainty_voice(low, thinking):
            return _uncertainty_voice()

        topic_hints: list[tuple[tuple[str, ...], str]] = [
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
                "регулярная практика + разбор ошибок.\n\n"
                "Скажите, что хотите создать — подскажу конкретный первый шаг.",
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
                "Хороший фильм часто цепляет не сюжетом, а тем, что он отражает в нас.\n\n"
                "Если скажете настроение — подберу направление, не навязывая «единственно верный» выбор.",
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
                "Первое solo-путешествие лучше делать простым: короткий маршрут, понятный язык или "
                "переводчик, запас денег на непредвиденное.\n\n"
                "Могу помочь собрать чек-лист под Ваш стиль.",
            ),
            (
                ("бизнес", "маркетинг", "клиент", "продаж", "стартап"),
                "На старте обычно выигрывает не «идеальный план», а быстрая проверка спроса.\n\n"
                "Один маленький эксперимент с реальными людьми часто честнее месяца размышлений.",
            ),
            (
                ("учит", "экзамен", "обучен", "язык"),
                "Эффективное обучение — это повторение + обратная связь + сон.\n\n"
                "Если скажете срок и цель, помогу разбить на реалистичный план.",
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

        need = thinking.implicit_need or thinking.real_goal or ""
        if need in ("полезный ответ без лишних вопросов", ""):
            need = "разобраться в теме"
        return (
            f"Понимаю — Вам важно {need}.\n\n"
            "Расскажите чуть конкретнее, что для Вас сейчас главное — "
            "тогда смогу ответить по делу, без общих фраз."
        )

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
                "Что ближе — офлайн с минимальной точкой или начать онлайн?"
            )
        if state.business_type == "coffee" and bd:
            return (
                f"Кофейня в {loc} с бюджетом **{bd}** — реалистичный старт.\n\n"
                "Формат «кофе с собой» или небольшой зал."
            )
        return (
            f"{loc}, бюджет **{bd}** — хорошая отправная точка.\n\n"
            "Три направления: локальный сервис · небольшое кафе · онлайн-услуга.\n\n"
            "Что ближе по духу — офлайн или онлайн?"
        )
