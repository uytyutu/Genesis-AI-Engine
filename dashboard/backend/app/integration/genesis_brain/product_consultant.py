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
INTENT_PRIVACY = "privacy"

_PACKAGE_LABELS = {
    "basic": ("Basic", 350, "готовый лендинг + ZIP + гайд публикации"),
    "business": ("Business", 650, "лендинг + помощь с публикацией + 1 правка"),
    "premium": ("Premium", 1200, "премиум-дизайн + assisted go-live + 14 дней поддержки"),
}

_BOT_LABELS = {
    "bot_starter": (
        "AI Bot Starter",
        499,
        99,
        "1 источник знаний · 1 язык · базовые сценарии · Website Chat + Telegram",
    ),
    "bot_business": (
        "AI Bot Business",
        999,
        199,
        "до 5 источников · до 3 языков · AI-анализ · расширенные сценарии",
    ),
    "bot_professional": (
        "AI Bot Professional",
        1499,
        349,
        "без лимита KB/языков · индивидуальные сценарии · приоритет поддержки",
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
    *,
    public_rails: bool = False,
) -> ConsultantReply | None:
    """Return a consultant-style reply when the turn is about Virtus Core products.

    public_rails=True (public /site chat): never fall through to slow LLM —
    always answer as consultant with form/support links only.
    """
    text = (last_user or "").strip()
    if not text:
        return None

    _absorb_turn(state, text)
    intent = state.consultant_intent
    if not intent and not _looks_like_product_turn(text) and not public_rails:
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
    if intent == INTENT_PRIVACY:
        return _reply_privacy()
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
        return try_product_consultant_reply(
            last_user, messages, state, public_rails=public_rails
        )
    if public_rails:
        return _reply_public_rails_default()
    return None


def _absorb_turn(state: ConversationState, text: str) -> None:
    low = text.lower().strip()

    detected = _detect_intent(low)
    if detected:
        sd = state.sales_discovery or {}
        discovery_active = (
            state.consultant_intent == INTENT_WEBSITE
            and bool(sd.get("step"))
            and sd.get("step") != "done"
        )
        # Mid sales-discovery: don't jump to SEO/pricing on answers like «Да, SEO»
        if discovery_active and detected not in (
            INTENT_WEBSITE,
            INTENT_ORDER,
            INTENT_PAYMENT,
            INTENT_TIMELINE,
        ):
            detected = None
        elif state.consultant_intent == INTENT_WEBSITE and detected in (
            INTENT_ABOUT,
            INTENT_TIMELINE,
            INTENT_PAYMENT,
        ):
            pass  # keep website sticky
        elif detected:
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
        r"расскажи\s+о\s+(компании|virtus|себе)|какие\s+услуг|что\s+вы\s+предлага",
        low,
    ):
        return INTENT_ABOUT
    if re.search(
        r"защит\w*\s+данн|персональн\w*\s+данн|privacy|datenschutz|gdpr|dsgvo|"
        r"не\s+переда|переда[её]те\s+\w*\s*данн|переда\w*.{0,24}данн|данн\w*.{0,24}переда|"
        r"кому\s+отда|конфиденц|шифрован|data\s+protection|do\s+you\s+share",
        low,
    ):
        return INTENT_PRIVACY
    if re.search(r"поддержк\w+|support|обслуживан\w+\s+сайт|контакт|связ\w+\s+с\s+вам", low):
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
    if state.package_choice and state.package_choice in _PACKAGE_LABELS:
        return _reply_order(state)
    if state.consultant_intent == INTENT_REPAIR:
        return _reply_repair(state)
    if state.needs_website or state.consultant_intent == INTENT_WEBSITE:
        return _reply_website(state, "да")
    return _reply_about()


def _sales_sd(state: ConversationState) -> dict[str, Any]:
    if state.sales_discovery is None:
        state.sales_discovery = {}
    return state.sales_discovery


_SALES_STEPS = (
    "niche",
    "has_site",
    "wants_bot",
    "wants_leads",
    "wants_blog",
    "wants_seo",
    "team",
)

_SALES_PROMPTS = {
    "niche": "1/7 Чем занимается ваша компания? (ниша или сфера)",
    "has_site": "2/7 Есть ли уже сайт? (да / нет / устаревший)",
    "wants_bot": "3/7 Нужен ли Telegram-бот или чат на сайте? (да / нет / позже)",
    "wants_leads": "4/7 Нужно ли принимать заявки с сайта? (да / нет)",
    "wants_blog": "5/7 Нужен ли блог или новости? (да / нет)",
    "wants_seo": "6/7 Планируете SEO / продвижение? (да / нет / позже)",
    "team": "7/7 Сколько примерно сотрудников отвечает клиентам? (1 / 2–5 / больше)",
}


