"""Farm Engine v1 — OS of digital services (not a site builder / microtask farm).

Canonical stack (CEO 2026-08-02) — never collapse adjacent layers:
  Capabilities → Composer → Digital Products → Distribution
  → Finance Reality Law → Ledger

  Capabilities = what the system can do (OCR, Browser, LLM…) — not products.
  Composer     = assembles a sellable service from capabilities.
  Products     = what is sold (Invoice Parser, Website Audit…).
  Distribution = where it is sold (Inbound / Marketplace / Partners / M2M).
  Finance Reality = sole gate into REAL (Hard REAL + single truth path).

Separate always:
  - Work source (who pays) ≠ Capabilities (how Virtus runs the job)
  - Toloka Requester = Spend capability; Toloka Performer bot = Hard Reject
  - No product/channel may increase REAL without external payout passport

Pipeline (platform-agnostic):
  Opportunity Scanner → Legal Check → Profit/ROI Check
  → CEO Decision → Execution Queue (dry_run)
  → (v2) Live Connector → Confirmed € → Ledger

v1 does NOT:
  - auto-solve captchas / human-only microtasks
  - multi-account / anti-fraud evasion
  - live Earn adapters (those need Legal Review + Mission 3)

v1 DOES:
  - seed research opportunities from the Earn catalog shape
  - CEO GO / Reject / Hold / Research
  - dry_run execution queue
  - profit ledger snapshot (Farm REAL separate from Path A display)

Farm KPI (north star, not “found opportunities”):
  Research → GO → Prototype → Confirmed €
  Until Confirmed € exists, Farm = research only.

v2 requirements (CEO 2026-08-01 — do not implement in v1 freeze of Path A):
  - Opportunity passport per source: Source, Legal, Automation (Full/Partial/None),
    Expected ROI %, Avg payout, Avg latency, Confidence, Status
  - Live Connector only after: ToS automation allowed + ROI > 0 + one-time CEO GO
  - North-star metric visible: Research | GO | Prototype | Confirmed €
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATE_FILE = "farm_engine_v1_state.json"
QUEUE_FILE = "farm_engine_v1_queue.jsonl"
DECISIONS_FILE = "farm_engine_v1_decisions.jsonl"

FACTORY_MODEL_VERSION = "1.2"
DISTRIBUTION_MODEL_VERSION = "1.1"

# Full value chain including money discipline
VALUE_CHAIN: tuple[str, ...] = (
    "capabilities",
    "composer",
    "digital_products",
    "distribution",
    "finance_reality_law",
    "ledger",
)

# Platforms worth researching as Earn Channels (not "find clients" first).
# All four must be true — otherwise Reject / Spend-only / research-not-GO.
PLATFORM_EARN_CRITERIA: tuple[dict[str, str], ...] = (
    {
        "id": "automation_officially_allowed",
        "title_ru": "Официально разрешает автоматизацию (ToS)",
    },
    {
        "id": "has_api",
        "title_ru": "Есть официальный API",
    },
    {
        "id": "pays_providers",
        "title_ru": "Платит исполнителям / провайдерам",
    },
    {
        "id": "no_forbidden_human_judgment",
        "title_ru": (
            "Не требует человеческого решения там, где боты запрещены правилами"
        ),
    },
)

# Distribution channel groups (product stays; channels multiply)
DISTRIBUTION_GROUPS: tuple[dict[str, Any], ...] = (
    {
        "id": "inbound",
        "title_en": "Inbound",
        "title_ru": "Входящие",
        "channels": (
            {"id": "stripe", "label": "Stripe"},
            {"id": "website", "label": "Website"},
            {"id": "own_api", "label": "API"},
        ),
    },
    {
        "id": "marketplace",
        "title_en": "Marketplace",
        "title_ru": "Маркетплейсы",
        "channels": (
            {"id": "rapidapi", "label": "RapidAPI"},
            {"id": "api_market", "label": "API.market"},
        ),
    },
    {
        "id": "partners",
        "title_en": "Partners",
        "title_ru": "Партнёры",
        "channels": (
            {"id": "white_label", "label": "White-label"},
            {"id": "agencies", "label": "Agencies"},
        ),
    },
    {
        "id": "machine_to_machine",
        "title_en": "Machine-to-Machine",
        "title_ru": "M2M",
        "channels": (
            {"id": "mcp", "label": "MCP"},
            {"id": "x402", "label": "x402"},
            {"id": "agent_marketplaces", "label": "Agent marketplaces"},
        ),
    },
)

# Flat list kept for older UI / criteria helpers
DISTRIBUTION_CHANNEL_CLASSES: tuple[dict[str, str], ...] = (
    {"id": "inbound", "label_ru": "Inbound (Stripe / Website / API)"},
    {"id": "marketplace", "label_ru": "Marketplace (RapidAPI, API.market…)"},
    {"id": "partners", "label_ru": "Partners (white-label / agencies)"},
    {"id": "machine_to_machine", "label_ru": "M2M (MCP / x402 / agent marketplaces)"},
)

# Hard rejects — never enter GO/execute without human platform ToS that allows bots.
_FORBIDDEN_WORK_KINDS = frozenset(
    {
        "captcha",
        "human_microtask_bot",
        "tos_forbidden_automation",
        "multi_account_evasion",
        "human_ui_only_bot",
        "mturk_performer_bot",
        "clickworker_bot",
        "antifraud_bypass",
    }
)

# Capabilities — what the system can do (NOT products)
CAPABILITIES: tuple[dict[str, str], ...] = (
    {"id": "llm", "label": "LLM"},
    {"id": "ocr", "label": "OCR"},
    {"id": "browser", "label": "Browser"},
    {"id": "vision", "label": "Vision"},
    {"id": "python", "label": "Python"},
    {"id": "toloka_requester", "label": "Toloka Requester (Spend)"},
)

# Back-compat alias (older callers / tests expecting EXECUTION_TOOLS)
EXECUTION_TOOLS = CAPABILITIES

# One capability → many products (Composer fan-out examples)
CAPABILITY_PRODUCT_FANOUT: tuple[dict[str, Any], ...] = (
    {
        "capability_id": "ocr",
        "products": [
            "Invoice Parser",
            "Resume Parser",
            "PDF → JSON",
            "Passport Extractor",
            "Receipt Reader",
        ],
    },
    {
        "capability_id": "browser",
        "products": [
            "Website Audit",
            "SEO Audit",
            "Competitor Monitor",
            "Price Tracker",
            "Change Detection",
        ],
    },
)

# Sellable digital products (research classes; not live connectors)
DIGITAL_PRODUCT_CLASSES: tuple[dict[str, Any], ...] = (
    {"id": "website_audit_api", "title": "Website Audit API", "income": "high", "farm_fit": True, "from_capabilities": ["browser", "llm"]},
    {"id": "ocr_document_processing", "title": "OCR / Document Processing", "income": "high", "farm_fit": True, "from_capabilities": ["ocr", "llm"]},
    {"id": "invoice_parser_api", "title": "Invoice Parser API", "income": "high", "farm_fit": True, "from_capabilities": ["ocr", "llm"]},
    {"id": "resume_parser_api", "title": "Resume Parser API", "income": "medium", "farm_fit": True, "from_capabilities": ["ocr", "llm"]},
    {"id": "site_monitoring", "title": "Site Monitoring", "income": "medium", "farm_fit": True, "from_capabilities": ["browser"]},
    {"id": "seo_api", "title": "SEO API", "income": "medium", "farm_fit": True, "from_capabilities": ["browser", "llm"]},
    {"id": "contact_extraction_api", "title": "Contact Extraction API", "income": "medium", "farm_fit": True, "from_capabilities": ["browser", "llm"]},
    {"id": "pdf_json_api", "title": "PDF → JSON API", "income": "medium", "farm_fit": True, "from_capabilities": ["ocr", "python"]},
    {"id": "image_classification_api", "title": "Image Classification API", "income": "medium", "farm_fit": True, "from_capabilities": ["vision", "llm"]},
    {"id": "text_classification_api", "title": "Text Classification API", "income": "medium", "farm_fit": True, "from_capabilities": ["llm"]},
    {"id": "translation_api", "title": "Translation API", "income": "medium", "farm_fit": True, "from_capabilities": ["llm"]},
    {"id": "ai_summarization_api", "title": "AI Summarization API", "income": "medium", "farm_fit": True, "from_capabilities": ["llm"]},
    {"id": "company_intelligence_api", "title": "Company Intelligence API", "income": "medium", "farm_fit": True, "from_capabilities": ["browser", "llm"]},
    {"id": "website_screenshot_api", "title": "Website Screenshot API", "income": "medium", "farm_fit": True, "from_capabilities": ["browser"]},
    {"id": "metadata_extraction_api", "title": "Metadata Extraction API", "income": "medium", "farm_fit": True, "from_capabilities": ["python", "llm"]},
    {"id": "price_monitoring", "title": "Price Monitoring Service", "income": "medium", "farm_fit": True, "from_capabilities": ["browser"]},
    {"id": "rss_news_analysis", "title": "RSS / News Analysis", "income": "medium", "farm_fit": True, "from_capabilities": ["python", "llm"]},
    {"id": "product_matching_api", "title": "Product Matching API", "income": "medium", "farm_fit": True, "from_capabilities": ["llm", "python"]},
    {"id": "duplicate_detection", "title": "Duplicate Detection", "income": "medium", "farm_fit": True, "from_capabilities": ["llm", "python"]},
    {"id": "csv_data_cleaning", "title": "CSV/Data Cleaning Service", "income": "medium", "farm_fit": True, "from_capabilities": ["python", "llm"]},
    {"id": "lead_validation", "title": "Lead Validation Service", "income": "medium", "farm_fit": True, "from_capabilities": ["browser", "python"]},
    {"id": "business_report_generator", "title": "Business Report Generator", "income": "high", "farm_fit": True, "from_capabilities": ["llm", "python"]},
)

# Explicit hard-reject catalog (shown to CEO; never research→GO)
HARD_REJECT_CATALOG: tuple[dict[str, str], ...] = (
    {"id": "captcha", "title_ru": "Капчи"},
    {"id": "human_emulation", "title_ru": "Эмуляция человека"},
    {"id": "multi_account", "title_ru": "Мультиаккаунты"},
    {"id": "toloka_performer_bot", "title_ru": "Toloka Performer Bot"},
    {"id": "mturk_bot", "title_ru": "MTurk Bot"},
    {"id": "clickworker_bot", "title_ru": "Clickworker Bot"},
    {"id": "antifraud_bypass", "title_ru": "Обход антифрода"},
)


def factory_model() -> dict[str, Any]:
    """OS of digital services — Capabilities ≠ Composer ≠ Products ≠ Distribution.

    Factory/Composer produce sellable work. Demand is Distribution.
    Money truth is Finance Reality Law → Ledger only.
    """
    return {
        "ok": True,
        "version": FACTORY_MODEL_VERSION,
        "identity_ru": (
            "Virtus = операционная система цифровых сервисов, "
            "не конструктор сайтов и не ферма микрозадач."
        ),
        "north_star_ru": (
            "Capabilities → Composer → Products → Distribution → "
            "Finance Reality → Ledger. Один capability → много продуктов; "
            "один продукт → много каналов — без переписывания продукта."
        ),
        "separation_ru": (
            "OCR/Browser/LLM — способности, не продукты. "
            "Composer собирает сервис. Product продаётся. Distribution — где. "
            "Toloka Requester — Spend capability; Performer-бот — Reject. "
            "Никакой продукт/канал не увеличивает REAL без Hard REAL payout."
        ),
        "value_chain": list(VALUE_CHAIN),
        "can_ru": [
            "Держать каталог Capabilities (что умеет система)",
            "Собирать продукты через Composer (из способностей)",
            "Описывать Digital Products независимо от канала продаж",
            "Подключать Distribution без переписывания продукта",
            "Вести учёт только по Finance Reality Law (Hard REAL)",
        ],
        "cannot_ru": [
            "Считать capability продуктом или доходом",
            "Автоматически генерировать спрос / покупателей (это Distribution)",
            "Превращать Estimate / dry_run в REAL",
            "Подключать Live Earn без Legal + Automation + ROI + Confirmed €",
        ],
        "gap_ru": (
            "Product без Distribution → нет покупателя → 0 €. "
            "Composer и каталог Capabilities готовы как архитектура; "
            "живой автопоток заказов — следующий слой."
        ),
        "layers": [
            {
                "id": "capabilities",
                "title_en": "Capabilities",
                "title_ru": "Способности",
                "note_ru": "Что умеет система. Не продаётся напрямую.",
                "items": list(CAPABILITIES),
            },
            {
                "id": "composer",
                "title_en": "Composer",
                "title_ru": "Composer",
                "note_ru": "Собирает продукт из Capabilities (один → многие).",
                "items": [
                    {
                        "id": f"fanout_{f['capability_id']}",
                        "label": (
                            f"{f['capability_id'].upper()} → "
                            + ", ".join(f["products"][:3])
                            + ("…" if len(f["products"]) > 3 else "")
                        ),
                    }
                    for f in CAPABILITY_PRODUCT_FANOUT
                ],
                "fanout": list(CAPABILITY_PRODUCT_FANOUT),
            },
            {
                "id": "digital_products",
                "title_en": "Digital Products",
                "title_ru": "Цифровые продукты",
                "note_ru": "Что продаётся. Канал не входит в определение продукта.",
                "items": [
                    {
                        "id": p["id"],
                        "title": p["title"],
                        "automation": True,
                        "income": p["income"],
                        "farm_fit": p["farm_fit"],
                        "from_capabilities": list(p.get("from_capabilities") or []),
                    }
                    for p in DIGITAL_PRODUCT_CLASSES
                ],
            },
            {
                "id": "distribution",
                "title_en": "Distribution",
                "title_ru": "Дистрибуция",
                "note_ru": "Где продаётся. См. distribution_model() — группы каналов.",
                "items": [
                    {"id": g["id"], "label": g["title_en"]} for g in DISTRIBUTION_GROUPS
                ],
            },
        ],
        "example_flows_ru": [
            "Capability OCR → Composer → Invoice Parser → RapidAPI + Stripe",
            "Capability Browser → Composer → Website Audit → Website + Agent Marketplace",
            "PDF → OCR+LLM → JSON → Stripe (после Hard REAL)",
        ],
        "hard_reject": list(HARD_REJECT_CATALOG),
        "marketplace_apis_ru": [
            "Website Audit",
            "OCR",
            "Resume Parser",
            "Invoice Parser",
            "Email Extractor",
            "SEO Analyzer",
            "Company Analyzer",
            "Business Report",
            "Product Matcher",
            "AI Classifier",
        ],
    }


def distribution_model() -> dict[str, Any]:
    """Where products sell. Independent of Composer; never mutates REAL alone."""
    return {
        "ok": True,
        "version": DISTRIBUTION_MODEL_VERSION,
        "title_ru": "Distribution — каналы продаж (не сам продукт)",
        "status": "architecture_only",
        "status_ru": "Архитектура · живой автопоток заказов ещё не реализован",
        "independent_of_factory_ru": (
            "Capabilities/Composer/Product производят сервис. "
            "Distribution находит того, кто заплатит. "
            "Один продукт → несколько каналов без переписывания продукта."
        ),
        "search_target_ru": (
            "Искать не клиентов вручную в первую очередь, а платформы, которые "
            "одновременно проходят все критерии Earn Platform Fit."
        ),
        "platform_earn_criteria": list(PLATFORM_EARN_CRITERIA),
        "groups": [
            {
                "id": g["id"],
                "title_en": g["title_en"],
                "title_ru": g["title_ru"],
                "channels": list(g["channels"]),
            }
            for g in DISTRIBUTION_GROUPS
        ],
        "channel_classes": list(DISTRIBUTION_CHANNEL_CLASSES),
        "example_product_channels_ru": (
            "Website Audit → Website · RapidAPI · Agent Marketplace"
        ),
        "value_chain": list(VALUE_CHAIN),
        "value_chain_ru": [
            "Capabilities",
            "Composer",
            "Digital Products",
            "Distribution",
            "Finance Reality Law",
            "Ledger",
        ],
        "without_distribution_ru": "Digital Product → нет покупателя → 0 €",
        "with_distribution_ru": "Digital Product → поток заказов → € (после Hard REAL)",
        "finance_gate_ru": (
            "Никакой канал Distribution не увеличивает REAL, пока нет "
            "подтверждённой внешней выплаты по Finance Reality Law."
        ),
        "next_ru": (
            "Следующий слой: легальная дистрибуция "
            "(Inbound · Marketplace · Partners · M2M) — не микрозадачные боты."
        ),
    }


def platform_earn_fit(passport: dict[str, Any] | None) -> dict[str, Any]:
    """True only when all PLATFORM_EARN_CRITERIA flags are present and true."""
    p = passport if isinstance(passport, dict) else {}
    checks: dict[str, bool] = {}
    for crit in PLATFORM_EARN_CRITERIA:
        cid = crit["id"]
        checks[cid] = bool(p.get(cid))
    ok = all(checks.values())
    return {
        "ok": ok,
        "decision": "fit" if ok else "reject_or_research",
        "checks": checks,
        "missing": [k for k, v in checks.items() if not v],
        "note_ru": (
            "Платформа годится как Earn Channel только при всех четырёх PASS. "
            "Иначе — Reject / только Spend / research без GO."
        ),
    }


# Dual strategy (CEO 2026-08-02): A = first Confirmed € · B = find new Earn markets
FIRST_LIVE_EARN_ID = "earn-own-api-stripe"

# Earn Platform Scanner seeds — markets where a machine may earn legally (not products).
# Criteria flags are research hypotheses until Legal Review stamps them.
_SEED_EARN_PLATFORMS: list[dict[str, Any]] = [
    {
        "id": "platform-own-stripe",
        "title": "Свой API / Digital Product + Stripe",
        "track": "A",
        "first_payout_score": 5,
        "autonomy_score": 5,
        "opinion_ru": "Самый реалистичный и уже частично готов (Path A Stripe).",
        "automation_officially_allowed": True,
        "has_api": True,
        "pays_providers": True,
        "no_forbidden_human_judgment": True,
        "evidence_status": "partially_ready",
        "hard_reject": False,
        "opportunity_id": "earn-own-api-stripe",
    },
    {
        "id": "platform-rapidapi",
        "title": "RapidAPI Hub — API Provider",
        "track": "B",
        "first_payout_score": 4,
        "autonomy_score": 4,
        "opinion_ru": (
            "Авто-публикация при Stripe Live + RAPIDAPI_KEY + "
            "GENESIS_OWNER_AUTO_PUBLISH=1. Иначе — Owner Gate, не вечный pause."
        ),
        "automation_officially_allowed": True,
        "has_api": True,
        "pays_providers": True,
        "no_forbidden_human_judgment": True,
        "evidence_status": "auto_when_armed",
        "hard_reject": False,
        "opportunity_id": "earn-rapidapi-provider",
    },
    {
        "id": "platform-api-market",
        "title": "API.market / аналогичные API-маркетплейсы",
        "track": "B",
        "first_payout_score": 3,
        "autonomy_score": 4,
        "opinion_ru": "Исследовать позже; нужен Legal Review ToS + payout ID.",
        "automation_officially_allowed": False,
        "has_api": True,
        "pays_providers": True,
        "no_forbidden_human_judgment": True,
        "evidence_status": "research_later",
        "hard_reject": False,
        "opportunity_id": None,
    },
    {
        "id": "platform-toloka-performer",
        "title": "Toloka Performer Bot",
        "track": "reject",
        "first_payout_score": 0,
        "autonomy_score": 0,
        "opinion_ru": "Не подходит по правилам и рискам (human judgment / ToS).",
        "automation_officially_allowed": False,
        "has_api": True,
        "pays_providers": True,
        "no_forbidden_human_judgment": False,
        "evidence_status": "hard_reject",
        "hard_reject": True,
        "opportunity_id": "reject-toloka-performer-bot",
    },
    {
        "id": "platform-captcha-human-bot",
        "title": "Капчи / human-bot",
        "track": "reject",
        "first_payout_score": 0,
        "autonomy_score": 0,
        "opinion_ru": "Исключить полностью.",
        "automation_officially_allowed": False,
        "has_api": False,
        "pays_providers": False,
        "no_forbidden_human_judgment": False,
        "evidence_status": "hard_reject",
        "hard_reject": True,
        "opportunity_id": "reject-captcha-farm",
    },
]


def dual_track_strategy() -> dict[str, Any]:
    """NOW = Commercial Micro/Stripe · Farm Scanner = unfinished north-star loop."""
    return {
        "ok": True,
        "architecture_ready_ru": (
            "Commercial Engine умеет продавать, если есть лиды. "
            "Farm Engine ещё не умеет сам найти рынок с уже оплачиваемой работой — "
            "это главный незавершённый элемент исходной идеи. "
            "Ограничение часто задаёт рынок (мало платформ: автомат + платят), не код."
        ),
        "strategic_question_ru": (
            "Сейчас: как получить 1 API-покупателя (Micro 5 €)? "
            "Параллельно: какие легальные Earn-платформы Scanner нашёл?"
        ),
        "priority_now_ru": (
            "/api-access → Micro 5 € → Stripe → API Key → 1 покупатель → REAL > 0. "
            "RapidAPI: авто при Stripe Live + token + GENESIS_OWNER_AUTO_PUBLISH=1."
        ),
        "first_live_earn_id": FIRST_LIVE_EARN_ID,
        "first_live_earn_choice_ru": "Virtus API + Stripe Micro 5 € (короткий путь)",
        "farm_loop_ru": [
            "Интернет",
            "искать легальные источники оплачиваемой цифровой работы",
            "проверить ToS",
            "проверить автоматизацию",
            "проверить API",
            "если подходит → предложить Earn Connector",
            "заказ → выполнить → External Payout ID → REAL",
        ],
        "commercial_loop_ru": [
            "Virtus API",
            "Stripe",
            "Micro 5 €",
            "Country Desk / /api-access",
            "первые продажи",
            "Hard REAL",
        ],
        "farm_may_ru": [
            "искать официальные платформы и маркетплейсы",
            "отслеживать заказы на уже подключённых платформах",
            "оценивать ROI задачи",
            "выполнять работу, если платформа разрешает автоматизацию",
            "фиксировать подтверждённые выплаты (Hard REAL)",
        ],
        "farm_must_not_ru": [
            "обходить правила платформ",
            "регистрировать аккаунты за владельца",
            "human-only микрозадачи ботом",
            "мультиаккаунты / обход антифрода",
        ],
        "tracks": [
            {
                "id": "commercial_now",
                "title_ru": "Вариант B — Commercial NOW (короткий путь)",
                "goal_ru": (
                    "Первый подтверждённый платёж: Micro 5 € → Stripe → API key. "
                    "Доказать Finance Reality / Ledger на реальных деньгах."
                ),
                "focus_ru": "/api-access · Country Desk dual offer · не ждать Farm Earn",
                "not_ru": "Не Toloka cents. RapidAPI — только с Owner Auto Mode.",
                "status": "primary",
            },
            {
                "id": "farm_scanner",
                "title_ru": "Farm Opportunity Scanner — исходная мечта (незавершено)",
                "goal_ru": (
                    "Не ждать клиента: искать легальные оплачиваемые цифровые задания, "
                    "которые разрешено выполнять автоматически; после Earn Connector — "
                    "брать заказы сама."
                ),
                "focus_ru": (
                    "Интернет → ToS → automation → API → предложить Connector. "
                    "Главная сложность — есть ли такие платформы на рынке."
                ),
                "not_ru": "Не продажа Website/API через Country Desk (это Commercial).",
                "status": "research_gap",
            },
        ],
        "do_not_ru": [
            "RapidAPI без Owner Auto Mode / без Live Stripe (вечный ceo_required)",
            "Ждать € от Toloka Pipeline (это Spend)",
            "Toloka Performer / капчи / human-bot",
            "Путать Commercial dual-offer с Farm Earn",
        ],
        "north_star_ru": (
            "Ферма не ждёт клиента — ищет легальную оплачиваемую авто-работу. "
            "Пока таких Connectors нет, короткий путь к REAL = Micro 5 € + Stripe."
        ),
        "gap_ru": (
            "Farm Market Scanner мониторит рынки (Reject/Research/GO) и честно говорит, "
            "когда подходящих Earn-платформ нет. Он не создаёт рынок. "
            "Commercial закрывает продажи своим лидам (Micro/Stripe)."
        ),
        "scanner_goal_ru": (
            "Ферма должна сама искать новые легальные цифровые рынки, на которых "
            "разрешено автоматическое выполнение работы, и предлагать подключить их "
            "как Earn Connector."
        ),
    }


def scan_earn_platforms(
    extra: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Direction B — score Earn markets (not product SKUs)."""
    rows: list[dict[str, Any]] = []
    catalog = list(_SEED_EARN_PLATFORMS) + list(extra or [])
    for raw in catalog:
        plat = dict(raw)
        fit = platform_earn_fit(plat)
        if plat.get("hard_reject"):
            stage = "hard_reject"
        elif fit["ok"] and plat.get("evidence_status") == "partially_ready":
            stage = "first_connector_candidate"
        elif fit["ok"]:
            stage = "research_fit"
        elif plat.get("evidence_status") == "research_later":
            stage = "research_later"
        else:
            stage = "reject_or_incomplete"
        rows.append(
            {
                **plat,
                "earn_fit": fit,
                "pipeline_stage": stage,
                "is_first_pick": plat.get("opportunity_id") == FIRST_LIVE_EARN_ID,
            }
        )
    rows.sort(
        key=lambda x: (
            0 if x.get("is_first_pick") else 1,
            0 if x["pipeline_stage"] == "first_connector_candidate" else 1,
            0 if x["pipeline_stage"] == "research_fit" else 1,
            -int(x.get("first_payout_score") or 0),
            -int(x.get("autonomy_score") or 0),
        )
    )
    return {
        "ok": True,
        "title_ru": "Earn Platform Scanner — легальные рынки (не продукты)",
        "criteria": list(PLATFORM_EARN_CRITERIA),
        "law_ru": (
            "Ищем платформы с 4× PASS. Toloka Requester = Spend, не Earn. "
            "Hard reject: performer-боты / капчи."
        ),
        "platforms": rows,
        "counts": {
            "total": len(rows),
            "fit": sum(1 for r in rows if r["earn_fit"]["ok"] and not r.get("hard_reject")),
            "hard_reject": sum(1 for r in rows if r.get("hard_reject")),
            "first_pick": sum(1 for r in rows if r.get("is_first_pick")),
        },
    }


