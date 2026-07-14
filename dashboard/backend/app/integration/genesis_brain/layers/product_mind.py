"""
Product Mind v1 — Vector ведёт к результату, а не к продаже.

Result-first: понять цель → предложить путь → помочь получить итог.
Два логичных этапа (под ключ / Studio) — факты Mission 1 без изменения.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from app.integration.genesis_brain.layers.conversation_state import ConversationState
from app.integration.genesis_brain.layers.thinking_brief import ThinkingBrief
from app.integration.public_truth_catalog import studio_unavailable_message, unavailable_online_message

# niche_id -> (label, stack items, service price hint)
_NICHE_STACKS: dict[str, tuple[str, list[str], str]] = {
    "car_wash": (
        "автомойка",
        [
            "сайт с услугами и ценами",
            "Telegram-бот для записи",
            "карточка в Google Maps",
            "простая CRM клиентов",
        ],
        "350 / 650 / 1200 € на /order",
    ),
    "coffee": (
        "кофейня",
        [
            "лендинг с меню и контактами",
            "карты и отзывы",
            "форма заявки",
        ],
        "от 350 € (Basic) или 650 € (Business)",
    ),
    "salon": (
        "салон / клиника",
        [
            "сайт с услугами и галереей",
            "онлайн-запись",
            "AI-консультант на сайте",
            "CRM записей",
        ],
        "от 650 € (Business) или 1200 € (Premium)",
    ),
    "shop": (
        "интернет-магазин",
        [
            "каталог и корзина",
            "оплата онлайн",
            "админка для товаров",
            "базовое SEO",
        ],
        "пока нельзя оформить онлайн — только лендинг",
    ),
    "restaurant": (
        "ресторан / кафе",
        [
            "сайт с меню",
            "бронь столиков",
            "доставка или заказ",
            "карты и отзывы",
        ],
        "от 350 € (Basic) или 650 € (Business)",
    ),
    "landing": (
        "лендинг",
        [
            "одностраничник под продукт или услугу",
            "форма заявки",
            "адаптив и SEO-база",
        ],
        "от 350 € под ключ",
    ),
    "generic_business": (
        "бизнес",
        [
            "сайт или лендинг",
            "запись / заявки клиентов",
            "присутствие в картах и соцсетях",
            "автоматизация рутины (бот, CRM)",
        ],
        "ориентир после brief",
    ),
}

_MULTI_SCALE = re.compile(
    r"несколько\s+точ|много\s+проект|десятк|регулярн|"
    r"каждый\s+месяц|франшиз|сеть\s+|studio|сам\s+(?:хочу|буду)\s+делать",
    re.I,
)
_ONE_OFF = re.compile(
    r"один\s+(?:сайт|магазин|проект|лендинг)|"
    r"только\s+(?:сайт|магазин|бот)|"
    r"под\s+ключ|одну\s+точк|первый\s+раз|"
    r"не\s+планирую\s+много",
    re.I,
)
_PRODUCT_INTENT = re.compile(
    r"сайт|лендинг|магазин|интернет-магазин|бот|telegram|whatsapp|"
    r"кофейн|кафе|автомойк|салон|клиник|открыть|бизнес|crm|"
    r"под\s+ключ|приложен|автоматизац",
    re.I,
)


@dataclass(frozen=True)
class ProductRecommendation:
    niche_label: str
    stack: tuple[str, ...]
    price_hint: str
    scale: str  # one_off | multi | unknown
    recommend: str  # service | studio | both


def detect_niche(text: str, state: ConversationState) -> str:
    low = text.lower()
    if state.business_type and state.business_type in _NICHE_STACKS:
        return state.business_type
    if re.search(r"автомойк|car\s*wash", low):
        return "car_wash"
    if re.search(r"кофейн|кофе|кафе", low) and not re.search(r"не\s+(кофейн|кафе)", low):
        return "coffee"
    if re.search(r"салон|клиник|красот", low):
        return "salon"
    if re.search(r"интернет-магазин|магазин|e-?commerce|shop", low):
        return "shop"
    if re.search(r"ресторан|доставк", low):
        return "restaurant"
    if re.search(r"лендинг|landing", low):
        return "landing"
    if re.search(r"хочу\s+сайт|нужен\s+сайт|сделай\s+сайт", low):
        return "landing"
    return "generic_business"


def infer_scale(text: str, messages: list[dict[str, str]] | None = None) -> str:
    blob = text.lower()
    if messages:
        blob += " " + " ".join(
            (m.get("content") or "") for m in messages if m.get("role") == "user"
        ).lower()
    if _MULTI_SCALE.search(blob):
        return "multi"
    if _ONE_OFF.search(blob):
        return "one_off"
    return "unknown"


def recommend(
    text: str,
    state: ConversationState,
    messages: list[dict[str, str]] | None = None,
) -> ProductRecommendation:
    niche_id = detect_niche(text, state)
    label, stack, price = _NICHE_STACKS.get(niche_id, _NICHE_STACKS["generic_business"])
    scale = infer_scale(text, messages)

    if scale == "multi":
        rec = "studio"
    elif scale == "one_off":
        rec = "service"
    elif niche_id in ("shop", "landing") and scale == "unknown":
        rec = "service"  # default honest: one project → service
    else:
        rec = "both"

    return ProductRecommendation(
        niche_label=label,
        stack=tuple(stack),
        price_hint=price,
        scale=scale,
        recommend=rec,
    )


def should_handle(
    last_user: str,
    state: ConversationState,
    thinking: ThinkingBrief,
) -> bool:
    """Product path — when the user moves toward a concrete digital result."""
    low = last_user.lower()

    personal = re.search(
        r"как\s+думаешь|как\s+считаешь|получится\s+ли|миллион|тяжело|грустн|"
        r"поспал|как\s+дела|космос|философ|смысл\s+жизни|депресс|любов|отношен|"
        r"фильм|музык|игр|программир|python|javascript",
        low,
    )
    if personal and not _PRODUCT_INTENT.search(low):
        return False

    if _PRODUCT_INTENT.search(low):
        return True
    if state.goal == "website" and re.search(
        r"сайт|лендинг|заказ|цена|стоимость|оформ|под\s+ключ|бот|магазин", low
    ):
        return True
    if state.goal == "open_business" and re.search(
        r"сайт|лендинг|бот|магазин|под\s+ключ|сколько\s+стоит|цена", low
    ):
        return True
    return False


def compose(
    last_user: str,
    state: ConversationState,
    thinking: ThinkingBrief,
    messages: list[dict[str, str]] | None = None,
) -> str:
    """Result-first response — path to outcome, navigation never forced."""
    rec = recommend(last_user, state, messages)
    low = last_user.lower()

    if detect_niche(last_user, state) == "shop":
        return unavailable_online_message("Интернет-магазин")

    # Opening — acknowledge niche when user stated it; no generic fillers
    if re.search(r"у меня\s+|есть\s+у меня", low):
        open_line = f"У Вас {rec.niche_label}."
    elif re.search(r"хочу\s+открыть|открыть\s+", low):
        open_line = f"Хорошая цель — {rec.niche_label}."
    elif re.search(r"хочу\s+сайт|нужен\s+сайт|интернет-магазин", low):
        open_line = "Давайте разберём, что именно нужно."
    else:
        open_line = ""

    stack_lines = "\n".join(f"• {item}" for item in rec.stack)
    stack_block = (
        f"**Что нужно для результата:**\n{stack_lines}\n\n"
        f"Ориентир по бюджету Mission 1: {rec.price_hint}."
    )

    if rec.recommend == "service":
        path_block = (
            f"**Следующий логичный этап**, когда будете готовы оформить: "
            f"лендинг под ключ на /order ({rec.price_hint}).\n\n"
            f"**Virtus Studio** пока в разработке — подписку купить нельзя."
        )
    elif rec.recommend == "studio":
        path_block = studio_unavailable_message()
    else:
        path_block = (
            "**Когда дойдёте до оформления:** лендинг под ключ на /order (350 / 650 / 1200 €).\n\n"
            + studio_unavailable_message()
        )

    close = (
        "Беру задачу в эту сторону — уточним детали и двинемся к первому результату."
    )

    # Tie memory inferences if present
    memory_hook = ""
    if thinking.implicit_need and "семь" in thinking.implicit_need:
        memory_hook = "\n\nС учётом того, что Вам важно время с семьёй — смотрю на модели без 24/7.\n"
    elif state.life_goal == "family_time":
        memory_hook = "\n\nС учётом цели — больше времени с семьёй — lean-модели без круглосуточного присутствия.\n"

    return f"{open_line}{memory_hook}\n\n{stack_block}\n\n{path_block}\n\n{close}".strip()


def product_mind_llm_rules() -> str:
    return """[Product Mind — инструмент следующего шага]
- Определите, какой элемент стека (сайт, бот, CRM, документ) приближает к цели на этом этапе Journey.
- Один конкретный следующий шаг за ответ — не каталог и не продажа.
- Цены Mission 1: 350 / 650 / 1200 € на /order — только из фактов каталога, не выдумывать.
- Studio, интернет-магазин, приложение: недоступны для онлайн-оформления (факт каталога).
- Рекомендуй пакет и инструмент под цель человека — без апселла и без «перейдите в раздел»."""
