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
SUB_VECTOR_PRO = "pro"
SUB_VECTOR_TEAM = "team"
SUB_VECTOR_ENTERPRISE = "enterprise"

SUBSCRIPTION_TIERS: tuple[dict[str, Any], ...] = (
    {
        "id": SUB_VECTOR_FREE,
        "name": "Vector Free",
        "customer_name_ru": "Vector Free",
        "tagline_ru": "Знакомство с цифровой компанией",
        "description_ru": (
            f"Ограниченные лимиты: сообщения, файлы, голос, проекты. "
            f"Познакомиться с {ASSISTANT_NAME}."
        ),
        "audience_ru": "Познакомиться",
        "available": True,
        "price_set": False,
    },
    {
        "id": SUB_VECTOR_PRO,
        "name": "Vector Pro",
        "customer_name_ru": "Vector Pro",
        "tagline_ru": "Для предпринимателей",
        "description_ru": (
            "Проекты, работа с Vector, развитие результатов, расширенные лимиты. "
            "Цифровая компания, которая продолжает работать — не скидка на услугу."
        ),
        "audience_ru": "Предприниматели",
        "available": False,
        "price_set": False,
    },
    {
        "id": SUB_VECTOR_TEAM,
        "name": "Vector Team",
        "customer_name_ru": "Vector Team",
        "tagline_ru": "Для небольшой команды",
        "description_ru": "Общие проекты, совместная работа, цифровые сотрудники.",
        "audience_ru": "Команды",
        "available": False,
        "price_set": False,
    },
    {
        "id": SUB_VECTOR_ENTERPRISE,
        "name": "Vector Enterprise",
        "customer_name_ru": "Vector Enterprise",
        "tagline_ru": "Для крупных компаний",
        "description_ru": "Роли, интеграции, автоматизация процессов, API.",
        "audience_ru": "Enterprise",
        "available": False,
        "price_set": False,
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


def universal_concept_ready_message(service_id: str) -> str:
    """Stage 2–3 — first version ready, iteration before sale."""
    artifact = artifact_label_ru(service_id)
    label = service_label_ru(service_id, fallback="работу")
    return (
        f"**Первая версия готова.**\n"
        f"В проект добавлен результат — **{artifact}**.\n\n"
        f"Посмотрите вариант. Если нужны правки — скажите, что изменить.\n\n"
        f"Когда всё устроит — оформим **покупку готового результата** ({label.lower()}) "
        f"или обсудим **подписку**, если хотите развивать проект вместе с {ASSISTANT_NAME}."
    )


def universal_approved_purchase_options(service_id: str, *, estimate_block: str = "") -> str:
    """Stage 4 — after explicit approval only; preliminary estimate first."""
    label = service_label_ru(service_id, fallback="результат")
    header = f"**{label} полностью согласован.**\n\n"
    if estimate_block:
        header += f"{estimate_block.strip()}\n\n"
    return (
        header
        + "Теперь доступны два варианта:\n\n"
        f"**1. Разовая покупка — готовый {label.lower()}**\n"
        "Полный проект: файлы, архив, инструкции, права. Результат ваш — "
        f"{BRAND_NAME} завершает сотрудничество после передачи.\n\n"
        f"**2. Подписка — продолжить с {ASSISTANT_NAME}**\n"
        f"Проект остаётся в {BRAND_NAME}. {ASSISTANT_NAME} — постоянный цифровой сотрудник: "
        "доработки, новые версии, подключение услуг.\n\n"
        "Подписка — не скидка, а другой опыт. Выберите сами — ничего не навязываю."
    )


def one_time_handoff_summary(service_id: str) -> str:
    """What client receives after one-time payment (all services)."""
    return (
        "После оплаты вы получите:\n"
        "✓ полный проект и исходные файлы\n"
        "✓ архив (ZIP)\n"
        "✓ инструкции\n"
        "✓ доступы и права использования (если применимо)\n\n"
        f"После передачи {BRAND_NAME} не сопровождает продукт."
    )


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
        f"• **{t['customer_name_ru']}** — {t['tagline_ru']}"
        + (" ✓" if t["available"] else " · в разработке")
        for t in SUBSCRIPTION_TIERS
    )
    return f"""## Универсальная модель услуг {BRAND_NAME}

**Любая услуга** (сайт, бизнес-план, презентация, автоматизация, чат-бот, CRM, маркетинг, приложение и др.) 
работает по **одному сценарию**:

{lifecycle}

**Разовая покупка:** готовый результат → передача → сотрудничество завершено.
**Подписка:** цифровая компания продолжает работать — проекты внутри {BRAND_NAME}.

Подписка продаётся **не как скидка**, а как другой опыт (постоянная команда).
**Ориентировочные диапазоны услуг** — показывай сразу по целевому рынку в локальной валюте.
Фиксированный тариф подписки Pro/Team — когда продукт откроется; ценность объясняй честно.

### Каталог услуг (разовая покупка)
{services}

### Подписки (среда)
{subs}

### {INTERNAL_CEO_EDITION}
Не продаётся. Только владелец. Не копировать клиентам.

### Правила {ASSISTANT_NAME}
1. Начинай с **диалога** — не с подписки, не с кода, не с внутренних терминов.
2. Показывай **концепцию** — итерации до согласования («переделай», «добавь», «измени»).
3. **Продажа** — только после явного «да» / «оформляем».
4. После согласования — **два варианта** (разовая покупка | подписка), без давления.
5. Не путать услугу и тариф: Business Website ≠ Vector Pro.
6. Недоступные услуги — честно «скоро», предложи то, что есть (сайт, анализ PDF).
7. Юр. данные перед передачей (DE: Impressum, Datenschutz) — веди клиента, не «добавьте сами».
"""


def service_vs_subscription_rules() -> str:
    """Backward-compatible alias."""
    return universal_service_model_rules()
