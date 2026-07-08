"""Multi-turn conversation logic — context-aware replies without re-introduction."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.integration.genesis_brain.public_brand import STUDIO_NAME
_COUNTRY_MAP = {
    "герман": "Германии",
    "germany": "Германии",
    "росси": "России",
    "украин": "Украине",
    "польш": "Польше",
    "казах": "Казахстане",
    "сша": "США",
    "америк": "США",
}


@dataclass
class BusinessContext:
    wants_business: bool = False
    country: str | None = None
    budget: str | None = None
    uncertain_niche: bool = False
    niche: str | None = None  # coffee, salon, etc.
    needs_website: bool = False
    needs_app: bool = False
    needs_marketing: bool = False
    wants_studio: bool = False
    user_name: str | None = None

    @classmethod
    def from_messages(cls, messages: list[dict[str, str]]) -> BusinessContext:
        ctx = cls()
        for m in messages:
            if m.get("role") != "user":
                continue
            text = (m.get("content") or "").strip()
            low = text.lower()
            cls._apply(ctx, low, text)
        return ctx

    @staticmethod
    def _apply(ctx: BusinessContext, low: str, raw: str) -> None:
        if re.search(r"открыть бизнес|начать бизнес|хочу бизнес|открыть бизнес", low):
            ctx.wants_business = True
        if re.search(r"не знаю какой|не знаю, какой|какой бизнес", low):
            ctx.uncertain_niche = True
        for key, country in _COUNTRY_MAP.items():
            if key in low:
                ctx.country = country
        bm = _BUDGET_RE.search(raw)
        if bm:
            val = next(g for g in bm.groups() if g)
            ctx.budget = val.replace(" ", "").replace(",", "")
        if any(w in low for w in ("кофейн", "кофе", "кафе")):
            ctx.niche = "coffee"
            ctx.wants_business = True
        if any(w in low for w in ("салон", "красот", "барбер")):
            ctx.niche = "salon"
        if re.search(r"нужен сайт|хочу сайт|сайт для", low):
            ctx.needs_website = True
        if "приложен" in low or "app" in low:
            ctx.needs_app = True
        if any(w in low for w in ("продвижен", "реклам", "маркетинг")):
            ctx.needs_marketing = True
        if "studio" in low:
            ctx.wants_studio = True
        nm = re.search(r"меня\s+зовут\s+([A-Za-zА-Яа-яЁё\-]+)", raw, re.I)
        if nm:
            ctx.user_name = nm.group(1).strip()


def business_reply(ctx: BusinessContext, last_user: str) -> str | None:
    """Context-first business consultant — never re-introduces Genesis."""
    low = last_user.lower()

    if ctx.wants_studio or ("studio" in low and "хочу" in low):
        return (
            f"{STUDIO_NAME} — платформа, где можно сами создавать сайты, приложения и автоматизации.\n\n"
            "**Free** — попробовать · **Basic 49 €** · **Pro 99 €** · **Business 199 €** (команда, AI COO).\n\n"
            "Хотите начать с бесплатного тарифа или сразу подключить Pro для серьёзной работы?"
        )

    if ctx.needs_marketing or any(w in low for w in ("продвижен", "реклам")):
        return (
            "Для продвижения кофейни или локального бизнеса обычно работают:\n"
            "• Google Maps и отзывы\n"
            "• Instagram с фото процесса\n"
            "• простой лендинг с меню и записью\n\n"
            "Могу набросать план на первые 2 недели — с чего начнём?"
        )

    if ctx.needs_app:
        return (
            "Приложение для кофейни имеет смысл, когда есть постоянные клиенты и программа лояльности.\n\n"
            "На старте часто достаточно сайта + Telegram-бота для заказов — дешевле и быстрее.\n\n"
            "Приложение нужно сразу или сначала проверим спрос через сайт?"
        )

    if ctx.needs_website and ctx.niche == "coffee":
        where = f" в {ctx.country}" if ctx.country else ""
        return (
            f"Отлично — сайт для кофейни{where}.\n\n"
            "Рекомендую: главная · меню · онлайн-заказ или запись · галерея · отзывы · контакты с картой.\n\n"
            "Ориентир под ключ — **650–850 €**. Можем собрать превью до публикации.\n\n"
            "Кофейня уже работает или только открывается?"
        )

    if ctx.niche == "coffee" and ctx.country and ctx.budget:
        return (
            f"Кофейня в {ctx.country} с бюджетом около **{ctx.budget} €** — реалистичный старт.\n\n"
            "На эти деньги обычно хватает: небольшое помещение в спальном районе или формат «кофе с собой», "
            "базовое оборудование и первый месяц расходников.\n\n"
            "Следующий шаг — сайт и карта в Google, чтобы первые клиенты вас нашли. Начнём с сайта?"
        )

    if ctx.uncertain_niche or ("не знаю" in low and ctx.wants_business):
        where = f" в {ctx.country}" if ctx.country else ""
        budget_note = f" При бюджете **{ctx.budget} €**" if ctx.budget else ""
        return (
            f"Понял — будем искать нишу вместе{where}.{budget_note}\n\n"
            "Три направления, которые часто хорошо заходят:\n"
            "• локальный сервис с онлайн-записью (салон, ремонт)\n"
            "• кофейня или небольшое кафе\n"
            "• онлайн-услуга (обучение, консультации, digital)\n\n"
            "Что Вам ближе по духу — работа с людьми лично или больше онлайн?"
        )

    if re.search(r"я из|из герман|из росс", low) or (
        ctx.country and any(k in low for k in ("герман", "росси", "украин", "польш"))
    ):
        return (
            f"Отлично, {ctx.country} — важная деталь для налогов, аренды и конкуренции.\n\n"
            "Какой примерно бюджет готовы вложить на старте?"
        )

    if _BUDGET_RE.search(last_user) and not ctx.niche:
        return (
            f"Бюджет **{ctx.budget} €** — хорошая отправная точка.\n\n"
            "Есть уже идея, чем заниматься, или подберём нишу вместе?"
        )

    if re.search(r"открыть бизнес|начать бизнес|хочу бизнес|открыть бизнес", low):
        return (
            "Отличная идея. Давайте вместе подберём бизнес, который реально сможет приносить прибыль.\n\n"
            "Задам всего несколько вопросов, чтобы не гадать:\n\n"
            "**1.** В какой стране планируете открываться?\n\n"
            "**2.** Какой бюджет готовы вложить?\n\n"
            "**3.** Хотите сами управлять каждый день или максимально автоматизировать?"
        )

    return None
