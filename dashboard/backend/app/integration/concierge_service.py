"""Public visitor concierge — intent-aware sales consultant (Mission 1)."""

from __future__ import annotations

import re
from typing import Any

from app.integration.genesis_brain.public_brand import ASSISTANT_NAME, BRAND_NAME, STUDIO_NAME


class ConciergeService:
    """Rule-based fallback for Genesis AI when LLM is unavailable."""

    _CONSULT_KEYS = ("business", "pages", "payment", "logo")
    _CONSULT_PROMPTS = {
        "business": "Для какого бизнеса или проекта нужен сайт?",
        "pages": "Сколько страниц примерно нужно? (например: 1, 3–5, 5–10)",
        "payment": "Нужен ли приём оплаты онлайн на сайте?",
        "logo": "Есть ли у вас логотип и фирменные цвета?",
    }
    _CAFE_KEYS = ("cafe_type", "booking", "logo", "pages")
    _CAFE_PROMPTS = {
        "cafe_type": (
            "Какое у вас заведение?\n\n"
            "• семейное кафе\n"
            "• кофейня\n"
            "• ресторан\n"
            "• фастфуд\n"
            "• другое — напишите своими словами"
        ),
        "booking": "Нужно ли принимать **онлайн-бронирование столиков**?",
        "logo": "Есть ли уже **фирменный стиль или логотип**?",
        "pages": "Сколько страниц примерно нужно? (1, 3–5, 5–10)",
    }

    def __init__(self, packages: list[dict] | None = None) -> None:
        self._packages = packages or []
        self._min_price = min((p["price_eur"] for p in self._packages), default=350)

    def ask(self, question: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        q = question.strip()
        ctx = self._normalize_context(context)

        if not q and not ctx.get("intent"):
            return self._reply(
                "Напишите, что вы хотите создать — например: «сайт для кафе» "
                "или «хочу заказать лендинг». Подберу пакет и цену.",
            )

        lower = q.lower() if q else ""

        if ctx.get("phase") == "quoted" and self._is_order_confirmation(lower):
            return self._order_cta(ctx)

        if ctx.get("phase") == "consulting":
            return self._continue_consultation(q, ctx)

        if self._match(lower, "привет", "здравств", "hello", "hi", "hallo", "добрый"):
            return self._reply(
                f"Здравствуйте! Я — {ASSISTANT_NAME}, интеллектуальный ИИ-помощник {BRAND_NAME}.\n\n"
                "Чем могу помочь? Можете рассказать, что хотите создать — "
                "например, сайт для кафе или магазина — и я подберу решение."
            )

        studio_intent = self._detect_studio_intent(lower)
        service_intent = self._detect_service_intent(lower)

        if studio_intent and not service_intent:
            return self._studio_pitch()

        if self._is_bot_only_request(lower):
            return self._bot_product_reply()

        if self._is_store_request(lower) and not ctx.get("phase"):
            return self._store_quick_quote(lower)

        if service_intent or self._is_deliverable_request(lower):
            return self._start_service_consultation(q, lower, ctx)

        if self._match(
            lower,
            "что такое genesis",
            "что это",
            "кто вы",
            "what is genesis",
            "was ist genesis",
        ):
            return self._reply(
                f"{BRAND_NAME} — интеллектуальная платформа: услуги под ключ и инструменты для самостоятельной работы.\n\n"
                f"**Сейчас доступно:**\n"
                f"• Разговор с {ASSISTANT_NAME} на **/site**\n"
                f"• Заказ **лендинга** — пакеты от **{self._min_price} €** на **/order** (350 / 650 / 1200 €)\n\n"
                f"**{STUDIO_NAME}** (подписка и рабочая среда) **пока в разработке** — купить онлайн нельзя.\n\n"
                f"Я — {ASSISTANT_NAME}, интеллектуальный помощник платформы. Расскажите, какой сайт или бизнес вам нужен.",
            )

        if self._match(lower, "чем отлича", "почему genesis", "why genesis", "anders"):
            return self._reply(
                f"{BRAND_NAME} отличается тем, что вы сразу говорите с консультантом, а не читаете длинный лендинг.\n\n"
                "• Цена до оплаты — без сюрпризов\n"
                "• Короткий диалог — понимаем задачу до заказа\n"
                "• Статус после оплаты — видно, что происходит\n"
                "• ИИ помогает на каждом шаге — не нужно быть технарём",
            )

        if self._match(lower, "сколько стоит", "цена", "price", "preis", "стоимость", "пакет"):
            return self._pricing_reply()

        if self._match(
            lower,
            "подписк",
            "subscription",
            "studio",
            "genesis studio",
            "абонемент",
            "месяц",
            "monthly",
        ):
            return self._studio_pitch()

        if self._match(
            lower,
            "после оплат",
            "что будет",
            "что дальше",
            "after pay",
            "nach zahlung",
        ):
            return self._reply(
                "После оплаты:\n"
                "1. Вы получаете подтверждение заказа на email.\n"
                f"2. {BRAND_NAME} начинает работу по вашим ответам.\n"
                "3. На странице статуса видно этапы и ориентировочный срок.\n"
                "4. Мы передаём готовый сайт и инструкцию по публикации.\n\n"
                "Обычно базовый лендинг — **5–14 дней** после подтверждения заказа.",
            )

        if self._match(lower, "сколько времени", "срок", "как долго", "how long", "wie lange"):
            return self._reply(
                "Для лендинга под ключ ориентир — **5–14 дней** после подтверждения заказа. "
                "Точный срок зависит от пакета и сложности — вы увидите его в статусе заказа.\n\n"
                "Мобильные приложения, игры и сложные платформы — отдельные проекты; "
                "сейчас Mission 1 сфокусирован на сайтах для малого бизнеса.",
            )

        if self._match(lower, "не мож", "огранич", "limit", "cannot", "können nicht"):
            return self._reply(
                f"Честно о границах {BRAND_NAME} сейчас:\n\n"
                "✔ Сайты и лендинги для малого бизнеса — основной фокус\n"
                "✔ Консультация, цена, заказ, статус — здесь, в диалоге\n"
                "◐ Мобильные приложения и игры — обсуждаем; полный цикл позже\n"
                f"✘ {BRAND_NAME} не обещает «100% попадание в алгоритмы» соцсетей\n"
                "✘ Крупные корпоративные контракты — CEO подключается отдельно",
            )

        if self._match(lower, "приложен", "mobile app", "app ", "ios", "android"):
            return self._reply(
                f"Мобильные приложения — в дорожной карте {BRAND_NAME}, но сейчас Mission 1 сфокусирован на сайтах "
                "как самом быстром пути к результату для малого бизнеса.\n\n"
                "Могу помочь с сайтом, который отлично работает на телефоне — для многих бизнесов "
                "это 80% эффекта быстрее и дешевле. Расскажите о вашем бизнесе подробнее.",
            )

        if self._match(lower, "игр", "game"):
            return self._reply(
                f"Игры — отдельное направление в экосистеме {BRAND_NAME}. "
                "Для Mission 1 мы делаем сайты для бизнеса. Если вам нужен сайт для игрового проекта — "
                "опишите задачу, и я подскажу, подходит ли текущий пакет.",
            )

        if self._match(lower, "как работает", "процесс", "how it works", "ablauf"):
            return self._reply(
                "Простой процесс:\n"
                "1. Вы описываете задачу (здесь, в диалоге).\n"
                "2. Я уточняю детали и называю предварительную цену.\n"
                "3. После вашего согласия — оформление заказа и оплата.\n"
                f"4. {BRAND_NAME} создаёт сайт по вашим ответам.\n"
                "5. Вы следите за статусом и получаете результат.\n\n"
                "Без бесконечных созвонов и скрытых доплат.",
            )

        if self._match(lower, "пример", "покаж", "demo", "beispiel"):
            return self._reply(
                "Пример: «Мне нужен сайт для автосервиса» → я задаю несколько вопросов → "
                f"называю цену и срок → вы соглашаетесь → оформляем заказ → {BRAND_NAME} делает сайт.\n\n"
                "Готовы попробовать на своём бизнесе?",
            )

        return self._reply(
            "Я понял запрос. Уточните, пожалуйста:\n\n"
            f"• Вам нужен **готовый результат** (сайт, магазин…) — {BRAND_NAME} сделает за вас?\n"
            f"• Или вы хотите **пользоваться {STUDIO_NAME}** и создавать проекты сами?\n\n"
            "Напишите своими словами — и я подберу правильный путь.",
        )

    def _start_service_consultation(
        self, question: str, lower: str, ctx: dict[str, Any]
    ) -> dict[str, Any]:
        business = self._extract_business(lower)
        project = self._extract_project_type(lower)
        flow = "cafe" if self._is_cafe_request(lower) else "default"

        ctx = {
            "intent": "service",
            "phase": "consulting",
            "step": 0,
            "answers": {},
            "project_type": project,
            "flow": flow,
        }
        if business and flow != "cafe":
            ctx["answers"]["business"] = business
            ctx["step"] = 1
        if flow == "cafe":
            ctx["answers"]["venue"] = "кафе"

        opening = self._service_opening(lower, business, project, flow)
        next_key = self._next_consult_key(ctx)
        if next_key is None:
            return self._present_quote(ctx, prefix=opening)

        prompt = self._consult_prompt(ctx, next_key)
        return self._reply(
            f"{opening}\n\n{prompt}",
            context=ctx,
        )

    def _continue_consultation(self, question: str, ctx: dict[str, Any]) -> dict[str, Any]:
        lower = question.lower()
        if self._is_meta_question(lower):
            return self._handle_meta_during_consultation(lower, ctx)

        flow = ctx.get("flow")
        if flow == "store":
            ctx = dict(ctx)
            answers = dict(ctx.get("answers") or {})
            answers["catalog_size"] = question.strip()
            ctx["answers"] = answers
            return self._present_store_quote(ctx)

        if flow == "bot":
            ctx = dict(ctx)
            answers = dict(ctx.get("answers") or {})
            answers["bot_scope"] = question.strip()
            ctx["answers"] = answers
            return self._present_bot_quote(ctx)

        key = self._current_consult_key(ctx)
        if key is None:
            return self._present_quote(ctx)

        ctx = dict(ctx)
        answers = dict(ctx.get("answers") or {})
        answers[key] = question.strip()
        ctx["answers"] = answers
        ctx["step"] = int(ctx.get("step", 0)) + 1

        next_key = self._next_consult_key(ctx)
        if next_key is None:
            return self._present_quote(ctx)

        step_num = len(ctx.get("answers") or {}) + 1
        prompt = self._consult_prompt(ctx, next_key)
        lead = "Понял." if step_num > 1 else "Отлично."
        return self._reply(
            f"{lead}\n\n{prompt}",
            context=ctx,
        )

    def _present_store_quote(self, ctx: dict[str, Any]) -> dict[str, Any]:
        return self._reply(
            "Интернет-магазин под ключ **пока нельзя оформить онлайн** — мы делаем только **лендинг** "
            f"(пакеты от {self._min_price} € на /order).\n\n"
            "Могу помочь с сайтом для бизнеса или записать пожелания по магазину для обсуждения позже. "
            "Напишите **«сайт»** или опишите задачу.",
            context={**ctx, "phase": "consulting", "flow": "default"},
        )

    def _present_bot_quote(self, ctx: dict[str, Any]) -> dict[str, Any]:
        return self._unavailable_product_reply(
            "чат-бот",
            "Сейчас онлайн можно заказать **лендинг** — пакеты на /order.",
        )

    def _present_quote(self, ctx: dict[str, Any], prefix: str = "") -> dict[str, Any]:
        quote = self._build_quote(ctx)
        ctx = dict(ctx)
        ctx["phase"] = "quoted"
        ctx["quote"] = quote

        body = prefix + "\n\n" if prefix else ""
        body += (
            "На основании ваших ответов я рекомендую пакет **"
            f"{quote['package_name']}**.\n\n"
            f"**Предварительная стоимость:** {quote['price_eur']} €\n"
            f"**Срок:** {quote['timeline']}\n\n"
            f"{quote['summary']}\n\n"
            "Хотите оформить заказ?\n"
            "Напишите **«да»** или **«изменить требования»**, если нужно что-то уточнить."
        )
        return self._reply(body, context=ctx)

    def _order_cta(self, ctx: dict[str, Any]) -> dict[str, Any]:
        quote = ctx.get("quote") or self._build_quote(ctx)
        package_id = quote.get("package_id", "business")
        href = f"/order?package={package_id}"
        return self._reply(
            "Отлично! На следующем шаге вы подтвердите детали и увидите финальную цену до оплаты.",
            cta_href=href,
            cta_label="Оформить заказ",
            context={**ctx, "phase": "done"},
        )

    def _studio_pitch(self) -> dict[str, Any]:
        return self._reply(
            f"**{STUDIO_NAME}** (рабочая среда и подписка) **пока в разработке** — купить онлайн нельзя.\n\n"
            f"**Сейчас доступно:**\n"
            f"• Бесплатный разговор с Vector на **/site**\n"
            f"• Заказ **лендинга** под ключ — пакеты от **{self._min_price} €** на **/order** "
            "(350 / 650 / 1200 € — как в форме заказа)\n\n"
            "Расскажите, какой сайт или бизнес вам нужен — подберём пакет после короткого разговора.",
        )

    def _bot_product_reply(self) -> dict[str, Any]:
        return self._unavailable_product_reply(
            "чат-бот",
            "Сейчас онлайн можно заказать **лендинг** — напишите, для какого бизнеса нужен сайт.",
        )

    def _unavailable_product_reply(self, product_label: str, alternative: str) -> dict[str, Any]:
        return self._reply(
            f"**{product_label.title()}** под ключ **пока нельзя оформить на сайте**.\n\n"
            f"{alternative}\n\n"
            "Или напишите **hello@genesis-ai-engine.com** — обсудим вручную, когда появится в каталоге.",
        )

    def _store_quick_quote(self, lower: str) -> dict[str, Any]:
        return self._reply(
            "Интернет-магазин под ключ **пока нельзя заказать онлайн**. "
            f"Сейчас мы делаем **лендинги** (от {self._min_price} € на /order).\n\n"
            "Если нужен сайт для бизнеса — опишите задачу. Для магазина — можем обсудить позже по email.",
            context={
                "intent": "service",
                "phase": "consulting",
                "flow": "store",
                "step": 0,
                "answers": {"product": "store"},
            },
        )

    def _service_opening(
        self, lower: str, business: str | None, project: str, flow: str = "default"
    ) -> str:
        if flow == "cafe":
            return (
                "Конечно!\n"
                "Я помогу подобрать оптимальное решение для вашего кафе — "
                "меню, часы работы, бронирование с телефона."
            )
        if self._match(lower, "автосервис", "автомастер", "werkstatt", "car service"):
            return (
                "Отлично! Подберём **сайт для автосервиса** — услуги, карта, запись с телефона."
            )
        if project == "store":
            return "Отлично! Разберём **интернет-магазин** под ваш ассортимент и приём заказов."
        return "Отлично! Я помогу подобрать подходящее решение для вашего бизнеса."

    def _build_quote(self, ctx: dict[str, Any]) -> dict[str, Any]:
        answers = ctx.get("answers") or {}
        flow = ctx.get("flow", "default")
        pages = (answers.get("pages") or "").lower()
        payment = self._is_yes(answers.get("payment", "")) or self._is_yes(
            answers.get("booking", "")
        )
        has_logo = self._is_yes(answers.get("logo", ""))

        pkg_by_price = {p["price_eur"]: p for p in self._packages}
        basic = pkg_by_price.get(350) or (self._packages[0] if self._packages else None)
        business = pkg_by_price.get(650) or basic
        premium = pkg_by_price.get(1200) or business

        chosen = business or {"id": "business", "name": "Landing Business", "price_eur": 650}
        timeline = "10–14 дней"

        if re.search(r"\b1\b|одн|одна|лендинг|landing", pages):
            chosen = basic or chosen
            timeline = "5–7 дней"
        elif re.search(r"10|больше|много|15", pages):
            chosen = premium or chosen
            timeline = "14–21 день"

        if payment and chosen and chosen.get("price_eur", 0) < 650:
            chosen = business or chosen
            timeline = "10–14 дней"

        business_name = (
            answers.get("cafe_type")
            or answers.get("business")
            or answers.get("venue")
            or "ваш бизнес"
        )
        if flow == "cafe":
            summary = (
                f"Сайт для **{business_name}**"
                + (" с онлайн-бронированием" if self._is_yes(answers.get("booking", "")) else "")
                + ("." if has_logo else " — поможем с визуалом, если логотипа пока нет.")
            )
        else:
            summary = (
                f"Сайт для **{business_name}**"
                + (" с приёмом оплаты" if payment else "")
                + ("." if has_logo else " — поможем с визуалом, если логотипа пока нет.")
            )

        return {
            "package_id": chosen.get("id", "business"),
            "package_name": chosen.get("name", "Landing Business"),
            "price_eur": chosen.get("price_eur", 650),
            "timeline": timeline,
            "summary": summary,
        }

    def _detect_studio_intent(self, lower: str) -> bool:
        return self._match(
            lower,
            "genesis studio",
            "хочу пользоваться genesis",
            "пользоваться genesis",
            "пользоваться платформ",
            "создавать проекты сам",
            "сам создавать",
            "сам создаю",
            "доступ к genesis",
            "mission control",
            "media engine",
            "я разработчик",
            "мы агентств",
            "агентство хочет",
            "каждый день в genesis",
            "подписка на studio",
            "купить studio",
            "оформить studio",
        )

    def _detect_service_intent(self, lower: str) -> bool:
        return self._match(
            lower,
            "мне нужен",
            "нужен сайт",
            "нужен лендинг",
            "нужен интернет",
            "нужна игра",
            "нужен магазин",
            "нужна автоматизац",
            "сделайте",
            "создайте",
            "заказать сайт",
        )

    def _is_deliverable_request(self, lower: str) -> bool:
        return self._match(
            lower,
            "сайт",
            "лендинг",
            "website",
            "landing",
            "webseite",
            "кафе",
            "coffee",
            "ресторан",
            "автосервис",
            "автомастер",
            "магазин",
            "shop",
            "e-commerce",
            "онлайн-магазин",
            "салон",
            "клиник",
            "стоматолог",
            "crm",
            "бот для",
        )

    def _extract_business(self, lower: str) -> str | None:
        patterns = [
            (r"сайт для (.+)", 1),
            (r"лендинг для (.+)", 1),
            (r"для (?:моего |моей )?(.+)", 1),
        ]
        for pattern, group in patterns:
            m = re.search(pattern, lower)
            if m:
                raw = m.group(group).strip(" .,?")
                if len(raw) > 2 and raw not in ("бизнеса", "компании"):
                    return self._normalize_business(raw, lower)
        if "кафе" in lower:
            return "кафе"
        if self._match(lower, "автосервис", "автомастер"):
            return "автосервис"
        if "ресторан" in lower:
            return "ресторан"
        return None

    def _normalize_business(self, raw: str, lower: str) -> str:
        if "автосервис" in raw or "автосервис" in lower or "автомастер" in lower:
            return "автосервис"
        if "кафе" in raw or "кафе" in lower:
            return "кафе"
        if "ресторан" in raw or "ресторан" in lower:
            return "ресторан"
        return raw[:80]

    def _extract_project_type(self, lower: str) -> str:
        if self._match(lower, "магазин", "shop", "e-commerce", "онлайн-магазин", "store"):
            return "store"
        if self._match(lower, "приложен", "mobile app", "app "):
            return "app"
        return "site"

    def _normalize_context(self, context: dict[str, Any] | None) -> dict[str, Any]:
        if not context:
            return {}
        return dict(context)

    def _current_consult_key(self, ctx: dict[str, Any]) -> str | None:
        keys = self._consult_keys(ctx)
        step = int(ctx.get("step", 0))
        if step < len(keys):
            return keys[step]
        return None

    def _next_consult_key(self, ctx: dict[str, Any]) -> str | None:
        answers = ctx.get("answers") or {}
        for key in self._consult_keys(ctx):
            if key not in answers or not str(answers[key]).strip():
                return key
        return None

    def _consult_keys(self, ctx: dict[str, Any]) -> tuple[str, ...]:
        if ctx.get("flow") == "cafe":
            return self._CAFE_KEYS
        return self._CONSULT_KEYS

    def _consult_prompt(self, ctx: dict[str, Any], key: str) -> str:
        if ctx.get("flow") == "cafe" and key in self._CAFE_PROMPTS:
            return self._CAFE_PROMPTS[key]
        return self._CONSULT_PROMPTS.get(key, key)

    def _is_cafe_request(self, lower: str) -> bool:
        return self._match(lower, "кафе", "coffee", "кофейн", "bistro") or (
            "ресторан" in lower and "сайт" in lower
        )

    def _is_bot_only_request(self, lower: str) -> bool:
        bot = self._match(
            lower,
            "чат-бот",
            "чатбот",
            "chatbot",
            "бот для",
            "бот в",
            "telegram",
            "телеграм",
            "instagram",
            "инстаграм",
            "whatsapp бот",
        )
        site = self._match(lower, "сайт", "лендинг", "магазин", "интернет-магазин")
        return bot and not site

    def _is_store_request(self, lower: str) -> bool:
        return self._match(
            lower,
            "интернет-магазин",
            "онлайн-магазин",
            "e-commerce",
            "магазин с",
            "магазин",
            "shop",
            "store",
        )

    def _is_order_confirmation(self, lower: str) -> bool:
        return self._match(
            lower,
            "да",
            "давай",
            "оформ",
            "готов",
            "согласен",
            "согласна",
            "хочу заказ",
            "начнём",
            "начнем",
            "поехали",
            "yes",
            "ok",
            "ок",
        )

    def _is_meta_question(self, lower: str) -> bool:
        return self._match(
            lower,
            "сколько стоит",
            "цена",
            "что такое",
            "подписк",
            "studio",
            "genesis studio",
        )

    def _handle_meta_during_consultation(
        self, lower: str, ctx: dict[str, Any]
    ) -> dict[str, Any]:
        if self._match(lower, "подписк", "studio", "genesis studio"):
            studio = self._studio_pitch()
            studio["answer"] += (
                "\n\n_Продолжим расчёт услуги — ответьте на текущий вопрос выше._"
            )
            studio["context"] = ctx
            return studio
        if self._match(lower, "сколько стоит", "цена", "стоимость"):
            pricing = self._pricing_reply()
            pricing["answer"] += (
                "\n\n_Точная сумма будет после пары вопросов — ответьте на текущий вопрос выше._"
            )
            pricing["context"] = ctx
            return pricing
        key = self._current_consult_key(ctx)
        if key:
            return self._reply(
                f"Отвечу подробнее после расчёта. Сейчас важен ответ:\n\n"
                f"{self._consult_prompt(ctx, key)}",
                context=ctx,
            )
        return self._present_quote(ctx)

    def _is_yes(self, text: str) -> bool:
        lower = (text or "").lower()
        if self._match(lower, "нет", "не нуж", "без оплат", "не надо"):
            return False
        return self._match(
            lower,
            "да",
            "нужен",
            "нужна",
            "нужно",
            "хочу",
            "будет",
            "yes",
            "есть",
            "имеется",
            "уже есть",
        )

    def _pricing_reply(self) -> dict[str, Any]:
        lines = [
            "Сейчас онлайн можно заказать **лендинг** — пакеты совпадают с формой на /order:\n",
        ]
        for p in self._packages:
            lines.append(f"• **{p['name']}** — {p['price_eur']} €")
        lines.extend(
            [
                "",
                f"**{STUDIO_NAME}** и другие услуги (магазин, бот) **пока нельзя купить на сайте**.",
                "Начните с разговора на /site или оформите заказ на /order после согласования.",
                "",
                "Расскажите, что именно вам нужно — подберём пакет.",
            ]
        )
        return self._reply("\n".join(lines))

    def _match(self, text: str, *phrases: str) -> bool:
        return any(p in text for p in phrases)

    def _reply(
        self,
        answer: str,
        *,
        cta_href: str | None = None,
        cta_label: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        out: dict[str, Any] = {
            "answer": answer,
            "source": "genesis-ai",
            "cta_href": cta_href,
            "cta_label": cta_label,
        }
        if context is not None:
            out["context"] = context
        return out
