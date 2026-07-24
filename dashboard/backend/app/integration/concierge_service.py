"""Public visitor fallback — Journey UX when LLM path is unavailable (Mission 1)."""

from __future__ import annotations

import re
from typing import Any

from app.integration.genesis_brain.language_constitution import apply_language_constitution
from app.integration.genesis_brain.public_brand import ASSISTANT_NAME, BRAND_NAME, STUDIO_NAME
from app.integration.public_truth_catalog import (
    MISSION1_LANDING_TIMELINE,
    format_order_packages_block,
    studio_unavailable_message,
    unavailable_online_message,
)


class ConciergeService:
    """Rule-based Journey fallback — organizes project steps, not a consultant chat."""

    def __init__(self, packages: list[dict] | None = None) -> None:
        self._packages = packages or []
        self._min_price = min((p["price_eur"] for p in self._packages), default=350)

    def ask(self, question: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        q = question.strip()
        ctx = self._normalize_context(context)
        last_for_lang = q or str(ctx.get("last_user") or "")

        if not q and not ctx.get("journey_phase"):
            return self._reply(
                "Опишите задачу — например, «сайт для кафе». Подберу пакет и следующий шаг.",
                user_message=last_for_lang,
            )

        lower = q.lower() if q else ""

        if ctx.get("journey_phase") == "launch" and self._is_order_confirmation(lower):
            return self._order_cta(ctx, user_message=last_for_lang)

        if ctx.get("journey_phase") in ("requirements", "quoted") and ctx.get("intent") == "service":
            return self._continue_journey(q, ctx, user_message=last_for_lang)

        if self._match(lower, "привет", "здравств", "hello", "hi", "hallo", "добрый"):
            return self._reply(
                f"Привет! Я {ASSISTANT_NAME} в {BRAND_NAME}.\n\n"
                "Опишите задачу — помогу довести до результата.",
                user_message=last_for_lang,
            )

        if self._detect_studio_intent(lower):
            return self._reply(studio_unavailable_message(), user_message=last_for_lang)

        if self._is_bot_only_request(lower):
            return self._reply(
                unavailable_online_message("Чат-бот"),
                user_message=last_for_lang,
            )

        if self._is_store_request(lower):
            return self._reply(
                unavailable_online_message("Интернет-магазин"),
                user_message=last_for_lang,
            )

        if self._detect_service_intent(lower) or self._is_deliverable_request(lower):
            return self._start_service_journey(q, lower, user_message=last_for_lang)

        if self._match(
            lower,
            "что такое genesis",
            "что такое virtus",
            "что это",
            "кто вы",
            "what is genesis",
            "what is virtus",
            "was ist genesis",
            "was ist virtus",
        ):
            return self._reply(self._what_is_block(), user_message=last_for_lang)

        if self._match(lower, "сколько стоит", "цена", "price", "preis", "стоимость", "пакет"):
            return self._reply(self._pricing_block(), user_message=last_for_lang)

        if self._match(
            lower,
            "подписк",
            "subscription",
            "studio",
            "genesis studio",
            "абонемент",
            "monthly",
        ):
            return self._reply(studio_unavailable_message(), user_message=last_for_lang)

        if self._match(
            lower,
            "после оплат",
            "что будет",
            "что дальше",
            "after pay",
            "nach zahlung",
        ):
            return self._reply(self._after_payment_block(), user_message=last_for_lang)

        if self._match(lower, "сколько времени", "срок", "как долго", "how long", "wie lange"):
            return self._reply(self._timeline_block(), user_message=last_for_lang)

        if self._match(lower, "как работает", "процесс", "how it works", "ablauf"):
            return self._reply(self._process_block(), user_message=last_for_lang)

        return self._reply(
            "Принял запрос.\n\n"
            f"• **Готовый результат** (сайт) — пакеты от **{self._min_price} €** на /order\n"
            f"• **{STUDIO_NAME}** — пока в разработке\n\n"
            "Опишите задачу своими словами — продолжим работу над проектом.",
            user_message=last_for_lang,
        )

    def _start_service_journey(
        self, question: str, lower: str, *, user_message: str
    ) -> dict[str, Any]:
        if re.search(
            r"хочу\s+сайт|нужен\s+сайт|сделать\s+сайт|создать\s+сайт", lower
        ) and not re.search(
            r"кафе|кофе|салон|стоматолог|клиник|магазин|для\s+\w+", lower
        ):
            body = (
                f"Отлично! В {BRAND_NAME} мы создаём сайты в трёх пакетах:\n\n"
                "* **Basic** — одностраничный сайт · **350 €**\n"
                "* **Business** — сайт компании с системой управления · **650 €**\n"
                "* **Premium** — блог, бронирование и CRM · **1200 €**\n\n"
                "Если уже знаете пакет — оформите заказ. Если нет — напишите нишу, помогу выбрать."
            )
            return self._reply(
                body,
                cta_href="/order",
                cta_label="Оформить заказ",
                context={
                    "intent": "service",
                    "journey_phase": "quoted",
                    "project_type": "website",
                },
                user_message=user_message,
            )

        business = self._extract_business(lower) or ("кафе" if "кафе" in lower else None)
        ctx: dict[str, Any] = {
            "intent": "service",
            "journey_phase": "requirements",
            "answers": {"business": business} if business else {},
            "project_type": self._extract_project_type(lower),
        }
        quote = self._build_quote(ctx)
        ctx["journey_phase"] = "quoted"
        ctx["quote"] = quote

        opening = "Отлично"
        if business:
            opening += f" — сайт для **{business}**"
        opening += "."

        body = (
            f"{opening}\n\n"
            f"Чаще всего подходит **{quote['package_name']}** — **{quote['price_eur']} €**, "
            f"срок **{quote['timeline']}**.\n\n"
            f"{quote['summary']}\n\n"
            "Следующий шаг — оформить заказ или написать **«изменить требования»**."
        )
        return self._reply(
            body,
            cta_href=f"/order?package={quote.get('package_id', 'business')}",
            cta_label="Оформить заказ",
            context=ctx,
            user_message=user_message,
        )

    def _continue_journey(
        self, question: str, ctx: dict[str, Any], *, user_message: str
    ) -> dict[str, Any]:
        lower = question.lower()
        if self._is_order_confirmation(lower):
            return self._order_cta(ctx, user_message=user_message)
        if "изменить" in lower or "уточн" in lower:
            ctx = dict(ctx)
            ctx["journey_phase"] = "requirements"
            ctx["answers"] = dict(ctx.get("answers") or {})
            ctx["answers"]["note"] = question.strip()
            quote = self._build_quote(ctx)
            ctx["quote"] = quote
            ctx["journey_phase"] = "quoted"
            return self._reply(
                f"Обновил требования.\n\n"
                f"**{quote['package_name']}** — **{quote['price_eur']} €**, "
                f"срок **{quote['timeline']}**.\n\n"
                f"{quote['summary']}\n\n"
                "Следующий шаг — оформить заказ.",
                context=ctx,
                user_message=user_message,
            )
        quote = ctx.get("quote") or self._build_quote(ctx)
        return self._reply(
            f"Текущий план: **{quote['package_name']}** — **{quote['price_eur']} €**.\n\n"
            "Следующий шаг — **«да»** для оформления или **«изменить требования»**.",
            context=ctx,
            user_message=user_message,
        )

    def _order_cta(self, ctx: dict[str, Any], *, user_message: str) -> dict[str, Any]:
        quote = ctx.get("quote") or self._build_quote(ctx)
        package_id = quote.get("package_id", "business")
        href = f"/order?package={package_id}"
        return self._reply(
            "Переходим к оформлению — на следующем шаге подтвердите детали и цену до оплаты.",
            cta_href=href,
            cta_label="Оформить заказ",
            context={**ctx, "journey_phase": "launch"},
            user_message=user_message,
        )

    def _build_quote(self, ctx: dict[str, Any]) -> dict[str, Any]:
        answers = ctx.get("answers") or {}
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
        timeline = MISSION1_LANDING_TIMELINE

        if re.search(r"\b1\b|одн|одна|лендинг|landing", pages):
            chosen = basic or chosen
            timeline = "около 15 минут"
        elif re.search(r"10|больше|много|15", pages):
            chosen = premium or chosen
            timeline = "около 15 минут"

        if payment and chosen and chosen.get("price_eur", 0) < 650:
            chosen = business or chosen

        business_name = (
            answers.get("cafe_type")
            or answers.get("business")
            or answers.get("venue")
            or "ваш бизнес"
        )
        summary = (
            f"Сайт для **{business_name}**"
            + (" с приёмом оплаты" if payment else "")
            + ("." if has_logo else " — визуал можно добавить на этапе материалов.")
        )

        return {
            "package_id": chosen.get("id", "business"),
            "package_name": chosen.get("name", "Landing Business"),
            "price_eur": chosen.get("price_eur", 650),
            "timeline": timeline,
            "summary": summary,
        }

    def _what_is_block(self) -> str:
        return (
            f"**{BRAND_NAME}** — платформа цифровых услуг: создание сайтов, "
            "модернизация существующих сайтов, автоматизация и AI-решения для бизнеса.\n\n"
            f"Я {ASSISTANT_NAME} — помогаю выбрать услугу и довести до заказа.\n\n"
            f"**Сейчас онлайн:** лендинг от **{self._min_price} €** (Basic / Business / Premium).\n"
            f"**{STUDIO_NAME}** — в разработке, купить онлайн нельзя.\n\n"
            "Следующий шаг — скажите: новый сайт, анализ/ремонт или другой запрос."
        )

    def _pricing_block(self) -> str:
        lines = [
            "Сейчас онлайн — **лендинг** (как на /order):\n",
            format_order_packages_block(self._packages),
            "",
            f"**{STUDIO_NAME}** и другие услуги пока вне онлайн-заказа.",
            "Опишите задачу — подберём пакет под проект.",
        ]
        return "\n".join(lines)

    def _after_payment_block(self) -> str:
        return (
            "После оплаты:\n"
            "1. Подтверждение на email.\n"
            f"2. {BRAND_NAME} начинает работу по brief.\n"
            "3. Статус заказа — этапы и срок.\n"
            "4. Готовый сайт и инструкция по публикации.\n\n"
            f"Ориентир для лендинга — **{MISSION1_LANDING_TIMELINE}** после подтверждения."
        )

    def _timeline_block(self) -> str:
        return (
            f"Лендинг под ключ — **{MISSION1_LANDING_TIMELINE}** после подтверждения заказа.\n\n"
            "Сложные платформы — отдельные проекты; Mission 1 сфокусирован на сайтах для малого бизнеса."
        )

    def _process_block(self) -> str:
        return (
            "Путь проекта:\n"
            "1. Вы описываете задачу.\n"
            "2. Фиксируем brief и цену.\n"
            "3. Оформление и оплата.\n"
            f"4. {BRAND_NAME} создаёт результат.\n"
            "5. Проверка, правки, запуск.\n\n"
            "Без скрытых доплат."
        )

    def _detect_studio_intent(self, lower: str) -> bool:
        return self._match(
            lower,
            "genesis studio",
            "хочу пользоваться genesis",
            "mission control",
            "подписка на studio",
            "купить studio",
        )

    def _detect_service_intent(self, lower: str) -> bool:
        return self._match(
            lower,
            "мне нужен",
            "нужен сайт",
            "нужен лендинг",
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
            "кафе",
            "ресторан",
            "автосервис",
            "салон",
        )

    def _extract_business(self, lower: str) -> str | None:
        patterns = [
            (r"сайт для (.+)", 1),
            (r"лендинг для (.+)", 1),
        ]
        for pattern, group in patterns:
            m = re.search(pattern, lower)
            if m:
                raw = m.group(group).strip(" .,?")
                if len(raw) > 2:
                    return raw[:80]
        if "кафе" in lower:
            return "кафе"
        if self._match(lower, "автосервис", "автомастер"):
            return "автосервис"
        if "ресторан" in lower:
            return "ресторан"
        return None

    def _extract_project_type(self, lower: str) -> str:
        if self._match(lower, "магазин", "shop", "store"):
            return "store"
        return "site"

    def _is_bot_only_request(self, lower: str) -> bool:
        bot = self._match(lower, "чат-бот", "чатбот", "chatbot", "бот для", "telegram")
        site = self._match(lower, "сайт", "лендинг", "магазин")
        return bot and not site

    def _is_store_request(self, lower: str) -> bool:
        return self._match(
            lower,
            "интернет-магазин",
            "онлайн-магазин",
            "e-commerce",
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
            "yes",
            "ok",
            "ок",
        )

    def _is_yes(self, text: str) -> bool:
        lower = (text or "").lower()
        if self._match(lower, "нет", "не нуж", "без оплат", "не надо"):
            return False
        return self._match(lower, "да", "нужен", "нужна", "нужно", "хочу", "yes", "есть")

    def _normalize_context(self, context: dict[str, Any] | None) -> dict[str, Any]:
        if not context:
            return {}
        ctx = dict(context)
        if ctx.get("phase") == "consulting":
            ctx["journey_phase"] = ctx.get("journey_phase") or "requirements"
        if ctx.get("phase") == "quoted":
            ctx["journey_phase"] = "quoted"
        if ctx.get("phase") == "done":
            ctx["journey_phase"] = "launch"
        return ctx

    def _match(self, text: str, *phrases: str) -> bool:
        return any(p in text for p in phrases)

    def _reply(
        self,
        answer: str,
        *,
        cta_href: str | None = None,
        cta_label: str | None = None,
        context: dict[str, Any] | None = None,
        user_message: str = "",
    ) -> dict[str, Any]:
        polished = apply_language_constitution(
            answer,
            user_message=user_message or answer[:200],
        )
        out: dict[str, Any] = {
            "answer": polished,
            "source": "genesis-ai",
            "cta_href": cta_href,
            "cta_label": cta_label,
        }
        if context is not None:
            out["context"] = context
        return out
