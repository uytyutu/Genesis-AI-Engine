"""Virtus Core — universal service model + product line.

Every customer-facing service follows the same lifecycle:
  Dialog → Concept → Collaboration → Approval → Choice (one-time | subscription)

One-time purchase = deliverable handoff. Subscription = ongoing digital company.
"""

from __future__ import annotations

from typing import Any

BRAND_NAME = "Virtus Core"
ASSISTANT_NAME = "Vector"
STUDIO_NAME = "Virtus Studio"
INTERNAL_CEO_EDITION = "Internal CEO Edition"

# --- Service lifecycle (all services) ------------------------------------------

LIFECYCLE_DIALOG = "dialog"
LIFECYCLE_CONCEPT = "concept"
LIFECYCLE_COLLABORATION = "collaboration"
LIFECYCLE_APPROVAL = "approval"
LIFECYCLE_CHOICE = "choice"
LIFECYCLE_HANDOFF = "handoff"  # one-time path
LIFECYCLE_SUBSCRIPTION = "subscription"  # ongoing path

SERVICE_LIFECYCLE: tuple[tuple[str, str], ...] = (
    (LIFECYCLE_DIALOG, "Диалог — Vector выясняет задачу (текст, голос, файлы, ссылки → один проект)"),
    (LIFECYCLE_CONCEPT, "Концепция — первая версия результата, не код и не внутренние файлы"),
    (LIFECYCLE_COLLABORATION, "Совместная работа — правки до полного согласования"),
    (LIFECYCLE_APPROVAL, "Согласование — клиент явно подтверждает «да, именно так»"),
    (LIFECYCLE_CHOICE, "Выбор — разовая покупка или подписка (без навязывания)"),
)

# --- One-time services (deliverable catalog) -----------------------------------

SERVICE_WEBSITE = "website"
SERVICE_BUSINESS_PLAN = "business_plan"
SERVICE_PRESENTATION = "presentation"
SERVICE_DOCUMENT_ANALYSIS = "document_analysis"
SERVICE_AUTOMATION = "automation"
SERVICE_AI_EMPLOYEE = "ai_employee"
SERVICE_CHATBOT = "chatbot"
SERVICE_MARKETING = "marketing_strategy"
SERVICE_CRM = "crm"
SERVICE_LOGO = "logo_design"
SERVICE_SEO = "seo_optimization"
SERVICE_APP = "application"
SERVICE_GAME = "game"

ONE_TIME_SERVICES: tuple[dict[str, Any], ...] = (
    {
        "id": SERVICE_WEBSITE,
        "name": "Business Website",
        "customer_name_ru": "Сайт для бизнеса",
        "artifact_ru": "Website",
        "description_ru": "Профессиональный сайт под ключ до утверждения и передачи проекта.",
        "online": True,
    },
    {
        "id": SERVICE_BUSINESS_PLAN,
        "name": "Business Plan",
        "customer_name_ru": "Бизнес-план",
        "artifact_ru": "Business Plan",
        "description_ru": "Профессиональная доработка и оформление бизнес-плана.",
        "online": False,
    },
    {
        "id": SERVICE_PRESENTATION,
        "name": "Presentation",
        "customer_name_ru": "Презентация",
        "artifact_ru": "Presentation",
        "description_ru": "Презентация для инвесторов или партнёров.",
        "online": False,
    },
    {
        "id": SERVICE_DOCUMENT_ANALYSIS,
        "name": "Document Analysis",
        "customer_name_ru": "Анализ документов",
        "artifact_ru": "Documents",
        "description_ru": "Анализ бизнес-документов с отчётами и рекомендациями.",
        "online": True,
    },
    {
        "id": SERVICE_AUTOMATION,
        "name": "Automation",
        "customer_name_ru": "Автоматизация",
        "artifact_ru": "Automation",
        "description_ru": "Автоматизация бизнес-процессов под задачу клиента.",
        "online": False,
    },
    {
        "id": SERVICE_AI_EMPLOYEE,
        "name": "AI Employee",
        "customer_name_ru": "Цифровой сотрудник",
        "artifact_ru": "Digital Employee",
        "description_ru": "Готовый цифровой сотрудник под роль (продажи, поддержка и др.).",
        "online": False,
    },
    {
        "id": SERVICE_CHATBOT,
        "name": "Chatbot",
        "customer_name_ru": "Чат-бот",
        "artifact_ru": "Chatbot",
        "description_ru": "Бот для сайта, Telegram или WhatsApp.",
        "online": False,
    },
    {
        "id": SERVICE_MARKETING,
        "name": "Marketing Strategy",
        "customer_name_ru": "Маркетинговая стратегия",
        "artifact_ru": "Marketing",
        "description_ru": "Стратегия продвижения и контент-план.",
        "online": False,
    },
    {
        "id": SERVICE_CRM,
        "name": "CRM",
        "customer_name_ru": "CRM",
        "artifact_ru": "CRM",
        "description_ru": "Настройка CRM под процессы клиента.",
        "online": False,
    },
    {
        "id": SERVICE_LOGO,
        "name": "Logo Design",
        "customer_name_ru": "Логотип",
        "artifact_ru": "Brand",
        "description_ru": "Разработка или доработка фирменного знака.",
        "online": False,
    },
    {
        "id": SERVICE_SEO,
        "name": "SEO Optimization",
        "customer_name_ru": "SEO-оптимизация",
        "artifact_ru": "SEO",
        "description_ru": "Оптимизация сайта для поисковых систем.",
        "online": False,
    },
    {
        "id": SERVICE_APP,
        "name": "Application",
        "customer_name_ru": "Приложение",
        "artifact_ru": "Application",
        "description_ru": "Мобильное или веб-приложение под задачу.",
        "online": False,
    },
    {
        "id": SERVICE_GAME,
        "name": "Game",
        "customer_name_ru": "Игра",
        "artifact_ru": "Game",
        "description_ru": "Игровой проект — по мере запуска каталога.",
        "online": False,
    },
)

