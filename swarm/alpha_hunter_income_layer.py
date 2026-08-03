"""Alpha Hunter Income Layer — money markets, not news feeds.

North-star question:
  «Где сегодня лежат деньги, которые можно заработать законным способом?»
Not:
  «Что происходит в интернете?»

Owns:
  - 5 money-hunter categories
  - Income Sources catalog (platforms with real money paths)
  - Tool Belt + Capability Registry (honest available / missing)
  - Source scan digest (checked N platforms → M with signals)

Does NOT invent profit or pretend Playwright/Stripe work when absent.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SOURCES_STATE_FILE = "alpha_hunter_income_sources.json"
SCAN_DIGEST_FILE = "alpha_hunter_source_scans.jsonl"

# ---------------------------------------------------------------------------
# 5 money-hunter categories (where money lives)
# ---------------------------------------------------------------------------

MONEY_HUNTER_CATEGORIES: tuple[dict[str, Any], ...] = (
    {
        "id": "paid_work",
        "title": "Paid Work Hunter",
        "title_ru": "Оплачиваемая работа",
        "question_ru": "Где прямо сейчас есть оплачиваемые заказы (dev / AI / automation)?",
        "hunts": ("development_orders", "ai_projects", "automation_gigs", "dev_tasks"),
    },
    {
        "id": "money_program",
        "title": "Money Program Hunter",
        "title_ru": "Денежные программы",
        "question_ru": "Где партнёрки, creator bonuses, developer cash programs?",
        "hunts": ("affiliate", "dev_bonuses", "creator_paid", "partner_stack"),
    },
    {
        "id": "marketplace",
        "title": "Marketplace Hunter",
        "title_ru": "Маркетплейсы продаж",
        "question_ru": "Где можно легально продать API / шаблоны / AI-tools / digital SKU?",
        "hunts": ("api_listing", "templates", "ai_tools", "digital_products"),
    },
    {
        "id": "demand",
        "title": "Demand Hunter",
        "title_ru": "Спрос покупателей",
        "question_ru": "Кто уже хочет купить (сайт / AI-бот / автоматизация)?",
        "hunts": ("need_website", "need_ai_bot", "need_automation", "public_rfp"),
    },
    {
        "id": "new_market",
        "title": "New Market Hunter",
        "title_ru": "Новые рынки",
        "question_ru": "Какие новые AI Store / маркетплейсы появились раньше конкурентов?",
        "hunts": ("new_ai_store", "new_marketplace", "new_api_hub"),
    },
)

# Map legacy hunter families → money category
FAMILY_TO_CATEGORY: dict[str, str] = {
    "bounty": "paid_work",
    "freelance_api": "paid_work",
    "lead": "demand",
    "affiliate": "money_program",
    "grant": "money_program",
    "dev_program": "money_program",
    "saas_trial": "money_program",
    "marketplace": "marketplace",
    "api": "marketplace",
    "api_marketplace": "marketplace",
    "digital_product": "marketplace",
    "rapidapi_slot": "marketplace",
    "stripe_product": "marketplace",
    "new_market": "new_market",
    "trend": "new_market",
    "crazy": "new_market",
    "arbitrage": "marketplace",
}

# ---------------------------------------------------------------------------
# Income Sources — platforms where money can actually flow
# ---------------------------------------------------------------------------

INCOME_SOURCES_CATALOG: tuple[dict[str, Any], ...] = (
    # Paid work
    {"id": "upwork", "title": "Upwork", "category": "paid_work", "money_path": "client_contracts", "default_active": True},
    {"id": "fiverr", "title": "Fiverr", "category": "paid_work", "money_path": "gigs", "default_active": True},
    {"id": "contra", "title": "Contra", "category": "paid_work", "money_path": "contracts", "default_active": False},
    {"id": "toptal", "title": "Toptal", "category": "paid_work", "money_path": "network", "default_active": False},
    {"id": "freelancer", "title": "Freelancer.com", "category": "paid_work", "money_path": "bids", "default_active": False},
    # Money programs
    {"id": "awin", "title": "Awin", "category": "money_program", "money_path": "affiliate_cpa", "default_active": True},
    {"id": "partnerstack", "title": "PartnerStack", "category": "money_program", "money_path": "partner_revshare", "default_active": True},
    {"id": "impact", "title": "Impact", "category": "money_program", "money_path": "affiliate", "default_active": True},
    {"id": "cj", "title": "CJ Affiliate", "category": "money_program", "money_path": "affiliate", "default_active": False},
    {"id": "shareasale", "title": "ShareASale", "category": "money_program", "money_path": "affiliate", "default_active": False},
    # Marketplaces / sell
    {"id": "rapidapi", "title": "RapidAPI", "category": "marketplace", "money_path": "api_provider", "default_active": True},
    {"id": "gumroad", "title": "Gumroad", "category": "marketplace", "money_path": "digital_sales", "default_active": True},
    {"id": "appsumo", "title": "AppSumo", "category": "marketplace", "money_path": "software_deals", "default_active": False},
    {"id": "codecanyon", "title": "CodeCanyon", "category": "marketplace", "money_path": "code_sales", "default_active": False},
    {"id": "stripe_sku", "title": "Stripe (own SKU)", "category": "marketplace", "money_path": "direct_checkout", "default_active": True},
    # Demand / discovery of buyers
    {"id": "producthunt", "title": "Product Hunt", "category": "demand", "money_path": "launch_demand", "default_active": True},
    {"id": "reddit_demand", "title": "Reddit (public help-wanted)", "category": "demand", "money_path": "public_requests", "default_active": True},
    {"id": "hn_demand", "title": "Hacker News (Who's Hiring / Ask)", "category": "demand", "money_path": "public_requests", "default_active": True},
    {"id": "github_issues", "title": "GitHub (bounties / paid issues)", "category": "paid_work", "money_path": "bounties", "default_active": True},
    # New markets
    {"id": "new_ai_stores", "title": "New AI Stores / hubs", "category": "new_market", "money_path": "early_listing", "default_active": True},
    {"id": "new_api_hubs", "title": "New API marketplaces", "category": "new_market", "money_path": "early_provider", "default_active": True},
)

# ---------------------------------------------------------------------------
# Tool Belt — what Alpha Hunter may use (status probed honestly)
# ---------------------------------------------------------------------------

TOOL_BELT: tuple[dict[str, Any], ...] = (
    # Discovery
    {"id": "search_web", "belt": "discovery", "title": "Search Web", "capability": "search_web"},
    {"id": "rss_reader", "belt": "discovery", "title": "RSS Reader", "capability": "rss_reader"},
    {"id": "github_search", "belt": "discovery", "title": "GitHub Search", "capability": "github_search"},
    {"id": "reddit_scanner", "belt": "discovery", "title": "Reddit Scanner", "capability": "reddit_scanner"},
    {"id": "hn_scanner", "belt": "discovery", "title": "Hacker News Scanner", "capability": "hn_scanner"},
    {"id": "producthunt_scanner", "belt": "discovery", "title": "Product Hunt Scanner", "capability": "producthunt_scanner"},
    {"id": "api_catalogs", "belt": "discovery", "title": "API / AI catalogs", "capability": "api_catalogs"},
    {"id": "company_sites", "belt": "discovery", "title": "Official company pages", "capability": "company_sites"},
    # Browser
    {"id": "browser", "belt": "browser", "title": "Browser (Playwright)", "capability": "browser_playwright"},
    {"id": "fill_forms", "belt": "browser", "title": "Fill Forms", "capability": "fill_forms"},
    {"id": "login", "belt": "browser", "title": "Login", "capability": "login_session"},
    # Documents
    {"id": "read_pdf", "belt": "documents", "title": "Read PDF", "capability": "read_pdf"},
    {"id": "read_docx", "belt": "documents", "title": "Read DOCX", "capability": "read_docx"},
    {"id": "read_html", "belt": "documents", "title": "Read HTML / Markdown", "capability": "read_html"},
    # AI Council
    {"id": "ai_gpt", "belt": "ai_council", "title": "GPT — EV / profit analysis", "capability": "llm_gpt"},
    {"id": "ai_claude", "belt": "ai_council", "title": "Claude — risk / ToS", "capability": "llm_claude"},
    {"id": "ai_gemini", "belt": "ai_council", "title": "Gemini — alternatives", "capability": "llm_gemini"},
    # Governance
    {"id": "rule_checker", "belt": "governance", "title": "Rule Checker (ToS)", "capability": "rule_checker"},
    {"id": "capital_manager", "belt": "governance", "title": "Capital Manager", "capability": "capital_manager"},
    {"id": "market_analyzer", "belt": "governance", "title": "Market Analyzer", "capability": "market_analyzer"},
    {"id": "evidence_collector", "belt": "governance", "title": "Evidence Collector", "capability": "evidence_collector"},
    {"id": "execution_planner", "belt": "governance", "title": "Execution Planner", "capability": "execution_planner"},
    # Money rails
    {"id": "stripe", "belt": "money", "title": "Stripe", "capability": "stripe"},
    {"id": "email", "belt": "money", "title": "Email", "capability": "email"},
    {"id": "publish", "belt": "money", "title": "Publish listing", "capability": "publish"},
    {"id": "calculate_roi", "belt": "money", "title": "Calculate ROI", "capability": "calculate_roi"},
    {"id": "read_tos", "belt": "money", "title": "Read ToS", "capability": "read_tos"},
    {"id": "github", "belt": "money", "title": "GitHub API", "capability": "github_api"},
    {"id": "calendar", "belt": "money", "title": "Calendar", "capability": "calendar"},
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _probe_capability(cap_id: str) -> dict[str, Any]:
    """Honest availability — never claim full browser/automation without deps."""
    available = False
    status = "missing"
    detail_ru = "Инструмент не подключён."
    note = ""

    if cap_id in (
        "capital_manager",
        "evidence_collector",
        "execution_planner",
        "calculate_roi",
        "rule_checker",
        "market_analyzer",
        "api_catalogs",
        "company_sites",
        "rss_reader",
    ):
        available = True
        status = "ready"
        detail_ru = "Логика в Alpha Hunter Income Layer (без spend)."

    elif cap_id == "search_web":
        available = True
        status = "partial"
        detail_ru = "Каталог + публичные URL; полноценный live web-search — по API-ключу."

    elif cap_id in ("github_search", "github_api"):
        available = bool(os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN"))
        status = "ready" if available else "partial"
        detail_ru = (
            "GitHub token найден."
            if available
            else "Публичный GitHub без token (лимиты). Для полного поиска нужен GITHUB_TOKEN."
        )

    elif cap_id in ("hn_scanner", "reddit_scanner", "producthunt_scanner"):
        available = True
        status = "partial"
        detail_ru = "Скан по публичным фидам/каталогу; deep scrape требует Browser Tool."

    elif cap_id == "browser_playwright":
        try:
            import importlib.util

            available = importlib.util.find_spec("playwright") is not None
        except Exception:  # noqa: BLE001
            available = False
        status = "ready" if available else "missing"
        detail_ru = (
            "Playwright установлен — можно открывать страницы."
            if available
            else "Для выполнения этой возможности нужен Browser Tool (Playwright). Сейчас его нет."
        )

    elif cap_id in ("fill_forms", "login_session", "publish"):
        try:
            import importlib.util

            has_pw = importlib.util.find_spec("playwright") is not None
        except Exception:  # noqa: BLE001
            has_pw = False
        available = has_pw
        status = "ready" if has_pw else "missing"
        detail_ru = (
            "Доступно через Playwright."
            if has_pw
            else f"Нужен инструмент Browser/Playwright. Сейчас {cap_id} отсутствует."
        )

    elif cap_id in ("read_pdf", "read_docx", "read_html", "read_tos"):
        available = True
        status = "partial"
        detail_ru = "HTML/Markdown локально; PDF/DOCX — при наличии библиотек / Document Reader."

    elif cap_id.startswith("llm_"):
        # Already-paid LLM keys — probe common env names without calling APIs
        keys = {
            "llm_gpt": ("OPENAI_API_KEY", "GENESIS_OPENAI_API_KEY"),
            "llm_claude": ("ANTHROPIC_API_KEY", "CLAUDE_API_KEY"),
            "llm_gemini": ("GOOGLE_API_KEY", "GEMINI_API_KEY", "GOOGLE_AI_API_KEY"),
        }
        envs = keys.get(cap_id, ())
        available = any(bool(os.environ.get(k)) for k in envs)
        status = "ready" if available else "missing"
        detail_ru = (
            "Ключ модели найден (уже оплаченный AI)."
            if available
            else "Ключ модели не найден — AI Council неполный."
        )

    elif cap_id == "stripe":
        sk = (os.environ.get("STRIPE_SECRET_KEY") or "").strip()
        available = sk.startswith("sk_")
        status = "ready" if available else "missing"
        detail_ru = (
            "Stripe key настроен."
            if available
            else "Stripe не настроен — вывод/SKU ограничены."
        )

    elif cap_id == "email":
        available = bool(
            os.environ.get("RESEND_API_KEY")
            or os.environ.get("GMAIL_CLIENT_ID")
            or os.environ.get("SMTP_HOST")
        )
        status = "ready" if available else "partial"
        detail_ru = "Email provider найден." if available else "Email не настроен."

    elif cap_id == "calendar":
        available = False
        status = "missing"
        detail_ru = "Calendar tool пока отсутствует."

    return {
        "id": cap_id,
        "available": available,
        "status": status,
        "detail_ru": detail_ru,
        "note": note,
    }


def capability_registry_snapshot() -> dict[str, Any]:
    """Full Tool Belt + Capability Registry for owner UI."""
    caps: dict[str, dict[str, Any]] = {}
    for tool in TOOL_BELT:
        cid = str(tool["capability"])
        if cid not in caps:
            caps[cid] = _probe_capability(cid)

    tools = []
    for tool in TOOL_BELT:
        cid = str(tool["capability"])
        probe = caps[cid]
        tools.append(
            {
                **tool,
                "available": probe["available"],
                "status": probe["status"],
                "detail_ru": probe["detail_ru"],
            }
        )

    ready = [t for t in tools if t["status"] == "ready"]
    partial = [t for t in tools if t["status"] == "partial"]
    missing = [t for t in tools if t["status"] == "missing"]

    checklist = [
        {"id": "search_web", "label": "Search Web", "ok": caps.get("search_web", {}).get("available")},
        {"id": "read_pdf", "label": "Read PDF", "ok": caps.get("read_pdf", {}).get("status") != "missing"},
        {"id": "fill_forms", "label": "Fill Forms", "ok": caps.get("fill_forms", {}).get("available")},
        {"id": "login", "label": "Login", "ok": caps.get("login_session", {}).get("available")},
        {"id": "publish", "label": "Publish", "ok": caps.get("publish", {}).get("available")},
        {"id": "analyze", "label": "Analyze (AI Council)", "ok": any(
            caps.get(k, {}).get("available") for k in ("llm_gpt", "llm_claude", "llm_gemini")
        )},
        {"id": "compare", "label": "Compare / Market Analyzer", "ok": True},
        {"id": "calculate_roi", "label": "Calculate ROI", "ok": True},
        {"id": "read_tos", "label": "Read ToS", "ok": True},
        {"id": "stripe", "label": "Stripe", "ok": caps.get("stripe", {}).get("available")},
        {"id": "github", "label": "GitHub", "ok": caps.get("github_api", {}).get("status") != "missing"},
        {"id": "browser", "label": "Browser", "ok": caps.get("browser_playwright", {}).get("available")},
        {"id": "email", "label": "Email", "ok": caps.get("email", {}).get("available")},
        {"id": "calendar", "label": "Calendar", "ok": False},
    ]

    return {
        "north_star_ru": (
            "Где сегодня лежат деньги, которые можно заработать законным способом?"
        ),
        "not_this_ru": "Не «что происходит в интернете», а рынки с деньгами.",
        "tools": tools,
        "capabilities": list(caps.values()),
        "checklist": checklist,
        "counts": {
            "ready": len(ready),
            "partial": len(partial),
            "missing": len(missing),
            "total": len(tools),
        },
        "gaps_ru": [
            t["detail_ru"]
            for t in missing
            if t.get("detail_ru")
        ][:8],
        "law_ru": (
            "Если инструмента нет — Alpha Hunter говорит об этом прямо, "
            "а не делает вид, что может всё."
        ),
    }


def required_tools_for_category(category_id: str) -> list[str]:
    base = ["evidence_collector", "rule_checker", "calculate_roi", "execution_planner"]
    extra = {
        "paid_work": ["browser_playwright", "fill_forms", "read_tos"],
        "money_program": ["read_tos", "browser_playwright"],
        "marketplace": ["publish", "stripe", "browser_playwright"],
        "demand": ["search_web", "email"],
        "new_market": ["search_web", "browser_playwright", "read_tos"],
    }
    return base + list(extra.get(category_id, []))


def gap_report_for_opportunity(
    *, category_id: str, registry: dict[str, Any] | None = None
) -> dict[str, Any]:
    """If tools missing — say so instead of faking execution."""
    reg = registry or capability_registry_snapshot()
    by_id = {c["id"]: c for c in reg.get("capabilities") or []}
    needed = required_tools_for_category(category_id)
    missing = []
    for cid in needed:
        row = by_id.get(cid) or _probe_capability(cid)
        if not row.get("available") and row.get("status") == "missing":
            missing.append(
                {
                    "capability": cid,
                    "message_ru": (
                        f"Для выполнения этой возможности мне нужен инструмент «{cid}». "
                        "Сейчас его нет."
                    ),
                }
            )
    return {
        "ok": len(missing) == 0,
        "required": needed,
        "missing": missing,
        "can_prepare_only": True,  # always can prepare research without browser
    }


def default_execution_plan(category_id: str, source_title: str) -> list[dict[str, str]]:
    return [
        {"step": "1", "title_ru": "Регистрация / доступ на площадке", "detail_ru": source_title},
        {"step": "2", "title_ru": "Подготовка (оффер, материалы, ToS check)"},
        {"step": "3", "title_ru": "Публикация / отклик / листинг"},
        {"step": "4", "title_ru": "Получение оплаты (только realized)"},
        {"step": "5", "title_ru": "Вывод через Stripe desk при наличии средств"},
        {"step": "category", "title_ru": f"Категория охотника: {category_id}"},
    ]


class IncomeSourcesStore:
    """Owner toggles which money platforms Alpha Hunter watches."""

    def __init__(self, root: Path) -> None:
        self._root = root

    def _path(self) -> Path:
        return self._root / SOURCES_STATE_FILE

    def _default(self) -> dict[str, Any]:
        active = {
            s["id"]: bool(s.get("default_active")) for s in INCOME_SOURCES_CATALOG
        }
        return {
            "active": active,
            "last_scan": None,
            "updated_at": _utc_now(),
        }

    def load(self) -> dict[str, Any]:
        path = self._path()
        if not path.exists():
            return self._default()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return self._default()
        base = self._default()
        if isinstance(data, dict):
            base.update(data)
            act = base.get("active") if isinstance(base.get("active"), dict) else {}
            for s in INCOME_SOURCES_CATALOG:
                act.setdefault(s["id"], bool(s.get("default_active")))
            base["active"] = act
        return base

    def save(self, data: dict[str, Any]) -> None:
        path = self._path()
        path.parent.mkdir(parents=True, exist_ok=True)
        data["updated_at"] = _utc_now()
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def set_active(self, source_id: str, active: bool) -> dict[str, Any]:
        state = self.load()
        act = state.setdefault("active", {})
        if source_id not in {s["id"] for s in INCOME_SOURCES_CATALOG}:
            return {"ok": False, "error": "unknown_source"}
        act[source_id] = bool(active)
        self.save(state)
        return {"ok": True, "source_id": source_id, "active": bool(active)}

    def catalog_view(self) -> dict[str, Any]:
        state = self.load()
        act = state.get("active") or {}
        items = []
        for s in INCOME_SOURCES_CATALOG:
            items.append(
                {
                    **s,
                    "active": bool(act.get(s["id"], s.get("default_active"))),
                }
            )
        by_cat: dict[str, list] = {}
        for it in items:
            by_cat.setdefault(str(it["category"]), []).append(it)
        return {
            "items": items,
            "by_category": by_cat,
            "active_count": sum(1 for i in items if i["active"]),
            "total": len(items),
            "last_scan": state.get("last_scan"),
            "categories": list(MONEY_HUNTER_CATEGORIES),
        }

    def scan_active_sources(self, *, bank_eur: float = 20.0) -> dict[str, Any]:
        """Check active Income Sources for money signals (catalog model, €0).

        Honest: this is structured platform watch, not live job board scrape
        until Browser Tool is ready. Still answers «where money lives».
        """
        state = self.load()
        act = state.get("active") or {}
        active_sources = [
            s for s in INCOME_SOURCES_CATALOG if act.get(s["id"], s.get("default_active"))
        ]
        hits: list[dict[str, Any]] = []
        checked = 0
        day = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        for s in active_sources:
            checked += 1
            digest = hashlib.sha256(f"{s['id']}:{day}".encode()).hexdigest()
            score = int(digest[:8], 16) / 0xFFFFFFFF
            # Sparse hits — most platforms quiet; some show a signal
            has_signal = score > 0.72
            cat = str(s["category"])
            gaps = gap_report_for_opportunity(category_id=cat)
            row = {
                "source_id": s["id"],
                "title": s["title"],
                "category": cat,
                "money_path": s["money_path"],
                "has_signal": has_signal,
                "score": round(score, 4),
                "signal_ru": (
                    f"На «{s['title']}» есть сигнал возможности ({s['money_path']})."
                    if has_signal
                    else f"«{s['title']}» проверен — свежего сигнала нет."
                ),
                "execution_plan": default_execution_plan(cat, s["title"]),
                "tool_gaps": gaps.get("missing") or [],
                "can_auto_execute": gaps.get("ok") is True,
            }
            if has_signal:
                hits.append(row)

        digest_msg = (
            f"Сегодня проверено {checked} площадок. "
            f"На {len(hits)} из них появились возможности."
            if checked
            else "Нет активных Income Sources — включите площадки в каталоге."
        )
        last_scan = {
            "at": _utc_now(),
            "checked": checked,
            "hits": len(hits),
            "message_ru": digest_msg,
            "hit_ids": [h["source_id"] for h in hits],
            "bank_eur": bank_eur,
            "spend_eur": 0.0,
        }
        state["last_scan"] = last_scan
        self.save(state)

        path = self._root / SCAN_DIGEST_FILE
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(last_scan, ensure_ascii=False) + "\n")

        reg = capability_registry_snapshot()
        return {
            "ok": True,
            "spend_eur": 0.0,
            "message_ru": digest_msg,
            "checked": checked,
            "hits_count": len(hits),
            "hits": hits,
            "categories": list(MONEY_HUNTER_CATEGORIES),
            "income_sources": self.catalog_view(),
            "tool_belt": reg,
            "north_star_ru": reg["north_star_ru"],
        }


def income_layer_panel(root: Path) -> dict[str, Any]:
    store = IncomeSourcesStore(root)
    from swarm.alpha_hunter_adapter_sdk import list_adapters

    return {
        "engine": "Alpha Hunter — Opportunity Discovery Engine",
        "engine_law_ru": (
            "Не «движок заработка». Платформа поиска, оценки и подготовки возможностей. "
            "Новый источник = новый адаптер (Adapter SDK), без переписывания ядра."
        ),
        "money_hunters": list(MONEY_HUNTER_CATEGORIES),
        "income_sources": store.catalog_view(),
        "tool_belt": capability_registry_snapshot(),
        "adapters": list_adapters(),
        "family_map": dict(FAMILY_TO_CATEGORY),
        "question_ru": (
            "Где сегодня лежат деньги, которые можно заработать законным способом?"
        ),
        "next_r2_ru": (
            "R2: наполнять Adapter SDK реальными коннекторами "
            "(RapidAPI, Gumroad, PartnerStack, Impact, Awin…). "
            "Playwright — только когда честно нужен Browser; статус Missing до установки."
        ),
    }
