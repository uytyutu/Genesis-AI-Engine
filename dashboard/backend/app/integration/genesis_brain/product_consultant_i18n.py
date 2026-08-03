"""Localized copy for Product Consultant public rails (DE market first)."""

from __future__ import annotations

from app.integration.genesis_brain.public_brand import ASSISTANT_NAME, BRAND_NAME
from app.integration.locale_service import resolve_locale

_CEO = frozenset({"de", "en", "ru", "uk"})


def pc_locale(raw: str | None) -> str:
    loc = resolve_locale(raw or "de")
    base = loc.split("-")[0].lower()
    return base if base in _CEO else "de"


def copy(locale: str | None, key: str, **fmt: object) -> str:
    loc = pc_locale(locale)
    pack = _COPY.get(loc) or _COPY["de"]
    text = pack.get(key) or _COPY["de"].get(key) or _COPY["en"].get(key) or key
    try:
        return text.format(assistant=ASSISTANT_NAME, brand=BRAND_NAME, **fmt)
    except Exception:
        return text


_COPY: dict[str, dict[str, str]] = {
    "de": {
        "cta_form": "Anfrage öffnen",
        "cta_form_bots": "AI-Bot Anfrage öffnen",
        "cta_catalog": "Leistungen ansehen",
        "cta_privacy": "Datenschutz",
        "default": (
            "Ich bin **{assistant}**, Ihr Berater bei **{brand}**.\n\n"
            "Ich kenne alle Produkte, die Sie hier kaufen können — Websites "
            "(Basic / Business / Premium), AI Bot, Analyse und Services. "
            "Beschreiben Sie Ihre Branche oder senden Sie einen Businessplan — "
            "ich empfehle das passende Paket. Websites baue ich im Chat nicht; "
            "danach führt der Link zur Bestellung.\n\n"
            "In Ihrem Projekt bleibe ich als Vector in der Virtus-Core-Welt: "
            "ich steuere Rollen (Berater, Bot, Analyse), wenn Sie sie gebucht haben."
        ),
        "about": (
            "Ich bin **{assistant}** — der KI-Berater von **{brand}**.\n\n"
            "Moderner Chat wie gewohnt, aber mit einer klaren Rolle: "
            "ich berate zu Produkten und Preisen, empfehle Pakete und "
            "begleite Sie in Ihr Kundenprojekt. KI nutze ich gezielt, "
            "wenn die gebuchte Leistung das braucht — sonst bleibe ich "
            "bei Produktwissen und klaren nächsten Schritten."
        ),
        "welcome_hint": (
            "Häufige Fragen: Pakete, Preise, AI Bot, Datenschutz — "
            "oder beschreiben Sie Ihre Nische."
        ),
        "pricing": (
            "Website-Pakete: **Basic 350 €** · **Business 650 €** · **Premium 1.200 €**.\n"
            "AI Bot: Setup + Monat — Starter / Business / Professional.\n\n"
            "Nennen Sie Ihre Branche — ich empfehle das passende Paket."
        ),
        "website": (
            "Für eine Website empfehle ich eines der Pakete:\n"
            "**Basic 350 €** · **Business 650 €** · **Premium 1.200 €**.\n\n"
            "Beschreiben Sie Branche und Ziel — ich wähle mit Ihnen das passende Paket. "
            "Danach öffnen wir die Anfrage; gebaut wird nach Bestellung in Virtus Core."
        ),
        "chatbot": (
            "AI Bot: digitaler Mitarbeiter für Website-Chat und Telegram "
            "(Setup + Monat — Starter / Business / Professional).\n\n"
            "Sagen Sie mir Kanal und Ziel (Anfragen, Termin, FAQ) — "
            "ich empfehle den Tarif. Vector steuert den Bot in Ihrem Projekt."
        ),
        "privacy": (
            "Wir **verkaufen** und **geben** personenbezogene Daten **nicht** "
            "an Dritte für Werbung weiter.\n\n"
            "Details stehen in der Datenschutzerklärung. "
            "Leistung bestellen — über das Formular."
        ),
        "faq_niche": "Welche Branche passt zu welchem Paket?",
        "faq_plan": "Businessplan — bitte analysieren",
        "faq_packages": "Unterschied Basic / Business / Premium?",
        "faq_bot": "Brauche ich einen AI Bot?",
        "faq_privacy": "Wie schützt ihr meine Daten?",
    },
    "en": {
        "cta_form": "Open order form",
        "cta_form_bots": "Open AI Bot form",
        "cta_catalog": "View catalog",
        "cta_privacy": "Privacy policy",
        "default": (
            "I'm **{assistant}**, your consultant at **{brand}**.\n\n"
            "I know every product you can buy here — websites "
            "(Basic / Business / Premium), AI Bot, analysis and services. "
            "Describe your niche or share a business plan — I'll recommend "
            "the right package. I don't build sites in chat; the next step "
            "is the order form.\n\n"
            "Inside your Virtus Core project I stay as Vector — managing "
            "roles (advisor, bot, analysis) for the services you purchased."
        ),
        "about": (
            "I'm **{assistant}** — the AI consultant for **{brand}**.\n\n"
            "Modern chat UX, clear role: product advice, package fit, "
            "and continuity in your client project. I use generative AI "
            "when a purchased service needs it — otherwise I stay on "
            "product truth and next steps."
        ),
        "welcome_hint": (
            "Common questions: packages, pricing, AI Bot, privacy — "
            "or describe your niche."
        ),
        "pricing": (
            "Website packages: **Basic €350** · **Business €650** · **Premium €1,200**.\n"
            "AI Bot: setup + monthly — Starter / Business / Professional.\n\n"
            "Tell me your niche — I'll recommend a fit."
        ),
        "website": (
            "For a website I recommend one of these packages:\n"
            "**Basic €350** · **Business €650** · **Premium €1,200**.\n\n"
            "Describe your niche and goal — I'll help pick the fit. "
            "Then we open the order form; delivery happens in Virtus Core after purchase."
        ),
        "chatbot": (
            "AI Bot: digital employee for website chat and Telegram "
            "(setup + monthly — Starter / Business / Professional).\n\n"
            "Tell me channel and goal — I'll recommend a plan. "
            "Vector runs the bot inside your project."
        ),
        "privacy": (
            "We do **not sell** or share personal data with third parties for ads.\n\n"
            "Details are in the privacy policy. To order — use the form."
        ),
        "faq_niche": "Which package fits my niche?",
        "faq_plan": "Analyze my business plan",
        "faq_packages": "Basic vs Business vs Premium?",
        "faq_bot": "Do I need an AI Bot?",
        "faq_privacy": "How do you protect my data?",
    },
    "ru": {
        "cta_form": "Открыть форму заявки",
        "cta_form_bots": "Открыть форму AI-сотрудника",
        "cta_catalog": "Смотреть каталог",
        "cta_privacy": "Datenschutz",
        "default": (
            "Я **{assistant}**, консультант **{brand}**.\n\n"
            "Знаю все продукты, которые можно купить здесь — сайты "
            "(Basic / Business / Premium), AI Bot, анализ и услуги. "
            "Опишите нишу или пришлите бизнес-план — предложу пакет. "
            "Сайты в чате не собираю — дальше форма заявки.\n\n"
            "В проекте Virtus Core я остаюсь с вами как Vector: "
            "веду роли (консультант, бот, аналитик) в купленных услугах."
        ),
        "about": (
            "Я **{assistant}** — ИИ-консультант **{brand}**.\n\n"
            "Современный чат, но с ролью: продукты, пакеты и сопровождение "
            "в клиентском проекте. Генеративный ИИ подключаю, когда это "
            "нужно купленной услуге — иначе опираюсь на каталог и следующие шаги."
        ),
        "welcome_hint": (
            "Частые вопросы: пакеты, цены, AI Bot, защита данных — "
            "или опишите нишу."
        ),
        "pricing": (
            "Сайты: **Basic 350 €** · **Business 650 €** · **Premium 1 200 €**.\n"
            "AI Bot: настройка + месяц — Starter / Business / Professional.\n\n"
            "Назовите нишу — подскажу пакет."
        ),
        "website": (
            "Для сайта подойдёт один из пакетов:\n"
            "**Basic 350 €** · **Business 650 €** · **Premium 1 200 €**.\n\n"
            "Опишите нишу и цель — подберём пакет. Дальше форма заявки; "
            "сборка — после покупки в Virtus Core."
        ),
        "chatbot": (
            "AI Bot: цифровой сотрудник для чата на сайте и Telegram "
            "(настройка + месяц — Starter / Business / Professional).\n\n"
            "Скажите канал и задачу — предложу тариф. "
            "Vector ведёт бота в вашем проекте."
        ),
        "privacy": (
            "Мы **не продаём** и **не передаём** персональные данные третьим лицам "
            "для рекламы.\n\n"
            "Подробности — в Datenschutz. Заказ — через форму."
        ),
        "faq_niche": "Какой пакет под мою нишу?",
        "faq_plan": "Проанализируй бизнес-план",
        "faq_packages": "Чем отличаются Basic / Business / Premium?",
        "faq_bot": "Нужен ли мне AI Bot?",
        "faq_privacy": "Как защищаете данные?",
    },
    "uk": {
        "cta_form": "Відкрити форму заявки",
        "cta_form_bots": "Відкрити форму AI-бота",
        "cta_catalog": "Каталог послуг",
        "cta_privacy": "Політика конфіденційності",
        "default": (
            "Я **{assistant}**, консультант **{brand}**.\n\n"
            "Знаю всі продукти, які можна купити тут — сайти "
            "(Basic / Business / Premium), AI Bot, аналіз і послуги. "
            "Опишіть нішу або надішліть бізнес-план — запропоную пакет."
        ),
        "about": (
            "Я **{assistant}** — AI-консультант **{brand}**. "
            "Сучасний чат із роллю консультанта по продуктах і пакетах."
        ),
        "welcome_hint": "Часті питання: пакети, ціни, AI Bot — або опишіть нішу.",
        "pricing": (
            "Сайти: **Basic 350 €** · **Business 650 €** · **Premium 1 200 €**.\n"
            "Назвіть нішу — підкажу пакет."
        ),
        "website": (
            "Для сайту: **Basic / Business / Premium**. Опишіть нішу — підберемо пакет."
        ),
        "chatbot": (
            "AI Bot для сайту та Telegram. Опишіть задачу — запропоную тариф."
        ),
        "privacy": (
            "Ми не продаємо персональні дані третім особам для реклами. "
            "Деталі — у політиці конфіденційності."
        ),
        "faq_niche": "Який пакет під мою нішу?",
        "faq_plan": "Проаналізуй бізнес-план",
        "faq_packages": "Чим відрізняються Basic / Business / Premium?",
        "faq_bot": "Чи потрібен мені AI Bot?",
        "faq_privacy": "Як захищаєте дані?",
    },
}