SERVICE_BY_ID: dict[str, dict[str, Any]] = {s["id"]: s for s in ONE_TIME_SERVICES}

WEBSITE_PACKAGE_LABELS: dict[str, str] = {
    "basic": "Business Website",
    "business": "Professional Website",
    "premium": "Premium Business Website",
}

# --- Subscriptions (environment — not a discount on services) ------------------

SUB_VECTOR_FREE = "free"
SUB_VECTOR_CORE = "core"  # internal — customer-facing: Professional
SUB_VECTOR_BUSINESS = "business"
SUB_VECTOR_ENTERPRISE = "enterprise"

# Legacy aliases (do not use in new code)
SUB_VECTOR_PRO = SUB_VECTOR_CORE
SUB_VECTOR_TEAM = SUB_VECTOR_BUSINESS

PRODUCT_PRINCIPLES: tuple[str, ...] = (
    "Virtus Core никогда не принуждает пользователя к покупке.",
    "Сначала продукт создаёт ценность.",
    "Потом предлагает варианты развития.",
    "Пользователь всегда принимает решение добровольно.",
    "Платёж появляется после ценности — не после регистрации.",
    "Free без срока: пользователь остаётся сколько угодно, пока лимитов достаточно.",
)

SUBSCRIPTION_TIERS: tuple[dict[str, Any], ...] = (
    {
        "id": SUB_VECTOR_FREE,
        "internal_id": SUB_VECTOR_FREE,
        "name": "Free",
        "customer_name_ru": "Free",
        "growth_stage_ru": "Знакомство",
        "tagline_ru": "Знакомство с цифровой компанией",
        "description_ru": (
            f"Без срока действия. Один активный проект, ограниченные сообщения и файлы. "
            f"Познакомиться с {ASSISTANT_NAME} и увидеть ценность — без давления на покупку."
        ),
        "audience_ru": "Знакомство",
        "available": True,
        "price_set": True,
        "price_eur_month": 0,
    },
    {
        "id": SUB_VECTOR_CORE,
        "internal_id": SUB_VECTOR_CORE,
        "name": "Vector Starter",
        "customer_name_ru": "Vector Starter",
        "growth_stage_ru": "AI Business Employee",
        "tagline_ru": "Vector для сайта и базовых диалогов",
        "description_ru": (
            "Website widget, ограниченные диалоги, DE hosting. "
            "Setup from 499 €. Paid checkout Coming Soon."
        ),
        "audience_ru": "SMB",
        "available": False,
        "price_set": True,
        "price_eur_month": 99,
    },
    {
        "id": SUB_VECTOR_BUSINESS,
        "internal_id": SUB_VECTOR_BUSINESS,
        "name": "Vector Business",
        "customer_name_ru": "Vector Business",
        "growth_stage_ru": "AI Business Employee",
        "tagline_ru": "Больше объёма и каналов",
        "description_ru": (
            "Больше объёма, knowledge base, каналы. Paid checkout Coming Soon."
        ),
        "audience_ru": "SMB growth",
        "available": False,
        "price_set": True,
        "price_eur_month": 199,
    },
    {
        "id": SUB_VECTOR_ENTERPRISE,
        "internal_id": SUB_VECTOR_ENTERPRISE,
        "name": "Vector Professional",
        "customer_name_ru": "Vector Professional",
        "growth_stage_ru": "AI Business Employee",
        "tagline_ru": "Приоритет и интеграции",
        "description_ru": (
            "Priority ops, интеграции, выше лимиты. Paid checkout Coming Soon."
        ),
        "audience_ru": "Growing teams",
        "available": False,
        "price_set": True,
        "price_eur_month": 349,
    },
)