def _parse_yes_no_later(text: str) -> str | None:
    low = text.lower().strip()
    if re.search(r"\b(нет|no|не\s+нуж|не\s+надо|без\s+эт|не\s+хочу)\b", low):
        return "no"
    if re.search(r"\b(позже|потом|пока\s+нет|maybe|perhaps)\b", low):
        return "later"
    if re.search(r"\b(да|yes|нуж|хочу|конечно|ага|угу|есть)\b", low):
        return "yes"
    if re.search(r"устарев|старый\s+сайт|ломается|плохо\s+работа", low):
        return "outdated"
    return None


def _parse_team(text: str) -> str | None:
    low = text.lower().strip()
    if re.search(r"\b(1|один|одна|я\s+сам|solo|единолич)\b", low):
        return "solo"
    if re.search(r"\b(2|3|4|5|двое|трое|небольш|small)\b", low):
        return "small"
    if re.search(r"\b(больше|много|команда|отдел|10|20|large)\b", low):
        return "large"
    return None


def _absorb_sales_answer(state: ConversationState, text: str) -> None:
    sd = _sales_sd(state)
    step = sd.get("step")
    if not step or step not in _SALES_STEPS:
        return
    low = text.lower().strip()

    if step == "niche":
        niche = _detect_niche(low) or state.consultant_niche
        if niche:
            state.consultant_niche = niche
            sd["niche"] = niche
        elif len(low) >= 2 and not _is_short_affirmation(text):
            sd["niche"] = text.strip()[:80]
            state.consultant_niche = state.consultant_niche or sd["niche"]
        else:
            return
        sd["step"] = "has_site"
        return

    if step == "has_site":
        yn = _parse_yes_no_later(low)
        if yn == "outdated":
            sd["has_site"] = "outdated"
        elif yn == "yes":
            sd["has_site"] = "yes"
        elif yn == "no":
            sd["has_site"] = "no"
        else:
            return
        sd["step"] = "wants_bot"
        return

    if step == "wants_bot":
        yn = _parse_yes_no_later(low)
        if not yn:
            return
        sd["wants_bot"] = yn
        sd["step"] = "wants_leads"
        return

    if step == "wants_leads":
        yn = _parse_yes_no_later(low)
        if not yn:
            return
        sd["wants_leads"] = "yes" if yn == "yes" else "no"
        sd["step"] = "wants_blog"
        return

    if step == "wants_blog":
        yn = _parse_yes_no_later(low)
        if not yn:
            return
        sd["wants_blog"] = "yes" if yn == "yes" else "no"
        sd["step"] = "wants_seo"
        return

    if step == "wants_seo":
        yn = _parse_yes_no_later(low)
        if not yn:
            return
        sd["wants_seo"] = yn
        sd["step"] = "team"
        return

    if step == "team":
        team = _parse_team(low)
        if not team:
            return
        sd["team"] = team
        sd["step"] = "done"


def _recommend_website_package(state: ConversationState) -> tuple[str, list[str]]:
    """Return package id + why bullets from discovery answers."""
    sd = _sales_sd(state)
    reasons: list[str] = []
    score = {"basic": 0, "business": 0, "premium": 0}

    score["business"] += 1  # default lean

    if sd.get("has_site") in ("yes", "outdated"):
        score["business"] += 1
        reasons.append("у вас уже есть сайт — нужен сильный новый каркас и помощь с публикацией")
    else:
        score["basic"] += 1
        reasons.append("сайт с нуля — можно стартовать с чистого лендинга")

    if sd.get("wants_leads") == "yes":
        score["business"] += 2
        reasons.append("нужны заявки с сайта — в Business это заложено лучше")
    if sd.get("wants_bot") == "yes":
        score["business"] += 1
        reasons.append("бот можно добавить отдельно; сайт Business удобная база под заявки")
    if sd.get("wants_blog") == "yes":
        score["premium"] += 2
        reasons.append("блог / расширенный контент — ближе к Premium")
    if sd.get("wants_seo") == "yes":
        score["business"] += 1
        reasons.append("SEO можно докупить отдельно; Business уже даёт крепкую SEO-основу")
    if sd.get("team") == "large":
        score["premium"] += 1
        reasons.append("больше команда — чаще нужен Premium-уровень подачи")
    if sd.get("team") == "solo":
        score["basic"] += 1
    if state.consultant_niche in ("dental", "clinic", "salon"):
        score["business"] += 2
        reasons.append(f"для ниши «{state.consultant_niche}» обычно выбирают Business")

    pkg = max(score, key=lambda k: score[k])
    if not reasons:
        reasons.append("сбалансированный вариант для большинства компаний")
    return pkg, reasons[:4]


