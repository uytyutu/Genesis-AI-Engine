"""Reasoned business replies using ConversationState — never re-ask known facts."""

from __future__ import annotations

import re

from app.integration.genesis_brain.layers.conversation_state import ConversationState, pick_opening
from app.integration.genesis_brain.public_brand import BRAND_NAME, STUDIO_NAME


def reasoned_business_reply(
    state: ConversationState,
    last_user: str,
    *,
    visitor_id: str = "anonymous",
    turn_index: int = 0,
    messages: list[dict[str, str]] | None = None,
) -> str | None:
    """Return None if not a business conversation."""
    from app.integration.genesis_brain.layers.conversation_type import (
        classify_conversation_type,
        is_business_mode,
    )

    talk = classify_conversation_type(
        last_user, messages or [], state
    )
    if not is_business_mode(talk):
        return None

    low = last_user.lower()
    if state.goal != "open_business" and not re.search(
        r"бизнес|придумай|открыть|кофейн|кафе|дело", low
    ):
        if not state.ready_for_business_advice():
            return None

    open_ = pick_opening(visitor_id, turn_index)

    if state.wants_studio or ("studio" in low and "хочу" in low):
        return (
            f"{STUDIO_NAME} — платформа для своих сайтов, ботов и автоматизаций.\n\n"
            "Один сайт под ключ — от 350 €. **Studio Basic 49 €/мес** — сколько угодно проектов.\n\n"
            "Сколько проектов планируете в год?"
        )

    if state.needs_app and re.search(r"приложен|\bapp\b", low):
        where = f" в {state.city or state.country}" if state.has_location() else ""
        return (
            f"{open_} Мобильное приложение{where} для {state.business_type or 'бизнеса'}.\n\n"
            "MVP: меню · заказ · push. Расширенная версия — лояльность и оплата.\n\n"
            "Сайт уже есть или приложение — главный приоритет?"
        )

    if state.needs_marketing and re.search(r"продвижен|реклам|маркетинг", low):
        return (
            f"{open_} Для локального бизнеса обычно работают карты, отзывы и простой лендинг.\n\n"
            "Могу набросать план на первые 2 недели — с чего начнём?"
        )

    if state.needs_website and state.business_type == "coffee" and re.search(
        r"сайт|лендинг", low
    ):
        where = f" в {state.city or state.country}" if state.has_location() else ""
        return (
            f"{open_} Сайт для кофейни{where}.\n\n"
            "Рекомендую: меню · заказ · галерея · отзывы · карта.\n\n"
            "Ориентир под ключ — **650–850 €**. Заведение уже работает?"
        )

    if state.goal == "ai_company" or state.business_type == "car_wash":
        return _advice_specialized(state, open_)

    # --- Enough facts: advise, don't questionnaire ---
    if state.ready_for_business_advice():
        return _advice_when_ready(state, open_)

    # --- One missing fact only ---
    missing = state.missing_critical(messages)
    if missing:
        return _ask_one(missing[0], state, open_)

    # First turn — business intent, need basics
    if re.search(r"бизнес|придумай|открыть|поможешь", low) or state.goal == "open_business":
        if state.has_country() and state.has_budget():
            return _advice_when_ready(state, open_)
        if not state.has_country():
            return (
                f"{open_} Давайте подберём бизнес, который реально может приносить прибыль.\n\n"
                "В какой стране планируете открываться?"
            )
        if not state.has_budget():
            where = f" в {state.country}" if state.country else ""
            return (
                f"{open_} {state.country or 'Страна'} — учту{where}.\n\n"
                "Какой бюджет готовы вложить на старт?"
            )

    return None


def _ask_one(gap: str, state: ConversationState, open_: str) -> str:
    ack = _fact_ack(state)
    if gap == "country":
        return f"{open_} {ack}В какой стране планируете открываться?"
    if gap == "budget":
        where = f" ({state.city}, {state.country})" if state.city and state.country else (
            f" ({state.country})" if state.country else ""
        )
        return f"{open_} {ack}Какой бюджет готовы вложить на старт{where}?"
    if gap == "niche":
        return (
            f"{open_} {ack}Что ближе — работа с людьми лично (кафе, салон, сервис) "
            "или онлайн (обучение, digital)?"
        )
    return f"{open_} {ack}Расскажите чуть подробнее — что хотите получить?"


