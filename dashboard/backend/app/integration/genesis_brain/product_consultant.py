"""Product Consultant v1 — Vector as Virtus Core sales manager (Mission 1).

Rule: every reply ends with one useful next action.
Sticky dialog goal: once Intent is set, do not re-ask the same step.
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

# Intent ids — stored on ConversationState.consultant_intent
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

_PACKAGE_LABELS = {
    "basic": ("Basic", 350, "одностраничный сайт"),
    "business": ("Business", 650, "сайт компании с системой управления"),
    "premium": ("Premium", 1200, "расширенный сайт: блог, бронирование и CRM"),
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
    """Return a manager-style reply when the turn is about Virtus Core products."""
    text = (last_user or "").strip()
    if not text:
        return None

    _absorb_turn(state, text)
    intent = state.consultant_intent
    if not intent and not _looks_like_product_turn(text):
        return None

    # Affirmations while an active commercial goal exists → advance, don't restart
    if _is_short_affirmation(text) and (intent or state.needs_website or state.package_choice):
        return _continue_active_goal(state)

    if intent == INTENT_WEBSITE or (state.needs_website and not intent):
        state.consultant_intent = INTENT_WEBSITE
        return _reply_website(state, text)
    if intent == INTENT_REPAIR:
        return _reply_repair(state)
    if intent == INTENT_PRICING:
        return _reply_pricing(state, text)
    if intent == INTENT_ABOUT:
        return _reply_about()
    if intent == INTENT_CHATBOT:
        return _reply_chatbot()
    if intent == INTENT_SEO:
        return _reply_seo()
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

    # Fresh product turn without sticky intent yet
    detected = _detect_intent(text)
    if detected:
        state.consultant_intent = detected
        return try_product_consultant_reply(last_user, messages, state)
    return None


def _absorb_turn(state: ConversationState, text: str) -> None:
    low = text.lower().strip()

    detected = _detect_intent(low)
    if detected:
        # Sticky: do not downgrade website → about on side questions; allow repair/pricing switches
        if state.consultant_intent == INTENT_WEBSITE and detected in (
            INTENT_ABOUT,
            INTENT_TIMELINE,
            INTENT_PAYMENT,
        ):
            pass  # keep website; side FAQs handled only when primary intent unset
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

    pkg = _detect_package(low, sticky_website=bool(state.needs_website or state.consultant_intent == INTENT_WEBSITE))
    if pkg:
        state.package_choice = pkg

    niche = _detect_niche(low)
    if niche:
        state.consultant_niche = niche
        if niche in ("dental", "clinic", "salon") and not state.package_choice:
            state.package_choice = state.package_choice or "business"


def _detect_intent(low: str) -> str | None:
    if re.search(
        r"ремонт\w*\s+сайт|починить\s+сайт|отремонтир|редизайн|"
        r"модерниз\w*\s+сайт|улучшить\s+сайт|анализ\w*\s+сайт|"
        r"проверить\s+сайт|разбор\s+сайт|site\s+audit|website\s+repair",
        low,
    ):
        return INTENT_REPAIR
    if re.search(
        r"сколько\s+стоит|какая\s+цена|прайс|pricing|preis|стоимость|"
        r"пакет\w*\s*(basic|business|premium)?|цены\s+на\s+сайт",
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
    if re.search(r"чат[- ]?бот|chatbot|telegram[- ]?бот|бот\s+для", low):
        return INTENT_CHATBOT
    if re.search(r"\bseo\b|поисков\w+\s+оптимиз|продвижен\w+\s+сайт", low):
        return INTENT_SEO
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
    # Bare «бизнес» after website intent = Business package (not open_business questionnaire)
    if sticky_website and re.fullmatch(r"бизнес\.?", low.strip()):
        return "business"
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
        or re.search(
            r"virtus|genesis|сайт|лендинг|/order|/analyze|пакет|basic|business|premium",
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
    if state.package_choice:
        return _reply_order(state)
    if state.consultant_intent == INTENT_REPAIR:
        return _reply_repair(state)
    if state.needs_website or state.consultant_intent == INTENT_WEBSITE:
        return _reply_website(state, "")
    return _reply_about()


def _packages_block() -> str:
    return (
        f"* **Basic** — {_PACKAGE_LABELS['basic'][2]} · **{_PACKAGE_LABELS['basic'][1]} €**\n"
        f"* **Business** — {_PACKAGE_LABELS['business'][2]} · **{_PACKAGE_LABELS['business'][1]} €**\n"
        f"* **Premium** — {_PACKAGE_LABELS['premium'][2]} · **{_PACKAGE_LABELS['premium'][1]} €**"
    )


def _reply_website(state: ConversationState, text: str) -> ConsultantReply:
    niche = state.consultant_niche
    pkg = state.package_choice

    if pkg:
        label, price, desc = _PACKAGE_LABELS[pkg]
        niche_note = ""
        if niche == "dental":
            niche_note = " Для стоматологии чаще всего как раз Business — услуги, запись, контакты.\n\n"
        elif niche:
            niche_note = f" Учту нишу ({niche}).\n\n"
        return ConsultantReply(
            answer=(
                f"Отлично — пакет **{label}** ({desc}, **{price} €**)."
                f"{niche_note}"
                "Следующий шаг — оформить заказ. В форме помогу с каждым пунктом, если что-то непонятно."
            ),
            cta_href=f"/order?package={pkg}",
            cta_label="Оформить заказ",
        )

    if niche == "dental":
        return ConsultantReply(
            answer=(
                "Для стоматологии чаще всего подходит **Business** — сайт компании с услугами "
                "и удобной записью.\n\n"
                "Если хотите, можете сразу оформить заказ — а я помогу с каждым пунктом формы. "
                "Или скажите Basic / Premium, если нужен другой уровень."
            ),
            cta_href="/order?package=business",
            cta_label="Оформить Business",
        )

    if niche == "cafe":
        return ConsultantReply(
            answer=(
                "Для кафе обычно хватает **Basic** или **Business** — меню, контакты, заявка.\n\n"
                f"{_packages_block()}\n\n"
                "Напишите пакет или оформите заказ — помогу на каждом шаге."
            ),
            cta_href="/order?package=business",
            cta_label="К заказу",
        )

    # First website turn — offer packages, no questionnaire
    return ConsultantReply(
        answer=(
            f"Отлично! В {BRAND_NAME} мы создаём сайты в трёх пакетах:\n\n"
            f"{_packages_block()}\n\n"
            "Если уже знаете, какой нужен — оформите заказ. "
            "Если нет — расскажите нишу (например, стоматология), и я помогу выбрать. "
            "Срок ориентир: "
            f"**{MISSION1_LANDING_TIMELINE}**."
        ),
        cta_href="/order",
        cta_label="Оформить заказ",
    )


def _reply_repair(state: ConversationState) -> ConsultantReply:
    return ConsultantReply(
        answer=(
            "Сначала проведём **анализ сайта**.\n\n"
            "Введите адрес вашего сайта в форму анализа. "
            "После проверки покажем найденные проблемы и предложим подходящий вариант — "
            "ремонт, улучшение или полный редизайн."
        ),
        cta_href="/site?analyze=1",
        cta_label="Открыть анализ сайта",
    )


def _reply_pricing(state: ConversationState, text: str) -> ConsultantReply:
    pkg = state.package_choice or _detect_package(text.lower(), sticky_website=True)
    if pkg:
        label, price, desc = _PACKAGE_LABELS[pkg]
        return ConsultantReply(
            answer=(
                f"**{label}** — **{price} €**: {desc}.\n\n"
                "Цена зависит от пакета и страны (локальная валюта на странице заказа). "
                "Следующий шаг — оформить этот пакет или сравнить все три на /order."
            ),
            cta_href=f"/order?package={pkg}",
            cta_label=f"Заказать {label}",
        )
    return ConsultantReply(
        answer=(
            f"Стоимость зависит от пакета и страны. **Basic** начинается от **{_MIN} €**.\n\n"
            f"{_packages_block()}\n\n"
            "Если расскажете, какой сайт нужен (ниша или задача), помогу подобрать вариант."
        ),
        cta_href="/order",
        cta_label="Смотреть пакеты",
    )


def _reply_about() -> ConsultantReply:
    return ConsultantReply(
        answer=(
            f"**{BRAND_NAME}** — платформа цифровых услуг: создание сайтов, "
            "модернизация существующих сайтов, автоматизация и AI-решения для бизнеса.\n\n"
            f"Я {ASSISTANT_NAME} — цифровой менеджер: помогаю выбрать услугу и довести до заказа.\n\n"
            "Следующий шаг — скажите, что нужно: новый сайт, анализ/ремонт или автоматизация."
        ),
        cta_href="/order",
        cta_label="К услугам",
    )


def _reply_chatbot() -> ConsultantReply:
    return ConsultantReply(
        answer=(
            "Чат-бот под ключ **пока нельзя оформить онлайн**.\n\n"
            "Сейчас доступен заказ **сайта** (Basic / Business / Premium). "
            "На Business и Premium часто закладывают заявки и будущую автоматизацию.\n\n"
            "Следующий шаг — сайт сейчас или описание задачи для будущей автоматизации."
        ),
        cta_href="/order?package=business",
        cta_label="Сайт Business",
    )


def _reply_seo() -> ConsultantReply:
    return ConsultantReply(
        answer=(
            "SEO как отдельную услугу онлайн пока не оформляем. "
            "В пакетах сайта уже есть базовая SEO-основа (структура, мета, адаптив).\n\n"
            "Следующий шаг — заказать сайт или отправить текущий сайт на **анализ**, "
            "чтобы увидеть пробелы."
        ),
        cta_href="/site?analyze=1",
        cta_label="Анализ сайта",
    )


def _reply_support() -> ConsultantReply:
    return ConsultantReply(
        answer=(
            "Поддержка и сопровождение — через заказ и кабинет клиента после оплаты.\n\n"
            "Если сайт уже есть и «ломается» — начните с **анализа**. "
            "Если нужен новый — выберите пакет и оформите заказ."
        ),
        cta_href="/site?analyze=1",
        cta_label="Анализ или заказ",
    )


def _reply_automation() -> ConsultantReply:
    return ConsultantReply(
        answer=(
            "Автоматизация и AI для бизнеса — часть направления Virtus Core. "
            "Онлайн сейчас стабильно оформляется **сайт под ключ**; "
            "боты и глубокая автоматизация — по запросу после сайта.\n\n"
            "Следующий шаг — описать процесс, который хотите упростить, "
            "или начать с сайта Business/Premium как базы."
        ),
        cta_href="/order?package=business",
        cta_label="Начать с сайта",
    )


def _reply_order(state: ConversationState) -> ConsultantReply:
    pkg = state.package_choice or "business"
    label, price, _ = _PACKAGE_LABELS.get(pkg, _PACKAGE_LABELS["business"])
    return ConsultantReply(
        answer=(
            f"Оформление: пакет **{label}** · **{price} €**.\n\n"
            "Откройте форму заказа — я рядом в чате, если на каком-то пункте нужна помощь."
        ),
        cta_href=f"/order?package={pkg}",
        cta_label="Оформить заказ",
    )


def _reply_payment() -> ConsultantReply:
    return ConsultantReply(
        answer=(
            "Оплата проходит на странице заказа (картой через безопасный checkout). "
            "После оплаты проект фиксируется, и вы получаете подтверждение на email.\n\n"
            "Следующий шаг — выбрать пакет и перейти к оплате в форме заказа."
        ),
        cta_href="/order",
        cta_label="К оформлению",
    )


def _reply_timeline() -> ConsultantReply:
    return ConsultantReply(
        answer=(
            f"Ориентир по сроку для лендинга под ключ — **{MISSION1_LANDING_TIMELINE}** "
            "(зависит от пакета и готовности материалов).\n\n"
            "Следующий шаг — выбрать пакет и оформить заказ, чтобы зафиксировать старт."
        ),
        cta_href="/order",
        cta_label="Выбрать пакет",
    )


def consultant_state_snapshot(state: ConversationState) -> dict[str, Any]:
    """Debug / UI hint — Intent · Package · Next step."""
    intent = state.consultant_intent or ("website" if state.needs_website else None)
    pkg = state.package_choice
    if intent == INTENT_REPAIR:
        nxt = "открыть форму анализа"
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