def _reply_sales_recommend(state: ConversationState) -> ConsultantReply:
    pkg, reasons = _recommend_website_package(state)
    state.package_choice = pkg
    label, price, desc = _PACKAGE_LABELS[pkg]
    why = "\n".join(f"• {r}" for r in reasons)
    extras: list[str] = []
    sd = _sales_sd(state)
    if sd.get("wants_bot") == "yes":
        extras.append("AI Bot (Telegram / website chat) — отдельным заказом после сайта")
    if sd.get("wants_seo") in ("yes", "later"):
        extras.append("SEO Audit — можно добавить к проекту позже")
    extra_block = ""
    if extras:
        extra_block = "\n\nПозже можно расширить проект:\n" + "\n".join(
            f"• {e}" for e in extras
        )
    return ConsultantReply(
        answer=(
            f"Я рекомендую пакет **{label}** — **{price} €**.\n"
            f"{desc}.\n\n"
            f"Почему:\n{why}"
            f"{extra_block}\n\n"
            "Можно сразу открыть форму заказа — сначала данные, потом оплата."
        ),
        cta_href=f"/order?package={pkg}",
        cta_label="Оформить заказ",
    )


def _reply_sales_question(state: ConversationState) -> ConsultantReply:
    sd = _sales_sd(state)
    step = sd.get("step") or "niche"
    prompt = _SALES_PROMPTS.get(step, _SALES_PROMPTS["niche"])
    return ConsultantReply(
        answer=(
            "Отлично.\n\n"
            "Чтобы подобрать оптимальный вариант, ответьте на несколько вопросов.\n\n"
            f"**{prompt}**"
        )
        if step == "niche" and not sd.get("_intro_shown")
        else f"**{prompt}**"
    )


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
        return f"/order/bot?package={package_id}"
    return "/order/bot"


def _reply_website(state: ConversationState, text: str) -> ConsultantReply:
    low = (text or "").lower().strip()
    niche = state.consultant_niche
    pkg = state.package_choice
    if pkg and str(pkg).startswith("bot_"):
        pkg = None

    # Explicit package → skip discovery
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

    # Escape hatch: show all packages without discovery
    if re.search(
        r"покажи\s+пакет|все\s+пакет|сразу\s+заказ|без\s+вопрос|просто\s+цены",
        low,
    ):
        return ConsultantReply(
            answer=(
                f"Пакеты сайта {BRAND_NAME}:\n\n"
                f"{_packages_block()}\n\n"
                "Напишите Basic / Business / Premium — или оформите заказ."
            ),
            cta_href="/order",
            cta_label="Оформить заказ",
        )

    sd = _sales_sd(state)
    if not sd.get("step"):
        sd["step"] = "niche"
        sd["_intro_shown"] = True
        # If niche already known from first message (e.g. «сайт автосервиса»)
        if state.consultant_niche or _detect_niche(low):
            if not state.consultant_niche:
                state.consultant_niche = _detect_niche(low)
            sd["niche"] = state.consultant_niche
            sd["step"] = "has_site"
            return ConsultantReply(
                answer=(
                    f"Отлично — ниша: **{state.consultant_niche}**.\n\n"
                    "Чтобы подобрать оптимальный пакет, ещё несколько коротких вопросов.\n\n"
                    f"**{_SALES_PROMPTS['has_site']}**"
                )
            )
        return _reply_sales_question(state)

    if sd.get("step") != "done":
        before = sd.get("step")
        _absorb_sales_answer(state, text)
        after = sd.get("step")
        if before == after and after != "done":
            # Unparsed answer — re-ask same step
            return ConsultantReply(answer=f"**{_SALES_PROMPTS.get(after, _SALES_PROMPTS['niche'])}**")
        if sd.get("step") == "done":
            return _reply_sales_recommend(state)
        # Advance to next question
        nxt = sd.get("step")
        return ConsultantReply(answer=f"**{_SALES_PROMPTS.get(nxt, _SALES_PROMPTS['niche'])}**")

    return _reply_sales_recommend(state)


def _reply_repair(state: ConversationState) -> ConsultantReply:
    return ConsultantReply(
        answer=(
            "**Website Repair** — ремонт существующего сайта **без покупки нового лендинга**.\n\n"
            "• от **199 €** (Lite) · Standard 349 € · Complete 499 €\n"
            "• объём согласуем по отчёту анализа\n"
            "• работу выполняет команда Virtus Core, статус — в кабинете\n\n"
            "Можно сразу оформить ремонт или сначала бесплатно/платно проанализировать сайт."
        ),
        cta_href="/order/service/website_repair",
        cta_label="Оформить заказ",
    )