def service_label_ru(service_id: str, *, fallback: str = "результат") -> str:
    row = SERVICE_BY_ID.get(service_id)
    return str(row["customer_name_ru"]) if row else fallback


def artifact_label_ru(service_id: str, *, fallback: str = "Результат") -> str:
    row = SERVICE_BY_ID.get(service_id)
    if not row:
        return fallback
    return str(row.get("artifact_ru") or row.get("customer_name_ru"))


# --- Universal customer messages -----------------------------------------------

def project_execution_ack_intro(service_id: str) -> str:
    """PE — Vector accepts responsibility; short, project-first."""
    if service_id == SERVICE_WEBSITE:
        return (
            "Проект создан.\n"
            "Прежде чем делать первый вариант, хочу понять ваш бизнес.\n\n"
            "Как называется компания и чем вы занимаетесь?\n"
            "Что человек должен сделать на сайте — позвонить, записаться, купить?"
        )
    label = service_label_ru(service_id, fallback="проект")
    return (
        "Проект создан.\n"
        f"Давайте сделаем {label.lower()} именно таким, каким вы хотите его видеть.\n\n"
        f"Опишите, пожалуйста, каким вы представляете результат."
    )


def universal_service_intro(service_id: str) -> str:
    """Stage 1 — dialog. Same pattern for every service."""
    label = service_label_ru(service_id, fallback="задачу")
    return (
        f"Отлично.\n"
        f"Давайте подготовим **{label.lower()}**, который будет работать на ваш бизнес.\n\n"
        f"Сначала хочу понять задачу.\n\n"
        "Вы можете:\n"
        "• рассказать текстом или голосом;\n"
        "• прикрепить документы, изображения, ссылки;\n"
        "• описать всё одним сообщением.\n\n"
        f"{ASSISTANT_NAME} объединит всё в **один проект**."
    )


def universal_first_version_scenario() -> str:
    """Human PM narrative after first deliverable — work continues until approval."""
    return (
        "Мы подготовили первую версию результата.\n"
        "Она уже находится внутри вашего проекта.\n"
        "Посмотрите её.\n"
        "Если захотите изменить структуру, тексты, цвета или другие детали — просто скажите.\n"
        "После вашего окончательного согласования мы подготовим финальную версию."
    )


def universal_concept_ready_message(service_id: str) -> str:
    """Stage 2–3 — first version in project; iteration before handoff."""
    artifact = artifact_label_ru(service_id)
    body = universal_first_version_scenario()
    return f"**{artifact}** — первая версия в проекте.\n\n{body}"


def universal_approved_purchase_options(service_id: str, *, estimate_block: str = "") -> str:
    """Stage 4 — after explicit approval only; voluntary choice, no pressure."""
    label = service_label_ru(service_id, fallback="результат")
    header = f"**Ваш проект сохранён.**\n\n"
    if estimate_block:
        header += f"{estimate_block.strip()}\n\n"
    return (
        header
        + f"**{label}** полностью согласован. Вы можете:\n\n"
        f"🛒 **Получить этот готовый проект полностью** (разовая покупка)\n"
        "Полный результат: файлы, архив, инструкции, права. "
        f"После передачи сотрудничество по этому проекту завершено.\n\n"
        f"⭐ **Продолжить развивать его вместе с {ASSISTANT_NAME}** (подписка)\n"
        f"Проект остаётся в {BRAND_NAME}. {ASSISTANT_NAME} — постоянный цифровой сотрудник: "
        "новые версии, другие проекты, CRM, автоматизация.\n\n"
        "Вы сами выбираете — ничего не навязываю."
    )


def universal_project_saved_without_purchase() -> str:
    """Free user declined purchase — project stays, export locked, no guilt copy."""
    return (
        "**Ваш проект сохранён.**\n\n"
        "Вы можете вернуться к нему в любое время.\n\n"
        "Когда будете готовы:\n"
        "🛒 получить готовый проект полностью\n"
        "или\n"
        f"⭐ продолжить развивать его вместе с {ASSISTANT_NAME}.\n\n"
        "Решение всегда за вами."
    )