# Seed catalog — research candidates (not live connectors).
_SEED_OPPORTUNITIES: list[dict[str, Any]] = [
    {
        "id": "earn-own-api-stripe",
        "title": "Own API + Stripe (agent/client paid endpoints)",
        "kind": "earn_api_product",
        "source_class": "own_product",
        "track": "A",
        "first_live_earn": True,
        "description_ru": (
            "Продажа цифровых сервисов (анализ сайтов, документы, отчёты) "
            "через собственный API с оплатой Stripe. "
            "Первый Live Earn Connector (Направление A)."
        ),
        "tos_automation": "allowed",
        "legal_notes_ru": "Вы — merchant; автоматизация = продукт. Path A Stripe уже есть.",
        "est_revenue_eur_per_job": 5.0,
        "est_cost_eur_per_job": 0.4,
        "payout_path": "stripe_bank",
        "capabilities": ["site_analysis", "documents", "reports", "api"],
        "rank_hint": 1,
    },
    {
        "id": "earn-rapidapi-provider",
        "title": "RapidAPI Hub — API Provider",
        "kind": "earn_marketplace_api",
        "source_class": "marketplace",
        "track": "B",
        "first_live_earn": False,
        "description_ru": (
            "RapidAPI Provider: после Stripe Live + RAPIDAPI_KEY + "
            "GENESIS_OWNER_AUTO_PUBLISH=1 публикация идёт автоматически "
            "(не вечный ceo_required). Иначе — Owner Gate."
        ),
        "tos_automation": "allowed",
        "legal_notes_ru": (
            "Auto-publish when Owner Auto Mode armed. "
            "First-time ToS / payouts may still need owner once."
        ),
        "est_revenue_eur_per_job": 0.15,
        "est_cost_eur_per_job": 0.03,
        "payout_path": "rapidapi_paypal",
        "capabilities": ["api", "ocr", "classification"],
        "rank_hint": 40,
        "ceo_priority": "auto_when_armed",
    },
    {
        "id": "work-document-extract",
        "title": "Document extract / OCR reports (B2B service)",
        "kind": "execution_service",
        "source_class": "b2b_service",
        "description_ru": (
            "Извлечение данных из документов, OCR, структурированные отчёты — "
            "как платная услуга (Stripe / invoice)."
        ),
        "tos_automation": "allowed",
        "legal_notes_ru": "Собственная услуга; нет чужой ToS на «человека в UI».",
        "est_revenue_eur_per_job": 25.0,
        "est_cost_eur_per_job": 1.5,
        "payout_path": "stripe_bank",
        "capabilities": ["ocr", "documents", "reports"],
        "rank_hint": 3,
    },
    {
        "id": "work-site-monitor",
        "title": "Site change monitoring + alerts",
        "kind": "execution_service",
        "source_class": "b2b_service",
        "description_ru": "Мониторинг изменений сайтов / цен / контента с отчётами.",
        "tos_automation": "allowed",
        "legal_notes_ru": "Собственный продукт; публичные страницы по правилам целевого сайта.",
        "est_revenue_eur_per_job": 12.0,
        "est_cost_eur_per_job": 0.2,
        "payout_path": "stripe_bank",
        "capabilities": ["site_analysis", "monitoring", "reports"],
        "rank_hint": 4,
    },
    {
        "id": "reject-toloka-performer-bot",
        "title": "Toloka Performer (unsupervised bot)",
        "kind": "human_microtask_bot",
        "source_class": "crowdsourcing_performer",
        "description_ru": (
            "Автоматическое выполнение человеческих микрозадач на Toloka. "
            "Отклонено: ToS / human judgment; не Earn Connector v1."
        ),
        "tos_automation": "forbidden",
        "legal_notes_ru": "Hard reject — не строить.",
        "est_revenue_eur_per_job": 0.05,
        "est_cost_eur_per_job": 0.02,
        "payout_path": "none",
        "capabilities": [],
        "rank_hint": 99,
    },
    {
        "id": "reject-captcha-farm",
        "title": "Captcha / anti-fraud bypass farm",
        "kind": "captcha",
        "source_class": "evasion",
        "description_ru": "Обход капч и антифрода. Запрещено.",
        "tos_automation": "forbidden",
        "legal_notes_ru": "Hard reject.",
        "est_revenue_eur_per_job": 0.01,
        "est_cost_eur_per_job": 0.0,
        "payout_path": "none",
        "capabilities": [],
        "rank_hint": 99,
    },
    {
        "id": "reject-mturk-performer-bot",
        "title": "MTurk Performer Bot",
        "kind": "mturk_performer_bot",
        "source_class": "crowdsourcing_performer",
        "description_ru": "Бот-исполнитель на MTurk. Hard reject.",
        "tos_automation": "forbidden",
        "legal_notes_ru": "Hard reject — не строить.",
        "est_revenue_eur_per_job": 0.02,
        "est_cost_eur_per_job": 0.01,
        "payout_path": "none",
        "capabilities": [],
        "rank_hint": 99,
    },
    {
        "id": "reject-clickworker-bot",
        "title": "Clickworker Bot",
        "kind": "clickworker_bot",
        "source_class": "crowdsourcing_performer",
        "description_ru": "Бот-исполнитель Clickworker. Hard reject.",
        "tos_automation": "forbidden",
        "legal_notes_ru": "Hard reject — не строить.",
        "est_revenue_eur_per_job": 0.02,
        "est_cost_eur_per_job": 0.01,
        "payout_path": "none",
        "capabilities": [],
        "rank_hint": 99,
    },
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def legal_check(opportunity: dict[str, Any]) -> dict[str, Any]:
    """Legal gate — company/work kind, not platform politics theater."""
    kind = str(opportunity.get("kind") or "").strip().lower()
    tos = str(opportunity.get("tos_automation") or "unknown").strip().lower()
    blockers: list[str] = []
    if kind in _FORBIDDEN_WORK_KINDS:
        blockers.append(f"forbidden_kind:{kind}")
    if tos in ("forbidden", "restricted"):
        if tos == "forbidden" or kind in _FORBIDDEN_WORK_KINDS:
            blockers.append(f"tos:{tos}")
    ok = not blockers
    return {
        "ok": ok,
        "decision": "pass" if ok else "reject",
        "blockers": blockers,
        "tos_automation": tos,
        "notes_ru": str(opportunity.get("legal_notes_ru") or ""),
    }


def roi_check(opportunity: dict[str, Any]) -> dict[str, Any]:
    """Simple profit check: est revenue − est cost per job."""
    rev = float(opportunity.get("est_revenue_eur_per_job") or 0)
    cost = float(opportunity.get("est_cost_eur_per_job") or 0)
    profit = round(rev - cost, 4)
    margin = round((profit / rev) * 100.0, 1) if rev > 0 else 0.0
    ok = profit > 0 and rev > 0
    return {
        "ok": ok,
        "est_revenue_eur": rev,
        "est_cost_eur": cost,
        "est_profit_eur": profit,
        "est_margin_pct": margin,
        "decision": "pass" if ok else "reject",
        "reason_ru": (
            f"Прибыль ≈ {profit} €/job ({margin}%)"
            if ok
            else "Нулевая/отрицательная оценка прибыли"
        ),
    }


class FarmEngineV1:
    def __init__(self, memory_dir: Path | None) -> None:
        self._memory = Path(memory_dir) if memory_dir else None

    def _state_path(self) -> Path | None:
        return (self._memory / STATE_FILE) if self._memory else None

    def _load_state(self) -> dict[str, Any]:
        empty = {
            "version": 1,
            "mode": "research_dry_run",
            "decisions": {},  # opportunity_id → go|reject|hold|research
            "execution_plans": {},  # opportunity_id → plan snapshot
            "updated_at": None,
        }
        path = self._state_path()
        if not path or not path.is_file():
            return empty
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return empty
        if not isinstance(data, dict):
            return empty
        data.setdefault("decisions", {})
        data.setdefault("execution_plans", {})
        data.setdefault("mode", "research_dry_run")
        data.setdefault("version", 1)
        return data

    def _save_state(self, state: dict[str, Any]) -> None:
        path = self._state_path()
        if not path:
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        state["updated_at"] = _utc_now()
        path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

    def _append_jsonl(self, filename: str, row: dict[str, Any]) -> None:
        if not self._memory:
            return
        path = self._memory / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    def scan(self) -> dict[str, Any]:
        """Opportunity Scanner — legal + ROI scored research candidates."""
        state = self._load_state()
        decisions = state.get("decisions") if isinstance(state.get("decisions"), dict) else {}
        plans = (
            state.get("execution_plans")
            if isinstance(state.get("execution_plans"), dict)
            else {}
        )
        items: list[dict[str, Any]] = []
        for raw in _SEED_OPPORTUNITIES:
            opp = dict(raw)
            legal = legal_check(opp)
            roi = roi_check(opp)
            ceo = str(decisions.get(opp["id"]) or "research")
            plan = plans.get(opp["id"]) if isinstance(plans.get(opp["id"]), dict) else None
            pipeline_ok = bool(legal["ok"] and roi["ok"])
            stage = "rejected"
            if not legal["ok"]:
                stage = "legal_reject"
            elif not roi["ok"]:
                stage = "roi_reject"
            elif ceo == "go" and plan:
                st = str(plan.get("stage") or "")
                if st == "blocked":
                    stage = "execution_blocked"
                elif st == "waiting_for_ceo":
                    stage = "waiting_for_ceo"
                elif st == "ready_for_production":
                    stage = "production_ready"
                else:
                    stage = "execution_plan"
            elif ceo == "go":
                stage = "execution_ready"
            elif ceo == "reject":
                stage = "ceo_reject"
            elif ceo == "hold":
                stage = "hold"
            else:
                stage = "research"
            items.append(
                {
                    **opp,
                    "legal": legal,
                    "roi": roi,
                    "ceo_decision": ceo,
                    "pipeline_stage": stage,
                    "can_enqueue": pipeline_ok and ceo == "go",
                    "execution_plan": plan,
                }
            )
        items.sort(
            key=lambda x: (
                0 if x["pipeline_stage"] == "execution_ready" else 1,
                0 if x["legal"]["ok"] and x["roi"]["ok"] else 1,
                int(x.get("rank_hint") or 50),
            )
        )
        strategy = dual_track_strategy()
        platforms = scan_earn_platforms(
            extra=list(state.get("extra_earn_platforms") or [])
            if isinstance(state.get("extra_earn_platforms"), list)
            else None
        )
        return {
            "ok": True,
            "engine": "farm_v1",
            "title_ru": "Farm Engine v1 — Opportunity Scanner",
            "law_ru": (
                "Только легальная цифровая работа. "
                "Капчи / human-microtask боты / обход ToS — reject. "
                "A: первый Confirmed € (свой API+Stripe). "
                "B: искать новые легальные Earn-платформы."
            ),
            "mode": state.get("mode") or "research_dry_run",
            "strategy": strategy,
            "earn_platforms": platforms,
            "opportunities": items,
            "counts": {
                "total": len(items),
                "legal_pass": sum(1 for i in items if i["legal"]["ok"]),
                "roi_pass": sum(1 for i in items if i["roi"]["ok"]),
                "execution_ready": sum(1 for i in items if i["pipeline_stage"] == "execution_ready"),
                "legal_reject": sum(1 for i in items if i["pipeline_stage"] == "legal_reject"),
            },
            "updated_at": state.get("updated_at"),
        }

    def register_earn_platform_research(
        self, passport: dict[str, Any]
    ) -> dict[str, Any]:
        """Direction B — CEO/agent adds a research platform passport (no Live Earn)."""
        pid = str(passport.get("id") or "").strip()
        if not pid:
            return {"ok": False, "error": "id_required"}
        if passport.get("hard_reject") or str(passport.get("track") or "") == "reject":
            return {"ok": False, "error": "hard_reject_not_registered"}
        state = self._load_state()
        extra = list(state.get("extra_earn_platforms") or [])
        # upsert by id
        extra = [e for e in extra if isinstance(e, dict) and e.get("id") != pid]
        row = {
            "id": pid,
            "title": str(passport.get("title") or pid)[:120],
            "track": "B",
            "first_payout_score": int(passport.get("first_payout_score") or 2),
            "autonomy_score": int(passport.get("autonomy_score") or 2),
            "opinion_ru": str(passport.get("opinion_ru") or "Research candidate")[:300],
            "automation_officially_allowed": bool(
                passport.get("automation_officially_allowed")
            ),
            "has_api": bool(passport.get("has_api")),
            "pays_providers": bool(passport.get("pays_providers")),
            "no_forbidden_human_judgment": bool(
                passport.get("no_forbidden_human_judgment")
            ),
            "evidence_status": str(
                passport.get("evidence_status") or "research_hypothesis"
            )[:40],
            "hard_reject": False,
            "opportunity_id": passport.get("opportunity_id"),
        }
        extra.append(row)
        state["extra_earn_platforms"] = extra[-50:]
        self._save_state(state)
        return {
            "ok": True,
            "registered": row,
            "earn_platforms": scan_earn_platforms(extra=extra),
        }

    def decide(self, opportunity_id: str, decision: str, *, note: str = "") -> dict[str, Any]:
        """CEO: go | reject | hold | research.

        GO runs Execution Plan (checklist + auto tasks) — not «money starts».
        """
        decision = str(decision or "").strip().lower()
        if decision not in ("go", "reject", "hold", "research"):
            return {"ok": False, "error": "invalid_decision", "allowed": ["go", "reject", "hold", "research"]}
        opp = next((x for x in _SEED_OPPORTUNITIES if x["id"] == opportunity_id), None)
        if not opp:
            return {"ok": False, "error": "unknown_opportunity"}
        legal = legal_check(opp)
        roi = roi_check(opp)
        if decision == "go" and not (legal["ok"] and roi["ok"]):
            return {
                "ok": False,
                "error": "cannot_go",
                "message_ru": "GO только если Legal PASS и ROI PASS",
                "legal": legal,
                "roi": roi,
            }
        state = self._load_state()
        decisions = dict(state.get("decisions") or {})
        decisions[opportunity_id] = decision
        state["decisions"] = decisions
        plan: dict[str, Any] | None = None
        job: dict[str, Any] | None = None
        if decision == "go":
            from swarm.farm_execution_plan import run_execution_plan

            plan = run_execution_plan(opp, memory_dir=self._memory)
            plans = dict(state.get("execution_plans") or {})
            plans[opportunity_id] = plan
            state["execution_plans"] = plans
            # Auto-queue so GO is visibly more than a status flip
            job = {
                "job_id": f"fj-{uuid.uuid4().hex[:12]}",
                "at": _utc_now(),
                "opportunity_id": opportunity_id,
                "title": opp.get("title"),
                "status": str(plan.get("stage") or "execution_plan"),
                "mode": "execution_plan",
                "note": str(note or "auto after GO")[:300],
                "plan_id": plan.get("plan_id"),
                "est_profit_eur": roi.get("est_profit_eur"),
            }
            self._append_jsonl(QUEUE_FILE, job)
        elif decision in ("reject", "research", "hold"):
            plans = dict(state.get("execution_plans") or {})
            plans.pop(opportunity_id, None)
            state["execution_plans"] = plans
        self._save_state(state)
        event = {
            "at": _utc_now(),
            "opportunity_id": opportunity_id,
            "decision": decision,
            "note": str(note or "")[:300],
        }
        self._append_jsonl(DECISIONS_FILE, event)
        out: dict[str, Any] = {"ok": True, **event, "scan": self.scan()}
        if plan is not None:
            out["execution_plan"] = plan
            out["message_ru"] = (
                f"GO → Execution Plan ({plan.get('stage')}). "
                f"{plan.get('why_no_eur_ru') or ''}"
            ).strip()
        if job is not None:
            out["job"] = job
        return out

    def run_plan(self, opportunity_id: str) -> dict[str, Any]:
        """Re-run Execution Plan for an opportunity already on GO."""
        state = self._load_state()
        if str((state.get("decisions") or {}).get(opportunity_id) or "") != "go":
            return {
                "ok": False,
                "error": "need_go",
                "message_ru": "Сначала CEO GO — затем Execution Plan",
            }
        opp = next((x for x in _SEED_OPPORTUNITIES if x["id"] == opportunity_id), None)
        if not opp:
            return {"ok": False, "error": "unknown_opportunity"}
        from swarm.farm_execution_plan import run_execution_plan

        plan = run_execution_plan(opp, memory_dir=self._memory)
        plans = dict(state.get("execution_plans") or {})
        plans[opportunity_id] = plan
        state["execution_plans"] = plans
        self._save_state(state)
        return {"ok": True, "execution_plan": plan, "scan": self.scan()}

    def market_monitor(self, *, force: bool = False) -> dict[str, Any]:
        """Daily Farm Market Scanner digest (honest empty market OK)."""
        from swarm.farm_market_scanner import load_latest_digest, run_market_monitor

        state = self._load_state()
        extra = (
            list(state.get("extra_earn_platforms") or [])
            if isinstance(state.get("extra_earn_platforms"), list)
            else []
        )
        if not force:
            cached = load_latest_digest(self._memory)
            if cached and cached.get("ok"):
                return {**cached, "from_cache": True}
        digest = run_market_monitor(self._memory, extra_platforms=extra)
        digest["from_cache"] = False
        return digest

    def enqueue(self, opportunity_id: str, *, note: str = "") -> dict[str, Any]:
        """Queue after GO — prefers Execution Plan stage over empty dry_run."""
        scan = self.scan()
        item = next(
            (x for x in scan["opportunities"] if x["id"] == opportunity_id),
            None,
        )
        if not item:
            return {"ok": False, "error": "unknown_opportunity"}
        if not item.get("can_enqueue"):
            return {
                "ok": False,
                "error": "not_execution_ready",
                "message_ru": "Нужны Legal PASS + ROI PASS + CEO GO",
                "pipeline_stage": item.get("pipeline_stage"),
            }
        plan = item.get("execution_plan") if isinstance(item.get("execution_plan"), dict) else None
        if not plan:
            from swarm.farm_execution_plan import run_execution_plan

            plan = run_execution_plan(item, memory_dir=self._memory)
            state = self._load_state()
            plans = dict(state.get("execution_plans") or {})
            plans[opportunity_id] = plan
            state["execution_plans"] = plans
            self._save_state(state)
        job = {
            "job_id": f"fj-{uuid.uuid4().hex[:12]}",
            "at": _utc_now(),
            "opportunity_id": opportunity_id,
            "title": item.get("title"),
            "status": str(plan.get("stage") or "execution_plan"),
            "mode": "execution_plan",
            "note": str(note or "")[:300],
            "plan_id": plan.get("plan_id"),
            "est_profit_eur": (item.get("roi") or {}).get("est_profit_eur"),
        }
        self._append_jsonl(QUEUE_FILE, job)
        return {"ok": True, "job": job, "execution_plan": plan}

    def queue(self, *, limit: int = 40) -> dict[str, Any]:
        rows: list[dict[str, Any]] = []
        if self._memory:
            path = self._memory / QUEUE_FILE
            if path.is_file():
                for line in path.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rows.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        rows = rows[-max(1, min(int(limit), 200)) :]
        return {
            "ok": True,
            "jobs": list(reversed(rows)),
            "count": len(rows),
            "note_ru": (
                "Очередь = Execution Plan после GO (checklist / auto tasks). "
                "Не Confirmed €. Live Earn / Owner Gate — отдельно."
            ),
        }

    def ledger_snapshot(self) -> dict[str, Any]:
        """Profit Ledger view — Farm-tagged + confirmed finance facts (read-only)."""
        confirmed = 0.0
        pending = 0.0
        entries_n = 0
        if self._memory:
            try:
                from swarm.finance_ledger import FinanceLedger
                from swarm.revenue_source import (
                    CONFIDENCE_CONFIRMED,
                    CONFIDENCE_BOOKED,
                    CONFIDENCE_PENDING,
                    is_withdrawable_confidence,
                )

                ledger = FinanceLedger(self._memory)
                for entry in ledger.list_entries(limit=200) or []:
                    if not isinstance(entry, dict):
                        continue
                    entries_n += 1
                    amt = float(entry.get("amount") or entry.get("amount_eur") or 0)
                    conf = str(entry.get("confidence") or "")
                    if is_withdrawable_confidence(conf) or conf in (
                        CONFIDENCE_CONFIRMED,
                        CONFIDENCE_BOOKED,
                    ):
                        confirmed += amt
                    elif conf == CONFIDENCE_PENDING:
                        pending += amt
            except Exception:
                pass
        return {
            "ok": True,
            "title_ru": "Farm Profit Ledger",
            "entries_scanned": entries_n,
            "confirmed_eur": round(confirmed, 2),
            "pending_eur": round(pending, 2),
            "formula_ru": "REAL PROFIT = Revenue − Execution − Infrastructure (на операции)",
            "note_ru": (
                "v1 читает существующий Finance Ledger. "
                "Path A Stripe остаётся Commercial Engine — не смешивать в UI как «доход фермы»."
            ),
        }

    def maturity_board(self) -> dict[str, Any]:
        """CEO maturity + Live gates — architecture ≠ Confirmed €."""
        scan = self.scan()
        q = self.queue(limit=50)
        led = self.ledger_snapshot()
        decisions = (self._load_state().get("decisions") or {})
        research_n = sum(
            1
            for o in scan["opportunities"]
            if o.get("ceo_decision") == "research"
            and o["legal"]["ok"]
            and o["roi"]["ok"]
        )
        go_n = sum(1 for d in decisions.values() if d == "go")
        prototype_n = int(q.get("count") or 0)
        confirmed_eur = float(led.get("confirmed_eur") or 0)
        confirmed_pass = confirmed_eur > 0

        levels = [
            {
                "id": "commercial_path_a",
                "title_ru": "Commercial Engine (Path A)",
                "status": "awaiting_kpi",
                "status_ru": "🟡 Ждёт KPI после сброса Places",
                "detail_ru": "Places → Ready → Email → Stripe. Freeze до реальных метрик.",
            },
            {
                "id": "farm_engine_v1",
                "title_ru": "Farm Engine v1",
                "status": "architecture_ready",
                "status_ru": "✅ Архитектура готова",
                "detail_ru": "Scanner → Legal → ROI → CEO → dry_run. Это не Confirmed €.",
            },
            {
                "id": "farm_earn",
                "title_ru": "Farm Earn (коммерция)",
                "status": "no_confirmed_eur" if not confirmed_pass else "commercial",
                "status_ru": (
                    "⛔ Нет Confirmed € — только research"
                    if not confirmed_pass
                    else f"✅ Confirmed €: {confirmed_eur:.2f}"
                ),
                "detail_ru": (
                    "Оценки Toloka / dry_run / потенциал ≠ REAL. "
                    "Коммерческой ферма становится только после внешней подтверждённой выплаты."
                ),
            },
        ]

        # Live Connector gates (all four required).
        live_gates = [
            {
                "id": "legal",
                "title_ru": "Legal PASS",
                "ok": True,
                "note_ru": "Gate на каждой возможности (captcha / human-bot → Reject)",
            },
            {
                "id": "automation",
                "title_ru": "Automation PASS",
                "ok": True,
                "note_ru": "tos_automation=allowed; Full machine work only",
            },
            {
                "id": "roi",
                "title_ru": "ROI PASS",
                "ok": True,
                "note_ru": "est profit > 0 на кандидате перед GO",
            },
            {
                "id": "confirmed_eur",
                "title_ru": "Confirmed € PASS",
                "ok": confirmed_pass,
                "note_ru": (
                    f"Есть подтверждённая выплата ({confirmed_eur:.2f} €)"
                    if confirmed_pass
                    else "Пока нет · оценки 0.05/0.15 € — не выплата"
                ),
            },
        ]
        live_ready = all(bool(g["ok"]) for g in live_gates)

        kpi = {
            "research": research_n,
            "go": go_n,
            "prototype": prototype_n,
            "confirmed_eur": confirmed_eur,
            "funnel_ru": ["Research", "GO", "Prototype", "Confirmed €"],
            "commercial_when_ru": (
                "Первый Confirmed € (любая сумма) с Connector + Job ID + External payout ID "
                "→ ферма перестаёт быть только исследовайской."
            ),
        }

        factory = factory_model()
        distribution = distribution_model()
        # Law №3 — until Live Earn + confirmed payouts, everything is modeling
        try:
            from swarm.finance_reality_law import income_phase

            phase = income_phase(
                live_earn_connector=False,  # no live Earn adapter in v1
                legal_review_pass=bool(
                    next((g["ok"] for g in live_gates if g["id"] == "legal"), False)
                ),
                confirmed_external_payouts=confirmed_pass,
            )
        except Exception:
            phase = {
                "phase": "modeling",
                "is_modeling": True,
                "real_income_possible": False,
                "law_ru": (
                    "Реальный доход возможен только после Live Earn Connector "
                    "с Legal Review и подтверждёнными внешними выплатами. "
                    "До этого все оценки — моделирование."
                ),
            }

        # Why REAL=0 — farm is before Law №3; Commercial NOW = Micro path
        commercial_blocker = {
            "ok": True,
            "question_wrong_ru": "Почему REAL = 0?",
            "question_right_ru": (
                "Как провести 1 покупателя Micro 5 € через /api-access + Stripe "
                "(и параллельно — какие Earn-платформы Scanner нашёл)?"
            ),
            "why_real_zero_ru": (
                "Нет ни первого Stripe Micro платежа, ни Live Earn Connector с payout. "
                "Toloka Pipeline = Spend. Farm Scanner ещё не нашёл чужой рынок "
                "«уже платят за авто-работу». RapidAPI — на паузе."
            ),
            "checklist": [
                {"id": "legal", "title_ru": "Legal PASS", "ok": True},
                {"id": "roi", "title_ru": "ROI PASS", "ok": True},
                {"id": "scanner", "title_ru": "Earn Platform Scanner", "ok": True},
                {
                    "id": "execution_plan",
                    "title_ru": "Execution Plan после GO",
                    "ok": True,
                },
                {
                    "id": "micro_stripe_buyer",
                    "title_ru": "1× Micro 5 € покупатель",
                    "ok": False,
                },
                {
                    "id": "live_earn_connector",
                    "title_ru": "Live Earn Connector (чужой рынок)",
                    "ok": False,
                },
                {
                    "id": "external_payout_id",
                    "title_ru": "External Payout ID",
                    "ok": confirmed_pass,
                },
                {
                    "id": "real_eur",
                    "title_ru": "REAL €",
                    "ok": confirmed_pass,
                    "value_eur": confirmed_eur,
                },
            ],
            "not_earn_ru": [
                {
                    "id": "toloka_pipeline",
                    "title_ru": "Toloka Pipeline API v2",
                    "role": "requester_spend",
                    "note_ru": (
                        "Pipeline OK = dataset принят. Не Live Earn. "
                        "Не источник центов/евро для Virtus."
                    ),
                },
                {
                    "id": "rapidapi_now",
                    "title_ru": "RapidAPI (сейчас)",
                    "role": "paused",
                    "note_ru": "Не приоритет до первого Micro/Stripe Confirmed €.",
                },
            ],
            "first_live_earn_candidates": [
                {
                    "id": "earn-own-api-stripe",
                    "title_ru": "Virtus API + Stripe Micro 5 €",
                    "why_ru": (
                        "Короткий путь NOW: /api-access → оплата → key → REAL. "
                        "Country Desk может слать API-оффер."
                    ),
                    "status": "first_pick",
                    "first_payout_score": 5,
                    "autonomy_score": 5,
                },
            ],
            "next_ru": (
                "NOW: довести Micro 5 € до первого Hard REAL. "
                "Параллельно: Farm Scanner ищет легальные Earn-платформы (не RapidAPI). "
                "Не ждать, что GO по каталогу сам принесёт центы с интернета."
            ),
        }

        strategy = dual_track_strategy()
        platforms = scan_earn_platforms()
        market = self.market_monitor(force=False)
        return {
            "ok": True,
            "title_ru": "Зрелость · Commercial vs Farm vs Earn",
            "law_ru": (
                "Два проекта: Commercial (лиды→Stripe) работает; "
                "Farm Scanner ищет легальные Earn-рынки и честно говорит, когда их нет. "
                "NOW: Micro 5 €. RapidAPI на паузе."
            ),
            "levels": levels,
            "live_gates": live_gates,
            "live_connector_allowed": live_ready,
            "kpi": kpi,
            "factory": factory,
            "distribution": distribution,
            "strategy": strategy,
            "earn_platforms": platforms,
            "market_digest": market,
            "income_phase": phase,
            "commercial_blocker": commercial_blocker,
            "estimate_vs_real_ru": (
                "Toloka «≈0.05 € · ожидает подтверждения» было ложным ожиданием Earn: "
                "это Spend/Requester. Пока нет Live Earn Connector — все оценки = "
                "моделирование. REAL только с External Payout ID (Hard REAL)."
            ),
        }

    def panel(self) -> dict[str, Any]:
        """CEO one-glance Farm Engine v1."""
        scan = self.scan()
        q = self.queue(limit=15)
        led = self.ledger_snapshot()
        maturity = self.maturity_board()
        factory = factory_model()
        distribution = distribution_model()
        strategy = dual_track_strategy()
        return {
            "ok": True,
            "engine": "farm_v1",
            "pipeline_ru": [
                "Opportunity Scanner",
                "Legal / ROI",
                "CEO GO",
                "Execution Plan",
                "Checklist / Auto Tasks",
                "Waiting for CEO",
                "Production-ready",
                "Confirmed € (Hard REAL)",
            ],
            "factory_layers_ru": [
                "Capabilities",
                "Composer",
                "Digital Products",
                "Distribution",
                "Finance Reality",
                "Ledger",
            ],
            "strategy": strategy,
            "factory": factory,
            "distribution": distribution,
            "maturity": maturity,
            "scan": scan,
            "earn_platforms": scan.get("earn_platforms") or scan_earn_platforms(),
            "market_digest": self.market_monitor(force=False),
            "queue": q,
            "ledger": led,
            "forbidden_ru": [
                "Капчи и обход антифрода",
                "Боты на human-only микрозадачах (Toloka / MTurk / Clickworker)",
                "Мультиаккаунты / эмуляция человека",
            ],
        }
