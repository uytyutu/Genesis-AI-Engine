"""Product Consultant — Vector as Virtus Core sales consultant (Mission 1 / G2.X).

Knows the live commercial catalog: websites, AI bots, website services.
Every product reply ends with Order CTA (not a link back to the homepage).
Does not rewrite Conversation Pipeline — early deterministic path before LLM.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from app.integration.genesis_brain.layers.conversation_state import ConversationState
from app.integration.genesis_brain.public_brand import ASSISTANT_NAME, BRAND_NAME
from app.integration.public_truth_catalog import MISSION1_LANDING_TIMELINE, min_landing_price_eur

_MIN = min_landing_price_eur()

INTENT_WEBSITE = "website"
INTENT_REPAIR = "repair"
INTENT_PRICING = "pricing"
INTENT_ABOUT = "about"
INTENT_CHATBOT = "chatbot"
INTENT_SEO = "seo"
INTENT_SUPPORT = "support"
INTENT_AUTOMATION = "automation"
INTENT_ORDER = "order"
INTENT_PAYMENT = "payment"
INTENT_TIMELINE = "timeline"
INTENT_ANALYSIS = "analysis"
INTENT_SPEED = "speed"
INTENT_SECURITY = "security"
INTENT_GBP = "google_business"
INTENT_MIGRATION = "migration"

_PACKAGE_LABELS = {
    "basic": ("Basic", 350, "готовый лендинг + ZIP + гайд публикации"),
    "business": ("Business", 650, "лендинг + помощь с публикацией + 1 правка"),
    "premium": ("Premium", 1200, "премиум-дизайн + assisted go-live + 14 дней поддержки"),
}

_BOT_LABELS = {
    "bot_starter": ("AI Bot Starter", 499, 99, "сайт-чат + Telegram, базовый объём"),
    "bot_business": ("AI Bot Business", 999, 199, "больше диалогов, база знаний, каналы"),
    "bot_professional": (
        "AI Bot Professional",
        1499,
        349,
        "приоритет, интеграции, расширенные лимиты",
    ),
}


@dataclass(frozen=True)
class ConsultantReply:
    answer: str
    cta_href: str | None = None
    cta_label: str | None = None


def try_product_consultant_reply(
    last_user: str,
    messages: list[dict[str, str]] | None,
    state: ConversationState,
) -> ConsultantReply | None:
    """Return a consultant-style reply when the turn is about Virtus Core products."""
    text = (last_user or "").strip()
    if not text:
        return None

    _absorb_turn(state, text)
    intent = state.consultant_intent
    if not intent and not _looks_like_product_turn(text):
        return None

    if _is_short_affirmation(text) and (intent or state.needs_website or state.package_choice):
        return _continue_active_goal(state)

    if intent == INTENT_WEBSITE or (state.needs_website and not intent):
        state.consultant_intent = INTENT_WEBSITE
        return _reply_website(state, text)
    if intent == INTENT_REPAIR:
        return _reply_repair(state)
    if intent == INTENT_ANALYSIS:
        return _reply_analysis()
    if intent == INTENT_PRICING:
        return _reply_pricing(state, text)
    if intent == INTENT_ABOUT:
        return _reply_about()
    if intent == INTENT_CHATBOT:
        return _reply_chatbot(state, text)
    if intent == INTENT_SEO:
        return _reply_seo()
    if intent == INTENT_SPEED:
        return _reply_addon(
            "Speed Optimization",
            199,
            "ускорение загрузки (изображения, кэш, критические правки)",
            "speed_optimization",
        )
    if intent == INTENT_SECURITY:
        return _reply_addon(
            "Security Check",
            299,
            "проверка HTTPS, форм и базовых уязвимостей с приоритетами",
            "security_check",
        )
    if intent == INTENT_GBP:
        return _reply_addon(
            "Google Business Profile Setup",
            149,
            "настройка карточки: категории, часы, фото, контакты",
            "google_business_setup",
        )
    if intent == INTENT_MIGRATION:
        return _reply_addon(
            "Website Migration",
            299,
            "перенос сайта на новый хостинг с проверкой после cutover",
            "website_migration",
            from_price=True,
        )
    if intent == INTENT_SUPPORT:
        return _reply_support()
    if intent == INTENT_AUTOMATION:
        return _reply_automation()
    if intent == INTENT_ORDER:
        return _reply_order(state)
    if intent == INTENT_PAYMENT:
        return _reply_payment()
    if intent == INTENT_TIMELINE:
        return _reply_timeline()

    detected = _detect_intent(text)
    if detected:
        state.consultant_intent = detected
        return try_product_consultant_reply(last_user, messages, state)
    return None


def _absorb_turn(state: ConversationState, text: str) -> None:
    low = text.lower().strip()

    detected = _detect_intent(low)
    if detected:
        if state.consultant_intent == INTENT_WEBSITE and detected in (
            INTENT_ABOUT,
            INTENT_TIMELINE,
            INTENT_PAYMENT,
        ):
            pass
        else:
            state.consultant_intent = detected

    if re.search(
        r"хочу\s+сайт|нужен\s+сайт|нужна\s+сайт|сделать\s+сайт|создать\s+сайт|"
        r"сайт\s+для|landing|website|webseite|хачу\s+сайт",
        low,
    ):
        state.needs_website = True
        state.goal = state.goal or "website"
        state.consultant_intent = state.consultant_intent or INTENT_WEBSITE

    if state.consultant_intent == INTENT_CHATBOT:
        bot_pkg = _detect_bot_package(low)
        if bot_pkg:
            state.package_choice = bot_pkg
    else:
        pkg = _detect_package(
            low,
            sticky_website=bool(
                state.needs_website or state.consultant_intent == INTENT_WEBSITE
            ),
        )
        if pkg:
            state.package_choice = pkg

    niche = _detect_niche(low)
    if niche:
        state.consultant_niche = niche
        if niche in ("dental", "clinic", "salon") and not state.package_choice:
            if state.consultant_intent != INTENT_CHATBOT:
                state.package_choice = state.package_choice or "business"


def _detect_intent(low: str) -> str | None:
    # Product-specific first (so «как заказать AI Bot» → chatbot, not generic order)
    if re.search(
        r"ai\s*bot|ai[- ]?бот|чат[- ]?бот|chatbot|telegram[- ]?бот|"
        r"бот\s+для|купить\s+бот|заказать\s+бот|website\s+chat|"
        r"телеграм\w*\s+бот",
        low,
    ):
        return INTENT_CHATBOT
    if re.search(
        r"ремонт\w*\s+сайт|починить\s+сайт|отремонтир|редизайн|"
        r"модерниз\w*\s+сайт|website\s+repair|что\s+такое\s+website\s+repair|"
        r"что\s+такое\s+ремонт",
        low,
    ):
        return INTENT_REPAIR
    if re.search(
        r"анализ\w*\s+сайт|проверить\s+сайт|разбор\s+сайт|site\s+audit|"
        r"website\s+analysis|ai\s+website\s+analysis",
        low,
    ):
        return INTENT_ANALYSIS
    if re.search(r"\bseo\b|поисков\w+\s+оптимиз|продвижен\w+\s+сайт|seo\s+audit", low):
        return INTENT_SEO
    if re.search(r"speed\s+opt|ускорен\w+\s+сайт|скорост\w+\s+сайт|оптимизац\w+\s+скорост", low):
        return INTENT_SPEED
    if re.search(r"security\s+check|безопасност\w+\s+сайт|проверк\w+\s+безопасн", low):
        return INTENT_SECURITY
    if re.search(r"google\s+business|гугл\s+бизнес|google\s+профиль", low):
        return INTENT_GBP
    if re.search(r"миграц\w+\s+сайт|website\s+migration|перенос\s+сайт", low):
        return INTENT_MIGRATION
    if re.search(
        r"сколько\s+стоит|какая\s+цена|прайс|pricing|preis|стоимость|"
        r"пакет\w*\s*(basic|business|premium|starter|professional)?|"
        r"чем\s+отличается|что\s+входит\s+в",
        low,
    ):
        return INTENT_PRICING
    if re.search(
        r"что\s+такое\s+(virtus|genesis)|чем\s+занимается\s+virtus|"
        r"who\s+are\s+you|what\s+is\s+virtus|was\s+ist\s+virtus|"
        r"расскажи\s+о\s+(компании|virtus|себе)",
        low,
    ):
        return INTENT_ABOUT
    if re.search(r"поддержк\w+|support|обслуживан\w+\s+сайт", low):
        return INTENT_SUPPORT
    if re.search(r"автоматизац|automation|crm\b|интеграц", low) and not re.search(
        r"хочу\s+сайт", low
    ):
        return INTENT_AUTOMATION
    if re.search(r"как\s+заказать|оформить\s+заказ|хочу\s+заказать", low):
        return INTENT_ORDER
    if re.search(r"как\s+оплат|оплата|payment|stripe|после\s+оплат", low):
        return INTENT_PAYMENT
    if re.search(r"когда\s+будет\s+готов|срок|сколько\s+времени|how\s+long|timeline", low):
        return INTENT_TIMELINE
    if re.search(
        r"хочу\s+сайт|нужен\s+сайт|нужна\s+сайт|сделать\s+сайт|создать\s+сайт|"
        r"сайт\s+для|landing\s+page|website|webseite",
        low,
    ):
        return INTENT_WEBSITE
    return None


def _detect_package(low: str, *, sticky_website: bool) -> str | None:
    if re.search(r"\bpremium\b|премиум", low):
        return "premium"
    if re.search(r"\bbasic\b|базов|одностранич|landing\s*basic", low):
        return "basic"
    if re.search(r"\bbusiness\b|landing\s*business", low):
        return "business"
    if sticky_website and re.fullmatch(r"бизнес\.?", low.strip()):
        return "business"
    return None


def _detect_bot_package(low: str) -> str | None:
    if re.search(r"professional|про\b|профи|enterprise", low):
        return "bot_professional"
    if re.search(r"\bstarter\b|старт", low):
        return "bot_starter"
    if re.search(r"\bbusiness\b|бизнес", low):
        return "bot_business"
    return None


def _detect_niche(low: str) -> str | None:
    if re.search(r"стоматолог|dental|Zahnarzt", low):
        return "dental"
    if re.search(r"клиник|clinic", low):
        return "clinic"
    if re.search(r"салон|красот|барбер", low):
        return "salon"
    if re.search(r"кофейн|кафе|ресторан", low):
        return "cafe"
    if re.search(r"автомойк|автосервис", low):
        return "autoservice"
    return None


def _looks_like_product_turn(text: str) -> bool:
    low = text.lower()
    return bool(
        _detect_intent(low)
        or _detect_package(low, sticky_website=False)
        or _detect_bot_package(low)
        or re.search(
            r"virtus|genesis|сайт|лендинг|/order|/analyze|пакет|basic|business|premium|"
            r"бот|seo|repair|security|migration",
            low,
        )
    )


def _is_short_affirmation(text: str) -> bool:
    low = text.lower().strip()
    return bool(
        re.fullmatch(
            r"(да|ок|хорошо|согласен|согласна|ладно|yes|ok|okay|давай|конечно|верно)\.?",
            low,
        )
    )


def _continue_active_goal(state: ConversationState) -> ConsultantReply:
    if state.consultant_intent == INTENT_CHATBOT:
        return _reply_chatbot(state, "да")
    if state.package_choice and str(state.package_choice).startswith("bot_"):
        return _reply_chatbot(state, "")
    if state.package_choice:
        return _reply_order(state)
    if state.consultant_intent == INTENT_REPAIR:
        return _reply_repair(state)
    if state.needs_website or state.consultant_intent == INTENT_WEBSITE:
        return _reply_website(state, "")
    return _reply_about()


def _packages_block() -> str:
    return (
        f"• **Basic** — {_PACKAGE_LABELS['basic'][2]} · **{_PACKAGE_LABELS['basic'][1]} €**\n"
        f"• **Business** — {_PACKAGE_LABELS['business'][2]} · **{_PACKAGE_LABELS['business'][1]} €**\n"
        f"• **Premium** — {_PACKAGE_LABELS['premium'][2]} · **{_PACKAGE_LABELS['premium'][1]} €**"
    )


def _bots_block() -> str:
    lines = []
    for _pid, (name, setup, monthly, desc) in _BOT_LABELS.items():
        lines.append(f"• **{name}** — **{setup} €** setup + **{monthly} €**/мес — {desc}")
    return "\n".join(lines)


def _bot_order_href(package_id: str | None = None) -> str:
    if package_id and package_id in _BOT_LABELS:
        return (
            f"/order?purchase_type=subscription&intent=bot"
            f"&package={package_id}"
        )
    return "/site?service=bots"


def _reply_website(state: ConversationState, text: str) -> ConsultantReply:
    niche = state.consultant_niche
    pkg = state.package_choice
    if pkg and str(pkg).startswith("bot_"):
        pkg = None

    if pkg and pkg in _PACKAGE_LABELS:
        label, price, desc = _PACKAGE_LABELS[pkg]
        niche_note = ""
        if niche == "dental":
            niche_note = " Для стоматологии чаще всего как раз Business.\n\n"
        elif niche:
            niche_note = f" Учту нишу ({niche}).\n\n"
        return ConsultantReply(
            answer=(
                f"Отлично — пакет **{label}** ({desc}, **{price} €**)."
                f"{niche_note}"
                "Следующий шаг — оформить заказ. В форме укажете компанию и контакты."
            ),
            cta_href=f"/order?package={pkg}",
            cta_label="Оформить заказ",
        )

    if niche == "dental":
        return ConsultantReply(
            answer=(
                "Для стоматологии чаще всего подходит **Business** — услуги, запись, контакты.\n\n"
                "Можете сразу оформить заказ — или скажите Basic / Premium."
            ),
            cta_href="/order?package=business",
            cta_label="Оформить заказ",
        )

    return ConsultantReply(
        answer=(
            f"Отлично! В {BRAND_NAME} сайты в трёх пакетах:\n\n"
            f"{_packages_block()}\n\n"
            "Скажите Basic / Business / Premium — или оформите заказ. "
            f"Срок ориентир: **{MISSION1_LANDING_TIMELINE}**."
        ),
        cta_href="/order",
        cta_label="Оформить заказ",
    )


def _reply_repair(state: ConversationState) -> ConsultantReply:
    return ConsultantReply(
        answer=(
            "**Website Repair** — ремонт существующего сайта **без покупки нового лендинга**.\n\n"
            "• от **199 €** (Lite) · Standard 349 € · Complete 499 €\n"
            "• объём согласуем по отчёту анализа\n"
            "• работу выполняет команда Virtus Core, статус — в кабинете\n\n"
            "Можно сразу оформить ремонт или сначала бесплатно/платно проанализировать сайт."
        ),
        cta_href="/order?package=website_repair",
        cta_label="Оформить заказ",
    )


def _reply_analysis() -> ConsultantReply:
    return ConsultantReply(
        answer=(
            "**AI Website Analysis** — **149 €**: отчёт по безопасности, мобильной версии, "
            "скорости и приоритетам улучшений. Рекомендуем ремонт или новый сайт.\n\n"
            "Услуга продаётся отдельно — сайт покупать не обязательно."
        ),
        cta_href="/order?package=ai_website_analysis",
        cta_label="Оформить заказ",
    )


def _reply_pricing(state: ConversationState, text: str) -> ConsultantReply:
    low = text.lower()
    if state.consultant_intent == INTENT_CHATBOT or re.search(r"бот|bot", low):
        state.consultant_intent = INTENT_CHATBOT
        return _reply_chatbot(state, text)

    pkg = state.package_choice or _detect_package(low, sticky_website=True)
    if pkg and pkg in _PACKAGE_LABELS:
        label, price, desc = _PACKAGE_LABELS[pkg]
        return ConsultantReply(
            answer=(
                f"**{label}** — **{price} €**: {desc}.\n\n"
                f"**Basic** vs **Business**: Business добавляет помощь с публикацией, Maps/FAQ и 1 правку.\n"
                f"**Premium**: exclusive design + assisted go-live + 14 дней поддержки.\n\n"
                "Можно оформить этот пакет сейчас."
            ),
            cta_href=f"/order?package={pkg}",
            cta_label="Оформить заказ",
        )

    if re.search(r"что\s+входит|чем\s+отличается|professional|premium|business", low):
        return ConsultantReply(
            answer=(
                f"Пакеты сайта {BRAND_NAME}:\n\n"
                f"{_packages_block()}\n\n"
                "**Business** — лучший старт для большинства компаний.\n"
                "**Premium** — если нужен сильный визуал и помощь с публикацией.\n"
                "(Тариф **Professional** относится к **AI Bot**, не к сайту.)"
            ),
            cta_href="/order?package=business",
            cta_label="Оформить заказ",
        )

    return ConsultantReply(
        answer=(
            f"Стоимость зависит от услуги. **Сайт Basic** — от **{_MIN} €**.\n\n"
            f"{_packages_block()}\n\n"
            f"**AI Bot** (отдельно):\n{_bots_block()}\n\n"
            "SEO Audit 249 € · Speed 199 € · Security 299 € · Repair от 199 € · "
            "Analysis 149 € · Google Business 149 € · Migration от 299 €.\n\n"
            "Скажите продукт — проведу до заказа."
        ),
        cta_href="/products",
        cta_label="Смотреть каталог",
    )


def _reply_about() -> ConsultantReply:
    return ConsultantReply(
        answer=(
            f"**{BRAND_NAME}** — цифровая компания: сайты, AI-боты, анализ и ремонт сайтов, "
            "SEO, скорость, безопасность, Google Business, миграция.\n\n"
            f"Я **{ASSISTANT_NAME}** — консультант: помогаю выбрать услугу и оформить заказ "
            "без возврата на главную «искать самому».\n\n"
            "Что нужно: сайт, AI Bot, ремонт, SEO или другое?"
        ),
        cta_href="/products",
        cta_label="Каталог услуг",
    )


def _reply_chatbot(state: ConversationState, text: str) -> ConsultantReply:
    low = (text or "").lower()
    pkg = state.package_choice if str(state.package_choice or "").startswith("bot_") else None
    pkg = pkg or _detect_bot_package(low)

    if pkg and pkg in _BOT_LABELS:
        name, setup, monthly, desc = _BOT_LABELS[pkg]
        state.package_choice = pkg
        return ConsultantReply(
            answer=(
                f"Отлично — **{name}**: **{setup} €** настройка + **{monthly} €**/мес.\n"
                f"{desc}.\n\n"
                "Каналы сейчас: **Website chat** и **Telegram**. "
                "WhatsApp и Instagram — в разработке (не продаём как готовые).\n\n"
                "Нажмите «Оформить заказ»: укажете компанию, сайт и задачи бота — "
                "настроим под ваш бизнес."
            ),
            cta_href=_bot_order_href(pkg),
            cta_label="Оформить заказ",
        )

    if re.search(
        r"какой\s+(бот|пакет|тариф)|что\s+выбрать|помоги\s+выбрать|не\s+знаю\s+какой",
        low,
    ):
        return ConsultantReply(
            answer=(
                "Подберём тариф. Ответьте коротко:\n\n"
                "1. Есть ли сайт?\n"
                "2. Какие каналы нужны: Telegram / Website Chat? "
                "(WhatsApp и Instagram пока в разработке)\n"
                "3. Сколько примерно сотрудников отвечает клиентам?\n"
                "4. Нужно принимать заявки и лиды?\n"
                "5. Нужен ИИ-консультант 24/7?\n\n"
                "По ответам предложу Starter / Business / Professional."
            ),
            cta_href=_bot_order_href(),
            cta_label="Смотреть пакеты ботов",
        )

    # Light recommend from signals without full questionnaire
    if re.search(r"telegram|телеграм|website\s*chat|сайт.?чат|заявк|лид|24/?7", low):
        rec = "bot_business"
        if re.search(r"маленьк|один|стартап|простой", low):
            rec = "bot_starter"
        if re.search(r"команда|интеграц|много|enterprise|сеть", low):
            rec = "bot_professional"
        name, setup, monthly, desc = _BOT_LABELS[rec]
        state.package_choice = rec
        return ConsultantReply(
            answer=(
                f"По вашим задачам чаще всего подходит **{name}** "
                f"(**{setup} €** + **{monthly} €**/мес) — {desc}.\n\n"
                f"Все варианты:\n{_bots_block()}\n\n"
                "Можно оформить этот тариф или сказать Starter / Business / Professional."
            ),
            cta_href=_bot_order_href(rec),
            cta_label="Оформить заказ",
        )

    return ConsultantReply(
        answer=(
            f"Отлично. AI Bot в {BRAND_NAME} — **отдельный продукт** (не входит в сайт).\n\n"
            f"{_bots_block()}\n\n"
            "Каналы в продаже: Website chat + Telegram. "
            "WhatsApp / Instagram — Coming Soon.\n\n"
            "Для оформления нажмите «Оформить заказ» — откроется форма о компании, "
            "и мы настроим бота под ваш бизнес. "
            "Если не уверены в тарифе — спросите «какой бот мне выбрать?»."
        ),
        cta_href=_bot_order_href("bot_starter"),
        cta_label="Оформить заказ",
    )


def _reply_seo() -> ConsultantReply:
    return ConsultantReply(
        answer=(
            "**SEO Audit** — **249 €**, продаётся отдельно от сайта.\n\n"
            "Входит: технический SEO-чек, мета/заголовки/структура, план приоритетных правок "
            "для локального бизнеса.\n\n"
            "Можно заказать без покупки лендинга."
        ),
        cta_href="/order?package=seo_audit",
        cta_label="Оформить заказ",
    )


def _reply_addon(
    name: str,
    price: int,
    blurb: str,
    package_id: str,
    *,
    from_price: bool = False,
) -> ConsultantReply:
    price_s = f"от {price} €" if from_price else f"{price} €"
    return ConsultantReply(
        answer=(
            f"**{name}** — **{price_s}**. {blurb}.\n\n"
            "Услуга самостоятельная: сайт Virtus Core покупать не обязательно.\n"
            "Оформите заказ — укажете сайт и контакты."
        ),
        cta_href=f"/order?package={package_id}",
        cta_label="Оформить заказ",
    )


def _reply_support() -> ConsultantReply:
    return ConsultantReply(
        answer=(
            "Поддержка — через заказ и кабинет после оплаты.\n\n"
            "Сайт «ломается» → **Website Repair** или **Analysis**. "
            "Нужен новый → пакеты сайта. Нужен бот → AI Bot."
        ),
        cta_href="/products",
        cta_label="Каталог услуг",
    )


def _reply_automation() -> ConsultantReply:
    return ConsultantReply(
        answer=(
            "CRM и глубокая автоматизация как подписка — **ещё в разработке** "
            "(не продаём как готовый checkout).\n\n"
            "Сейчас онлайн: **сайт**, **AI Bot**, SEO, speed, security, repair, analysis, "
            "Google Business, migration.\n\n"
            "Часто начинают с сайта Business или AI Bot — что ближе вашей задаче?"
        ),
        cta_href="/products",
        cta_label="Каталог услуг",
    )


def _reply_order(state: ConversationState) -> ConsultantReply:
    if state.consultant_intent == INTENT_CHATBOT or str(state.package_choice or "").startswith(
        "bot_"
    ):
        return _reply_chatbot(state, "")
    if state.consultant_intent == INTENT_SEO:
        return _reply_seo()
    if state.consultant_intent == INTENT_REPAIR:
        return _reply_repair(state)
    if state.consultant_intent == INTENT_ANALYSIS:
        return _reply_analysis()

    pkg = state.package_choice if state.package_choice in _PACKAGE_LABELS else "business"
    label, price, _ = _PACKAGE_LABELS[pkg]
    return ConsultantReply(
        answer=(
            f"Оформление: пакет **{label}** · **{price} €**.\n\n"
            "Откройте форму заказа — укажете компанию и контакты. Я рядом в чате, если нужна помощь."
        ),
        cta_href=f"/order?package={pkg}",
        cta_label="Оформить заказ",
    )


def _reply_payment() -> ConsultantReply:
    return ConsultantReply(
        answer=(
            "Оплата — на странице заказа (безопасный checkout). "
            "После оплаты — подтверждение на email и статус в кабинете (если есть аккаунт).\n\n"
            "Аккаунт для покупки **не обязателен** — можно купить как гость."
        ),
        cta_href="/order",
        cta_label="Оформить заказ",
    )


def _reply_timeline() -> ConsultantReply:
    return ConsultantReply(
        answer=(
            f"Лендинг под ключ — ориентир **{MISSION1_LANDING_TIMELINE}** "
            "(зависит от пакета и материалов).\n\n"
            "Ремонт / SEO / анализ — срок согласуем после заказа. "
            "AI Bot: настройка после оплаты по анкете."
        ),
        cta_href="/order",
        cta_label="Оформить заказ",
    )


def consultant_state_snapshot(state: ConversationState) -> dict[str, Any]:
    intent = state.consultant_intent or ("website" if state.needs_website else None)
    pkg = state.package_choice
    if intent == INTENT_REPAIR:
        nxt = "оформить ремонт или анализ"
    elif intent == INTENT_CHATBOT and not (pkg and str(pkg).startswith("bot_")):
        nxt = "подобрать тариф бота"
    elif intent == INTENT_WEBSITE and not pkg:
        nxt = "помочь выбрать пакет"
    elif pkg:
        nxt = "оформить заказ"
    else:
        nxt = "уточнить задачу"
    return {
        "intent": intent,
        "package": pkg,
        "niche": state.consultant_niche,
        "next_step": nxt,
    }