def product_principles_block() -> str:
    lines = "\n".join(f"• {p}" for p in PRODUCT_PRINCIPLES)
    return f"## Product Principles\n{lines}"


def subscription_growth_stages_block() -> str:
    lines = "\n".join(
        f"• **{t['customer_name_ru']}** — {t['growth_stage_ru']}: {t['tagline_ru']}"
        for t in SUBSCRIPTION_TIERS
    )
    return f"## Этапы роста цифровой компании\n{lines}"


def one_time_handoff_summary(service_id: str) -> str:
    """What client receives after one-time payment (all services)."""
    from app.legal.handoff import one_time_purchase_handoff

    return one_time_purchase_handoff()


def project_display_name(service_id: str, *, project_name: str | None = None) -> str:
    """Customer-facing project label — never a package code."""
    if service_id == SERVICE_WEBSITE:
        label = "Landing Page"
    else:
        label = service_label_ru(service_id, fallback="Projekt")
    if project_name and project_name.strip():
        return f"{label} «{project_name.strip()}»"
    return label


def project_order_created_message(
    service_id: str,
    *,
    launch_mode: bool = False,
    project_name: str | None = None,
    ui_lang: str | None = None,
) -> str:
    """After order submit — project fixed, not «we will start building someday»."""
    name = project_display_name(service_id, project_name=project_name)
    lang = (ui_lang or "de").strip().lower().split("-")[0]
    if launch_mode:
        msgs = {
            "de": (
                f"Danke. {name} ist erfasst — "
                "wir bereiten die Übergabe der abgestimmten Version vor."
            ),
            "en": (
                f"Thank you. {name} is registered — "
                "we are preparing handover of the agreed version."
            ),
            "ru": (
                f"Спасибо. {name} зафиксирован — "
                "готовим передачу согласованной версии."
            ),
            "uk": (
                f"Дякуємо. {name} зафіксовано — "
                "готуємо передачу узгодженої версії."
            ),
        }
        return msgs.get(lang) or msgs["en"]
    msgs = {
        "de": (
            f"Danke! Ihre Anfrage für {name} ist eingegangen. "
            "Bitte zahlen Sie jetzt — dann fixieren wir den Projektstart."
        ),
        "en": (
            f"Thank you! Your request for {name} was received. "
            "Please pay now — then we lock in the project start."
        ),
        "ru": (
            f"Спасибо! Заявка на {name} получена. "
            "Оплатите сейчас — после этого фиксируем старт проекта."
        ),
        "uk": (
            f"Дякуємо! Заявку на {name} отримано. "
            "Оплатіть зараз — після цього фіксуємо старт проєкту."
        ),
    }
    return msgs.get(lang) or msgs["en"]


def project_awaiting_payment_message(
    *, launch_mode: bool = False, ui_lang: str | None = None
) -> str:
    lang = (ui_lang or "de").strip().lower().split("-")[0]
    if launch_mode:
        msgs = {
            "de": (
                "Bitte bezahlen Sie die Bestellung — das Projekt bleibt wie abgestimmt. "
                "Es ändert sich nur der Status."
            ),
            "en": (
                "Please pay for the order — the project stays as agreed. "
                "Only the status changes."
            ),
            "ru": (
                "Оплатите заказ — проект остаётся как согласовано. "
                "Меняется только статус."
            ),
            "uk": (
                "Оплатіть замовлення — проєкт залишається як узгоджено. "
                "Змінюється лише статус."
            ),
        }
        return msgs.get(lang) or msgs["en"]
    msgs = {
        "de": "Bitte bezahlen Sie die Bestellung — dann fixieren wir den Projektstart.",
        "en": "Please pay for the order — then we lock in the project start.",
        "ru": "Оплатите заказ — после этого фиксируем старт проекта.",
        "uk": "Оплатіть замовлення — після цього фіксуємо старт проєкту.",
    }
    return msgs.get(lang) or msgs["en"]


def project_client_current_step(service_id: str, status: str) -> str:
    if status == "awaiting_payment":
        return "Wir warten auf die Zahlung zur Projektfixierung"
    if status in ("paid", "in_production"):
        return "Wir bereiten die abgestimmte Version zur Übergabe vor"
    if status == "ready":
        return "Projekt fertig — Übergabe wird vorbereitet"
    if status == "delivered":
        return "Projekt übergeben — danke für Ihr Vertrauen!"
    return "Wir bearbeiten Ihr Projekt"


