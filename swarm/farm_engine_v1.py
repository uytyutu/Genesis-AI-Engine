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
        "opinion_ru": "Хороший второй канал после первого Confirmed €.",
        "automation_officially_allowed": True,
        "has_api": True,
        "pays_providers": True,
        "no_forbidden_human_judgment": True,
        "evidence_status": "research_hypothesis",
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
    """A = commercial first € · B = continuous Earn-market discovery."""
    return {
        "ok": True,
        "architecture_ready_ru": (
            "Архитектура Farm Engine / Finance Reality почти готова; "
            "бизнес (Live Earn + Confirmed €) ещё нет."
        ),
        "strategic_question_ru": "Какой будет первый Live Earn Connector?",
        "first_live_earn_id": FIRST_LIVE_EARN_ID,
        "first_live_earn_choice_ru": "Свой API + Stripe (Направление A)",
        "tracks": [
            {
                "id": "A",
                "title_ru": "Направление A — коммерческое (самое быстрое)",
                "goal_ru": (
                    "Первый Confirmed € через собственный продукт (API/Stripe). "
                    "Доказать, что Finance Reality Law, Ledger и Payout Manager "
                    "работают на реальных деньгах."
                ),
                "focus_ru": "Свой Digital Product → Stripe → External Payout ID → REAL",
                "not_ru": "Не путать с «ферма сама находит работу в интернете».",
                "status": "primary",
            },
            {
                "id": "B",
                "title_ru": "Направление B — исследовательское (исходная идея)",
                "goal_ru": (
                    "Opportunity / Earn Platform Scanner постоянно ищет новые легальные "
                    "Earn-платформы: автоматизация разрешена · API · платит поставщикам · "
                    "есть внешний payout_id. Подключение без перестройки архитектуры."
                ),
                "focus_ru": (
                    "Искать рынки, где машина может работать сама — "
                    "не писать ещё OCR/анализатор."
                ),
                "not_ru": "Не ручной поиск клиентов и не Toloka Performer.",
                "status": "parallel_research",
            },
        ],
        "do_not_ru": [
            "Ещё один AI-модуль ради модуля",
            "Ещё один OCR / анализатор без Earn-канала",
            "Toloka Performer / капчи / human-bot",
        ],
        "north_star_ru": (
            "A даёт первый € и проверяет деньги. "
            "B приближает «ферма сама находит легальную работу»."
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
            "Опубликовать metered API (OCR/анализ/классификация) на RapidAPI Hub; "
            "официальный payout провайдера. Второй канал после первого Confirmed €."
        ),
        "tos_automation": "allowed",
        "legal_notes_ru": "Serving own API is the product. Marketplace fee + payout lag.",
        "est_revenue_eur_per_job": 0.15,
        "est_cost_eur_per_job": 0.03,
        "payout_path": "rapidapi_paypal",
        "capabilities": ["api", "ocr", "classification"],
        "rank_hint": 2,
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
        items: list[dict[str, Any]] = []
        for raw in _SEED_OPPORTUNITIES:
            opp = dict(raw)
            legal = legal_check(opp)
            roi = roi_check(opp)
            ceo = str(decisions.get(opp["id"]) or "research")
            pipeline_ok = bool(legal["ok"] and roi["ok"])
            stage = "rejected"
            if not legal["ok"]:
                stage = "legal_reject"
            elif not roi["ok"]:
                stage = "roi_reject"
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
        """CEO: go | reject | hold | research."""
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
        self._save_state(state)
        event = {
            "at": _utc_now(),
            "opportunity_id": opportunity_id,
            "decision": decision,
            "note": str(note or "")[:300],
        }
        self._append_jsonl(DECISIONS_FILE, event)
        return {"ok": True, **event, "scan": self.scan()}

    def enqueue(self, opportunity_id: str, *, note: str = "") -> dict[str, Any]:
        """Put CEO-GO opportunity on dry_run execution queue."""
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
        job = {
            "job_id": f"fj-{uuid.uuid4().hex[:12]}",
            "at": _utc_now(),
            "opportunity_id": opportunity_id,
            "title": item.get("title"),
            "status": "queued_dry_run",
            "mode": "dry_run",
            "note": str(note or "")[:300],
            "est_profit_eur": (item.get("roi") or {}).get("est_profit_eur"),
        }
        self._append_jsonl(QUEUE_FILE, job)
        return {"ok": True, "job": job}

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
            "note_ru": "v1 = dry_run очередь. Live execution — Farm v2 после Legal Review.",
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

        # Why REAL=0 — farm is before Law №3 step 1 (not a Toloka payout bug)
        commercial_blocker = {
            "ok": True,
            "question_wrong_ru": "Почему REAL = 0?",
            "question_right_ru": (
                "Какой первый Live Earn Connector мы можем легально подключить, "
                "чтобы появился первый External Payout ID?"
            ),
            "why_real_zero_ru": (
                "Toloka Pipeline API = Requester/Spend: dataset принят ≠ «вот тебе 0.05 €». "
                "Интеграция успешна как Spend; шага «платформа начислила выплату» нет — "
                "подтверждать нечего. Live Earn Connector отсутствует → REAL остаётся 0."
            ),
            "checklist": [
                {"id": "legal", "title_ru": "Legal PASS", "ok": True},
                {"id": "roi", "title_ru": "ROI PASS", "ok": True},
                {"id": "scanner", "title_ru": "Scanner", "ok": True},
                {"id": "execution_dry_run", "title_ru": "Execution (dry_run)", "ok": True},
                {
                    "id": "live_earn_connector",
                    "title_ru": "Live Earn Connector",
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
                        "Pipeline OK = dataset принят. Нет endpoint «earnings/payout» "
                        "для Virtus-исполнителя. Не Live Earn Connector."
                    ),
                },
            ],
            "first_live_earn_candidates": [
                {
                    "id": "earn-own-api-stripe",
                    "title_ru": "Свой Digital Product API + Stripe",
                    "why_ru": (
                        "Первый Live Earn (A): merchant → Stripe → External Payout ID. "
                        "Path A Stripe уже частично готов."
                    ),
                    "status": "first_pick",
                    "first_payout_score": 5,
                    "autonomy_score": 5,
                },
                {
                    "id": "earn-rapidapi-provider",
                    "title_ru": "RapidAPI Hub — API Provider",
                    "why_ru": "Второй канал (B) после первого Confirmed €.",
                    "status": "research",
                    "first_payout_score": 4,
                    "autonomy_score": 4,
                },
            ],
            "next_ru": (
                "A: довести свой API+Stripe до первого Hard REAL payout. "
                "B: крутить Earn Platform Scanner — искать новые легальные рынки. "
                "Не писать ещё OCR/AI без Earn-канала."
            ),
        }

        strategy = dual_track_strategy()
        platforms = scan_earn_platforms()
        return {
            "ok": True,
            "title_ru": "Зрелость · Commercial vs Farm vs Earn",
            "law_ru": (
                "Архитектура готова · бизнес ещё нет. "
                "A: первый Confirmed € = свой API+Stripe. "
                "B: Scanner ищет новые легальные Earn-платформы. "
                "Toloka Requester ≠ Earn."
            ),
            "levels": levels,
            "live_gates": live_gates,
            "live_connector_allowed": live_ready,
            "kpi": kpi,
            "factory": factory,
            "distribution": distribution,
            "strategy": strategy,
            "earn_platforms": platforms,
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
                "Earn Platform Scanner (B)",
                "Legal Check",
                "Profit Check",
                "Execution Queue",
                "Live Earn (A: API+Stripe)",
                "Finance Reality",
                "Ledger",
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
            "queue": q,
            "ledger": led,
            "forbidden_ru": [
                "Капчи и обход антифрода",
                "Боты на human-only микрозадачах (Toloka / MTurk / Clickworker)",
                "Мультиаккаунты / эмуляция человека",
            ],
        }