def _fact_ack(state: ConversationState) -> str:
    parts: list[str] = []
    if state.budget_display():
        parts.append(f"Бюджет **{state.budget_display()}** — принял.")
    elif state.country:
        parts.append(f"{state.country} — учту.")
    if not parts:
        return ""
    return " ".join(parts) + " "


def _advice_when_ready(state: ConversationState, open_: str) -> str:
    loc = state.city or state.country or "вашем регионе"
    bd = state.budget_display()

    # Moscow + ~10k RUB — realistic advice (CEO scenario)
    if (
        state.country == "Россия"
        and state.budget_amount
        and state.budget_amount <= 50000
        and state.budget_currency == "RUB"
    ):
        city_note = f" в {state.city}" if state.city else ""
        return (
            f"{open_} Теперь картина понятна: {loc}, бюджет около **{bd}**.\n\n"
            f"Честно: классическую кофейню{city_note} на такую сумму открыть практически невозможно — "
            "аренда и оборудование съедят бюджет за первый месяц.\n\n"
            "Но есть варианты, которые реально стартуют с **10–50 тыс. ₽**:\n"
            "• **Кофе with you** — точка в проходном месте без зала\n"
            "• **Доставка/напитки** — Instagram + Telegram-бот, без аренды\n"
            "• **Услуги с записью** — маникюр, ремонт телефонов, репетиторство\n"
            "• **Digital** — консультации, дизайн, SMM для локального бизнеса\n\n"
            "Что ближе — офлайн с минимальной точкой или начать онлайн?"
        )

    if state.business_type == "coffee" and state.budget_currency == "EUR" and state.budget_amount:
        return (
            f"{open_} Кофейня в {loc} с бюджетом **{bd}** — реалистичный старт.\n\n"
            "Формат «кофе с собой» или небольшой зал в спальном районе.\n\n"
            "Следующий шаг — карта и простой сайт. Начнём с сайта?"
        )

    if state.uncertain_niche or not state.business_type:
        return (
            f"{open_} {loc}, бюджет **{bd}** — хорошая отправная точка.\n\n"
            "Три направления под такой старт:\n"
            "• локальный сервис с онлайн-записью\n"
            "• небольшое кафе / coffee to go\n"
            "• онлайн-услуга (обучение, digital, консультации)\n\n"
            "Что ближе по духу — офлайн или онлайн?"
        )

    return (
        f"{open_} {loc}, бюджет **{bd}**, цель — открыть бизнес.\n\n"
        "Могу предложить конкретный план на первые 30 дней. С чего хотите начать — идея или юридическое оформление?"
    )


def _advice_specialized(state: ConversationState, open_: str) -> str:
    loc = state.city or state.country or "вашем регионе"
    bd = state.budget_display()
    motiv = ""
    if state.life_goal == "financial_independence":
        motiv = " Цель — финансовая независимость, поэтому смотрим на масштабируемость."
    elif state.life_goal == "family_time":
        motiv = " Цель — больше времени с семьёй, поэтому lean-модели без 24/7 присутствия."

    if state.goal == "ai_company":
        return (
            f"{open_} AI-компания{(' в ' + loc) if state.has_location() else ''} — "
            f"реальный путь с бюджетом **{bd or 'от 0 €'}**.{motiv}\n\n"
            f"**1. Micro-SaaS** — узкая автоматизация для одной ниши (Factory · {BRAND_NAME} как база).\n\n"
            "**2. AI-агентство** — боты и консалтинг для локального бизнеса.\n\n"
            "**3. Продукт + подписка** — свой инструмент с recurring revenue.\n\n"
            "Если захотите — уточним, что ближе: продукт или услуги."
        )

    if state.business_type == "car_wash":
        return (
            f"{open_} Автомойка в {loc} с бюджетом **{bd or 'уточняем'}**.\n\n"
            "Форматы: self-service (ниже CAPEX) · ручная мойка · комбо с кофе/магазином.\n\n"
            "На старте важны локация и пропускная способность — могу набросать чек-лист на первую неделю."
        )

    return _advice_when_ready(state, open_)