def project_client_next_step(service_id: str, status: str) -> str:
    if status == "awaiting_payment":
        return "Projektzahlung"
    if status in ("paid", "in_production"):
        return "Übergabe der abgestimmten Version"
    if status == "ready":
        return "Финальная передача проекта"
    if status == "delivered":
        return "Проект завершён"
    return "Обработка проекта"


def project_client_timeline(status: str) -> list[dict[str, Any]]:
    paid = status in ("paid", "in_production", "ready", "delivered")
    handoff = status in ("in_production", "ready", "delivered")
    return [
        {"id": "payment", "label": "Zahlung eingegangen", "done": paid},
        {"id": "handoff", "label": "Vorbereitung der Übergabe", "done": handoff},
    ]


def project_launch_deliverables(service_id: str) -> list[str]:
    """Launch-mode checklist — publication/handoff, not «build from scratch»."""
    # Client-facing DE (Path A market); keep label short and language-neutral where possible.
    label = "Website" if service_id == SERVICE_WEBSITE else service_label_ru(service_id, fallback="Projekt")
    return [
        f"Übergabe der abgestimmten Version ({label})",
        "Finale Prüfung vor dem Go-live",
        "Anleitungen und Zugänge",
        "Begleitung bei der Einführung",
    ]


# Website aliases (existing callers)
def website_studio_intro() -> str:
    return universal_service_intro(SERVICE_WEBSITE)


def website_concept_ready_message() -> str:
    return universal_concept_ready_message(SERVICE_WEBSITE)


def website_approved_purchase_options() -> str:
    return universal_approved_purchase_options(SERVICE_WEBSITE)


# --- Rules for Vector / catalog ------------------------------------------------

def universal_service_model_rules() -> str:
    """Full business model — injected into commerce rules and Brain knowledge."""
    lifecycle = "\n".join(f"{i + 1}. {desc}" for i, (_, desc) in enumerate(SERVICE_LIFECYCLE))
    services = "\n".join(
        f"• **{s['customer_name_ru']}**"
        + (" ✓ онлайн" if s.get("online") else " · скоро")
        for s in ONE_TIME_SERVICES
    )
    subs = "\n".join(
        f"• **{t['customer_name_ru']}** ({t['growth_stage_ru']}) — {t['tagline_ru']}"
        + (" ✓" if t["available"] else " · в разработке")
        for t in SUBSCRIPTION_TIERS
    )
    principles = product_principles_block()
    stages = subscription_growth_stages_block()
    return f"""## Универсальная модель услуг {BRAND_NAME}

{principles}

{stages}

**Любая услуга** (сайт, бизнес-план, презентация, автоматизация, чат-бот, CRM, маркетинг, приложение и др.) 
работает по **одному сценарию**:

{lifecycle}

**Разовая покупка:** готовый результат → передача → сотрудничество завершено.
**Подписка:** цифровая компания продолжает работать — проекты внутри {BRAND_NAME}.

Подписка продаётся **не как скидка**, а как **следующий этап роста** цифровой компании.
Разовая покупка остаётся выгодной, когда нужен **один конкретный результат**.
**Ориентировочные диапазоны услуг** — показывай сразу по целевому рынку в локальной валюте.

### Каталог услуг (разовая покупка)
{services}

### Подписки (этапы роста)
{subs}

### {INTERNAL_CEO_EDITION}
Не продаётся. Только владелец. Не копировать клиентам.

### Правила {ASSISTANT_NAME}
1. Начинай с **диалога** — не с подписки, не с кода, не с внутренних терминов.
2. Показывай **концепцию** — итерации до согласования («переделай», «добавь», «измени»).
3. **Продажа** — только после явного «да» / «оформляем» и **созданной ценности**.
4. После согласования — **два варианта** (разовая покупка | подписка), **без давления**.
5. Никогда не пиши «купите подписку, иначе…» — только «ваш проект сохранён, вы можете…».
6. Free **без срока** — лимиты по объёму, не по времени.
7. Не путать услугу и тариф: Business Website ≠ Professional подписка.
8. Недоступные услуги — честно «скоро», предложи то, что есть (сайт, анализ PDF).
9. Юр. данные перед передачей (DE: Impressum, Datenschutz) — веди клиента, не «добавьте сами».
"""


def service_vs_subscription_rules() -> str:
    """Backward-compatible alias."""
    return universal_service_model_rules()