def _reply_analysis() -> ConsultantReply:
    return ConsultantReply(
        answer=(
            "**AI Website Analysis** — **149 €**: отчёт по безопасности, мобильной версии, "
            "скорости и приоритетам улучшений. Рекомендуем ремонт или новый сайт.\n\n"
            "Услуга продаётся отдельно — сайт покупать не обязательно."
        ),
        cta_href="/order/service/ai_website_analysis",
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
            f"Я **{ASSISTANT_NAME}** — консультант: объясняю продукты и даю ссылки на "
            "форму заказа или поддержку. Сам файлы, код и готовые сайты в чате не выдаю.\n\n"
            "Данные диалога и заказа **не передаём** третьим лицам.\n\n"
            "Что нужно: сайт, AI Bot, ремонт, SEO или другое?"
        ),
        cta_href="/products",
        cta_label="Каталог услуг",
    )


def _reply_privacy() -> ConsultantReply:
    return ConsultantReply(
        answer=(
            "**Защита данных:** сообщения в чате и данные заказа используются только "
            f"для консультации и выполнения услуги **{BRAND_NAME}**. "
            "Мы **не продаём** и **не передаём** персональные данные третьим лицам "
            "для рекламы или рассылок.\n\n"
            "Подробности — в Datenschutz. "
            "Чтобы заказать услугу — форма заказа; вопрос человеку — контакт."
        ),
        cta_href="/datenschutz",
        cta_label="Datenschutz",
    )


def _reply_public_rails_default() -> ConsultantReply:
    return ConsultantReply(
        answer=(
            f"Я **{ASSISTANT_NAME}**, консультант **{BRAND_NAME}** — отвечаю быстро: "
            "продукты, цены, защита данных. "
            "Готовые файлы и сайты в чате не выдаю — только ссылки на форму или поддержку.\n\n"
            "Напишите: «сайт», «AI Bot», «цены», «защита данных» — или откройте каталог."
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


_COMING_SOON_SERVICE_IDS = frozenset(
    {
        "seo_audit",
        "speed_optimization",
        "security_check",
        "google_business_setup",
        "website_migration",
    }
)


def _reply_seo() -> ConsultantReply:
    return ConsultantReply(
        answer=(
            "**SEO Audit** — **249 €**, отдельная услуга (сайт покупать не нужно).\n\n"
            "Сейчас онлайн-оплата ещё в подготовке. "
            "Откройте форму интереса — укажите сайт и цель, мы свяжемся, "
            "когда доставка будет готова. "
            "Уже можно заказать **AI Website Analysis** или **Website Repair**."
        ),
        cta_href="/order/service/seo_audit",
        cta_label="Открыть форму интереса",
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
    soon = package_id in _COMING_SOON_SERVICE_IDS
    if soon:
        return ConsultantReply(
            answer=(
                f"**{name}** — **{price_s}**. {blurb}.\n\n"
                "Онлайн-оплата пока в подготовке (Coming Soon). "
                "Откройте форму — укажите, что нужно, и мы вернёмся, когда услуга будет готова. "
                "Уже доступны: сайт, AI Bot, анализ сайта, ремонт сайта."
            ),
            cta_href=f"/order/service/{package_id}",
            cta_label="Открыть форму интереса",
        )
    return ConsultantReply(
        answer=(
            f"**{name}** — **{price_s}**. {blurb}.\n\n"
            "Услуга самостоятельная: сайт Virtus Core покупать не обязательно.\n"
            "Сначала форма заказа (что именно нужно) — потом безопасная оплата."
        ),
        cta_href=f"/order/service/{package_id}",
        cta_label="Открыть форму заказа",
    )


def _reply_support() -> ConsultantReply:
    return ConsultantReply(
        answer=(
            "Поддержка: откройте форму контакта — команда ответит.\n\n"
            "Сайт «ломается» → **Website Repair** или **Analysis**. "
            "Нужен новый → пакеты сайта. Нужен бот → AI Bot.\n\n"
            "Данные заявки не передаём третьим лицам."
        ),
        cta_href="/kontakt",
        cta_label="Связаться",
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
    sd = state.sales_discovery or {}
    if intent == INTENT_REPAIR:
        nxt = "оформить ремонт или анализ"
    elif intent == INTENT_CHATBOT and not (pkg and str(pkg).startswith("bot_")):
        nxt = "подобрать тариф бота"
    elif intent == INTENT_WEBSITE and sd.get("step") and sd.get("step") != "done" and not pkg:
        nxt = "sales discovery"
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
        "sales_step": sd.get("step"),
    }
