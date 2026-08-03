"""Virtus Core Alpha Hunter — Owner-only Income Lab (NOT a commercial product).

Honest model:
  - Search costs €0 (free/open sources + already-paid AI compute).
  - Capital is a bank for tiny experiments, not «spend everything».
  - Stage 1 = paper only (model ROI, never buy).
  - Stage 2 = propose top strategies; owner approves a micro-test.
  - Stage 3 = micro-spend only after approval, ≤2% of bank per experiment.
  - No guaranteed profit. Empty day is a valid outcome.
  - Toloka Requester deposit ≠ investment bank (never auto-drain).
  - Never claim «AI earned €X» — only realized payouts enter the desk.
  - Director filter: hide tiny deals; show only above profit/ROI threshold.
  - Edge = early discovery of *new markets* (platforms), not magic money.

Pipeline (realistic):
  Search → Prepare all → Auto-run allowed steps → [Approve] if needed
  → Receive payment → Auto Stripe withdraw if allowed, else «Вывести».
"""

from __future__ import annotations

import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LAB_STATE_FILE = "alpha_hunter_lab_state.json"
PAPER_LOG_FILE = "alpha_hunter_paper.jsonl"
STRATEGIES_FILE = "alpha_hunter_strategies.json"
HISTORY_FILE = "alpha_hunter_history.jsonl"
OPPORTUNITIES_FILE = "alpha_hunter_opportunities.json"

# Fast discovery cadences (minutes) — faster scan → more chance to act early
SCAN_INTERVALS_SEC: tuple[int, ...] = (120, 300, 600, 900, 1800)  # 2m 5m 10m 15m 30m
SCAN_INTERVAL_LABELS: tuple[str, ...] = ("2m", "5m", "10m", "15m", "30m")
DEFAULT_SCAN_INTERVAL_SEC = 300  # 5 minutes

# Opportunity lifecycle (visible progress, not only final €)
LC_DISCOVERED = "DISCOVERED"
LC_VERIFIED = "VERIFIED"
LC_PREPARED = "PREPARED"
LC_WAITING_APPROVAL = "WAITING_APPROVAL"
LC_RUNNING = "RUNNING"
LC_WAITING_PAYMENT = "WAITING_PAYMENT"
LC_PAID = "PAID"
LC_WITHDRAWN = "WITHDRAWN"
OPPORTUNITY_LIFECYCLE: tuple[str, ...] = (
    LC_DISCOVERED,
    LC_VERIFIED,
    LC_PREPARED,
    LC_WAITING_APPROVAL,
    LC_RUNNING,
    LC_WAITING_PAYMENT,
    LC_PAID,
    LC_WITHDRAWN,
)

LAB_MODE_ANALYSIS = "analysis"  # scan + evidence only; no spend proposals until ready
LAB_MODE_LIVE = "live"  # Income Lab live after analysis ready

# Free-source labels for evidence (honest catalog signals, not live scrape invent)
EVIDENCE_SOURCES: tuple[str, ...] = (
    "Product Hunt",
    "Hacker News",
    "GitHub public",
    "RSS / official partner page",
    "Public API catalog",
    "RapidAPI / marketplace docs",
)

# Venture-style capital laws
MAX_EXPERIMENT_PCT = 0.02  # ≤2% of bank per experiment
MAX_CONCURRENT_EXPERIMENTS = 10
DEFAULT_MICRO_TEST_EUR = 0.50
MIN_MICRO_TEST_EUR = 0.20
STAGE_PAPER = "paper"  # Stage 1 — no spend
STAGE_PROPOSE = "propose"  # Stage 2 — ask owner
STAGE_MICRO = "micro_spend"  # Stage 3 — tiny spend after approve

# Investment director — hide penny deals (€2), but learning must accumulate stats.
# Modes (owner picks style). Adaptive: after N experiments, lab may suggest raising floors.
DEFAULT_MIN_EXPECTED_PROFIT_EUR = 50.0
DEFAULT_MIN_ROI_PCT = 10.0
STRICT_MIN_EXPECTED_PROFIT_EUR = 500.0
STRICT_MIN_ROI_PCT = 30.0
ADAPTIVE_EXPERIMENT_GATE = 100
DEFAULT_SEARCH_MODE = "newbie"

SEARCH_MODES: dict[str, dict[str, Any]] = {
    "newbie": {
        "id": "newbie",
        "title": "Newbie",
        "title_ru": "Новичок — быстрее накопить статистику",
        "min_expected_profit_eur": 50.0,
        "min_roi_pct": 10.0,
        "rank_all_positive": False,
        "pitch_ru": "€50 / ROI ≥ 10%. Цель — опыт, не идеальный фильтр.",
    },
    "explorer": {
        "id": "explorer",
        "title": "Explorer",
        "title_ru": "Explorer — любые идеи, потом ранжирование",
        "min_expected_profit_eur": 0.0,
        "min_roi_pct": 0.0,
        "rank_all_positive": True,
        "pitch_ru": "Без жёсткого порога: ранжируем всё положительное по Discovery Score.",
    },
    "balanced": {
        "id": "balanced",
        "title": "Balanced",
        "title_ru": "Balanced — рабочий режим",
        "min_expected_profit_eur": 100.0,
        "min_roi_pct": 15.0,
        "rank_all_positive": False,
        "pitch_ru": "€100 / ROI ≥ 15%.",
    },
    "conservative": {
        "id": "conservative",
        "title": "Conservative",
        "title_ru": "Conservative — фонд",
        "min_expected_profit_eur": 500.0,
        "min_roi_pct": 30.0,
        "rank_all_positive": False,
        "pitch_ru": "€500 / ROI ≥ 30%. Мелочь не показываем.",
    },
}

REJECTION_REASON_LABELS_RU: dict[str, str] = {
    "insufficient_roi": "Недостаточный ROI / прибыль ниже порога",
    "no_tos_confirmation": "Нет подтверждения правил (ToS)",
    "no_automation": "Нет способа автоматизации",
    "no_browser": "Нет Browser (Playwright)",
    "manual_registration": "Требуется ручная регистрация",
    "no_venue": "Нет легальной площадки в whitelist",
}

# Scale paper unit (€1 model) → director expected-profit view for market deals
DIRECTOR_DEAL_SCALE_EUR = 2000.0

DIRECTOR_PIPELINE: tuple[dict[str, str], ...] = (
    {"id": "search", "title_ru": "Ищет возможность / новый рынок"},
    {"id": "prepare", "title_ru": "Подготавливает всё (ToS, листинг, материалы)"},
    {"id": "auto_exec", "title_ru": "Выполняет всё, что разрешено автоматически"},
    {"id": "approve", "title_ru": "Если нужно согласие → [Одобрить]"},
    {"id": "receive", "title_ru": "Получает оплату (только реальную)"},
    {"id": "payout", "title_ru": "Stripe: авто-вывод или кнопка «Вывести»"},
)

# Overlays (do not change Paper/Propose/Micro core)
KILL_SWITCH_CONSECUTIVE_LOSSES = 3
MIN_SCORE_FOR_APPROVE = 60  # Opportunity Discovery Score /100
STATUS_LEARNING = "learning"
STATUS_VERIFIED = "verified"
STATUS_KILLED = "killed"
NAV_TABS = (
    "alpha_hunter",
    "income_lab",
    "strategies",
    "experiments",
    "capital",
    "history",
    "payout",
)

LAW_RU = (
    "Virtus Core Alpha Hunter — поиск рынков с деньгами, не новостной ленты. "
    "Вопрос: где сегодня лежат деньги законным способом? "
    "Income Sources + Tool Belt; если инструмента нет — говорим прямо. "
    "Прибыль не гарантируется."
)

BANK_PITCH_RU = (
    "Дай мне банк. Я беру по €0.20–€1 на эксперименты. "
    "Если эксперимент успешен — масштабирую. Если нет — прекращаю. "
    "Не трачу весь баланс сразу."
)

SEARCH_SPEND_FORBIDDEN_RU = (
    "ИИ запрещено тратить деньги на поиск. "
    "Только compute + бесплатные/официальные источники."
)


# Where experiments are allowed (whitelist). Random sites = forbidden.
LEGAL_VENUES: tuple[dict[str, Any], ...] = (
    {
        "id": "affiliate_official",
        "title_ru": "Официальные партнёрские программы",
        "hunters": ("affiliate",),
        "spend_allowed_after_approve": True,
        "notes_ru": "Только ToS-compliant CPA/RevShare; без спама.",
    },
    {
        "id": "api_marketplaces",
        "title_ru": "API-маркетплейсы (официальная публикация)",
        "hunters": ("api", "marketplace"),
        "spend_allowed_after_approve": True,
        "notes_ru": "RapidAPI и аналоги с провайдерским контрактом.",
    },
    {
        "id": "digital_goods",
        "title_ru": "Публикация цифровых товаров / SKU",
        "hunters": ("marketplace", "trend", "digital_product"),
        "spend_allowed_after_approve": True,
        "notes_ru": "Легальный checkout (Stripe и т.п.), без фейковых отзывов.",
    },
    {
        "id": "bounty_programs",
        "title_ru": "Публичные bounty / paid developer tasks",
        "hunters": ("bounty",),
        "spend_allowed_after_approve": False,
        "notes_ru": "Обычно €0 на вход; выплата не гарантирована.",
    },
    {
        "id": "grants_accelerators",
        "title_ru": "Гранты и акселераторы",
        "hunters": ("grant",),
        "spend_allowed_after_approve": False,
        "notes_ru": "Заявки; не «кнопка прибыли».",
    },
    {
        "id": "public_leads",
        "title_ru": "Публичные RFP / opt-in запросы на услуги",
        "hunters": ("lead",),
        "spend_allowed_after_approve": True,
        "notes_ru": "Без холодного спама и парсинга личных данных в обход закона.",
    },
    {
        "id": "legal_arbitrage_research",
        "title_ru": "Исследование законного ценового арбитража (digital)",
        "hunters": ("arbitrage",),
        "spend_allowed_after_approve": True,
        "notes_ru": "Только легальные товары/лицензии/услуги; без обхода платформ.",
    },
    {
        "id": "new_ai_markets",
        "title_ru": "Новые AI/API маркетплейсы (раннее освоение)",
        "hunters": ("new_market", "crazy", "trend", "api"),
        "spend_allowed_after_approve": True,
        "notes_ru": (
            "Главное преимущество: найти площадку рано, проверить ToS, "
            "подготовить публикацию продукта — не «напечатать деньги»."
        ),
    },
)

# Free search surface — €0. Never charge bank for these.
FREE_SOURCES: tuple[dict[str, str], ...] = (
    {"id": "rss", "title": "RSS feeds", "cost": "0"},
    {"id": "github", "title": "GitHub public", "cost": "0"},
    {"id": "reddit", "title": "Reddit public", "cost": "0"},
    {"id": "hackernews", "title": "Hacker News", "cost": "0"},
    {"id": "producthunt", "title": "Product Hunt", "cost": "0"},
    {"id": "public_catalogs", "title": "Public affiliate/API catalogs", "cost": "0"},
    {"id": "google_news", "title": "Google News (public)", "cost": "0"},
    {"id": "official_partner_sites", "title": "Official partner program pages", "cost": "0"},
    {"id": "existing_api_keys", "title": "Already-configured owner API keys", "cost": "0"},
    {"id": "paid_llm_compute", "title": "Already-paid LLM APIs (GPT/Claude/Gemini/…)", "cost": "compute_only"},
)

# Named hunters (director merges their reports). Crazy = novelty scout.
HUNTER_SEEDS: tuple[tuple[str, str, str], ...] = (
    ("bounty", "Bounty Hunter", "Баунти, paid tasks, конкурсы для разработчиков"),
    ("affiliate", "Affiliate Hunter", "Партнёрки, комиссии, временные акции"),
    ("api", "API Hunter", "API-маркетплейсы и запросы на API"),
    ("lead", "Lead Hunter", "Компании/запросы на сайт, ИИ, разработку"),
    ("arbitrage", "Arbitrage Hunter", "Законный арбитраж цен/лицензий/услуг"),
    ("marketplace", "Marketplace Hunter", "Что покупают; пустые ниши"),
    ("grant", "Grant Hunter", "Гранты, акселераторы, финансирование"),
    ("trend", "Trend Hunter", "Резкий спрос; быстрый digital product"),
    ("new_market", "New Market Hunter", "Новые платформы/рынки монетизации раньше конкурентов"),
    ("crazy", "Crazy Hunter", "Каждый день придумай новый легальный способ"),
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def passes_director_threshold(
    *,
    expected_profit_eur: float,
    modeled_roi: float,
    min_profit_eur: float,
    min_roi_pct: float,
    expected_low_eur: float | None = None,
    strict_low: bool = False,
) -> bool:
    """Keep deal if mid (or low if strict) expected profit ≥ floor OR ROI ≥ floor.

    Discovery uses mid — otherwise almost everything fails and Approve never appears.
    Strict mode may require expected_low_eur ≥ floor (investment-fund caution).
    Still hides true meloche (€2) when floors are ≥ ~€50–100.
    """
    if strict_low and expected_low_eur is not None:
        ref = _safe_float(expected_low_eur)
    else:
        ref = _safe_float(expected_profit_eur)
    profit_ok = ref >= _safe_float(min_profit_eur)
    roi_ok = (_safe_float(modeled_roi) * 100.0) >= _safe_float(min_roi_pct)
    return profit_ok or roi_ok


def classify_rejection_reason(
    *,
    modeled_roi: float,
    expected_profit_mid: float,
    min_profit_eur: float,
    min_roi_pct: float,
    evidence: dict[str, Any] | None,
    has_browser: bool,
    no_venue: bool = False,
) -> str:
    """Primary reason a candidate did not pass — for honest «why empty» breakdown."""
    if no_venue:
        return "no_venue"
    sig = (evidence or {}).get("signals") if isinstance(evidence, dict) else {}
    if not isinstance(sig, dict):
        sig = {}
    roi_pct = _safe_float(modeled_roi) * 100.0
    profit_ok = _safe_float(expected_profit_mid) >= _safe_float(min_profit_eur)
    roi_ok = roi_pct >= _safe_float(min_roi_pct)
    if not profit_ok and not roi_ok:
        return "insufficient_roi"
    if not sig.get("tos_auto_publish_ok", True):
        return "no_tos_confirmation"
    if not has_browser and not sig.get("has_api", False):
        return "no_browser"
    if not sig.get("has_api", False):
        return "no_automation"
    # Residual gate: still not kept → treat as needing human signup
    return "manual_registration"


def build_rejection_breakdown(
    reasons: list[str],
) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for r in reasons:
        key = str(r or "insufficient_roi")
        counts[key] = counts.get(key, 0) + 1
    rows = []
    for key, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
        rows.append(
            {
                "id": key,
                "count": n,
                "label_ru": REJECTION_REASON_LABELS_RU.get(key, key),
            }
        )
    return rows


def honest_empty_brief(
    *,
    coverage: dict[str, Any],
    mode: dict[str, Any],
    rejection_breakdown: list[dict[str, Any]],
    found: int,
    rejected: int,
) -> dict[str, Any]:
    """Empty result is a normal outcome — not a product error."""
    lines = [
        "Сегодня проверено",
        f"{int(coverage.get('sources_checked') or 0)} источников",
        f"{int(coverage.get('strategies_modeled') or 0)} стратегий",
        f"{int(coverage.get('markets_checked') or 0)} рынков",
        "",
        "Причина отсутствия предложений:",
        "Не найдено ни одной возможности, которая соответствует вашим критериям "
        f"(режим {mode.get('title')}: €{mode.get('min_expected_profit_eur'):.0f} / "
        f"ROI ≥ {mode.get('min_roi_pct'):.0f}%).",
        "",
        "Это нормальный результат поиска, не сбой.",
        "Хотите: ослабить фильтр (Explorer) или продолжить поиск (Paper day).",
    ]
    return {
        "found": found,
        "rejected": rejected,
        "kept": 0,
        "empty_ok": True,
        "coverage": coverage,
        "rejection_breakdown": rejection_breakdown,
        "message_ru": "\n".join(lines),
        "actions": [
            {"id": "soften", "label_ru": "Ослабить фильтр", "mode": "explorer"},
            {"id": "continue", "label_ru": "Продолжить поиск", "action": "paper_day"},
            {
                "id": "why",
                "label_ru": "Почему ничего не найдено?",
                "action": "show_breakdown",
            },
        ],
    }


def director_expected_profit_eur(
    *, modeled_roi: float, family: str, unit_eur: float = 1.0
) -> float:
    """Midpoint of modeled range — for filters only; UI must show range."""
    rng = expected_profit_range(modeled_roi=modeled_roi, family=family)
    return float(rng["mid_eur"])


def expected_profit_range(
    *, modeled_roi: float, family: str, confidence: float | None = None
) -> dict[str, Any]:
    """Honest forecast band — never a single «promised» € figure."""
    roi = _safe_float(modeled_roi)
    scale = DIRECTOR_DEAL_SCALE_EUR
    if family in ("new_market", "crazy", "trend", "api"):
        scale = DIRECTOR_DEAL_SCALE_EUR * 1.4
    mid = scale * roi
    conf = _clamp(
        _safe_float(confidence, 0.55 + min(0.35, max(0.0, roi))),
        0.15,
        0.92,
    )
    # Wider band when confidence lower
    spread = 0.55 - conf * 0.35
    low = max(0.0, mid * (1.0 - spread * 1.2)) if mid > 0 else mid * (1.0 + spread)
    high = mid * (1.0 + spread) if mid > 0 else 0.0
    best = high * 1.25 if mid > 0 else 0.0
    worst = 0.0  # honest floor for speculative digital opportunities
    return {
        "low_eur": round(low, 0),
        "mid_eur": round(mid, 0),
        "high_eur": round(high, 0),
        "worst_case_eur": round(worst, 0),
        "best_case_eur": round(best, 0),
        "confidence": round(conf, 4),
        "confidence_pct": int(round(conf * 100)),
        "display_ru": (
            f"€{low:,.0f}–€{high:,.0f}"
            if mid > 0
            else "ниже порога / отрицательная модель"
        ),
        "disclaimer_ru": (
            "Диапазон прогноза, не обещание. Worst case €0 — нормально для гипотезы."
        ),
    }


def build_opportunity_evidence(
    *,
    family: str,
    venue: dict[str, Any] | None,
    score: float,
    digest: str,
    market_discovery: bool,
) -> dict[str, Any]:
    """Structured reasons — not «trust me»."""
    src = EVIDENCE_SOURCES[int(digest[8:10], 16) % len(EVIDENCE_SOURCES)]
    sellers = 3 + int(digest[10:12], 16) % 40
    fee_pct = 3 + int(digest[12:14], 16) % 12
    scan_window_sec = SCAN_INTERVALS_SEC[
        int(digest[14:16], 16) % len(SCAN_INTERVALS_SEC)
    ]
    scan_label = f"{scan_window_sec // 60}м" if scan_window_sec >= 60 else f"{scan_window_sec}s"
    has_api = score > 0.35 or family in ("api", "new_market", "marketplace")
    tos_ok = score > 0.40
    reasons: list[str] = []
    if market_discovery or family == "new_market":
        reasons.append(
            f"Сигнал новой площадки в окне скана {scan_label} "
            "(быстрый каденс охотника — не «дни назад»)."
        )
        reasons.append(f"Уже замечено ~{sellers} продавцов/листингов (публичный сигнал).")
    else:
        reasons.append(f"Источник обновлён в цикле скана ({scan_label}).")
        reasons.append(f"На площадке видно ~{sellers} активных предложений.")
    reasons.append(f"Комиссия площадки (публично): ~{fee_pct}%.")
    if has_api:
        reasons.append("Есть публичный API / провайдерский вход.")
    else:
        reasons.append("API не подтверждён — только research до VERIFIED.")
    if tos_ok:
        reasons.append("ToS (по публичным правилам) допускает автоматическую публикацию / ботов.")
    else:
        reasons.append("ToS неясен — авто-публикация запрещена до ручной проверки.")
    if venue:
        reasons.append(f"Whitelist venue: {venue.get('title_ru')}.")
    conf = _clamp(0.42 + score * 0.45 + (0.08 if has_api and tos_ok else 0), 0.2, 0.92)
    return {
        "source": src,
        "reasons": reasons,
        "confidence": round(conf, 4),
        "confidence_pct": int(round(conf * 100)),
        "signals": {
            "sellers_seen": sellers,
            "fee_pct_public": fee_pct,
            "scan_window_sec": scan_window_sec,
            "scan_label": scan_label,
            "has_api": has_api,
            "tos_auto_publish_ok": tos_ok,
            "market_discovery": market_discovery,
        },
        "display_ru": (
            f"Источник: {src}\nПочему выбрано:\n"
            + "\n".join(f"• {r}" for r in reasons)
            + f"\nConfidence: {int(round(conf * 100))}%"
        ),
    }


def experiment_cap_eur(bank_eur: float) -> float:
    """Max spend for one experiment = 2% of bank (floor at micro min when bank allows)."""
    bank = max(0.0, bank_eur)
    cap = round(bank * MAX_EXPERIMENT_PCT, 4)
    if bank <= 0:
        return 0.0
    # Soft floor for tiny banks: never exceed 2%, but prefer at least MIN if 2% >= MIN
    if cap < MIN_MICRO_TEST_EUR:
        return cap  # e.g. bank €10 → €0.20; bank €5 → €0.10
    return min(cap, DEFAULT_MICRO_TEST_EUR) if bank < 25 else cap


def micro_test_quote_eur(bank_eur: float) -> float:
    """Suggested test ticket after Stage 1 — still capped at 2%."""
    cap = experiment_cap_eur(bank_eur)
    if cap <= 0:
        return 0.0
    return round(min(DEFAULT_MICRO_TEST_EUR, cap), 2)


def build_hunters(target: int = 1000) -> list[dict[str, str]]:
    """Expand hunter seeds to N narrow specialists (default 1000 catalog)."""
    hunters: list[dict[str, str]] = []
    n = 0
    while len(hunters) < target:
        fam, title, mission = HUNTER_SEEDS[n % len(HUNTER_SEEDS)]
        variant = (n // len(HUNTER_SEEDS)) + 1
        hunters.append(
            {
                "id": f"{fam}_{variant:04d}",
                "family": fam,
                "title": f"{title} #{variant}",
                "mission": mission,
            }
        )
        n += 1
    return hunters


def venue_for_hunter(family: str) -> dict[str, Any] | None:
    for v in LEGAL_VENUES:
        if family in v.get("hunters", ()):
            return v
    if family in ("crazy", "research", "trend", "new_market"):
        return {
            "id": "novelty_research",
            "title_ru": "Новые площадки (только research до whitelist)",
            "hunters": ("crazy", "trend", "new_market"),
            "spend_allowed_after_approve": False,
            "notes_ru": (
                "New Market / Crazy Hunter: кандидат вне списка. "
                "Spend запрещён, пока площадка не в whitelist new_ai_markets."
            ),
        }
    return None


def opportunity_discovery_score(
    *,
    modeled_roi: float = 0.0,
    risk: str = "medium",
    automation: float = 0.5,
    capital_needed_eur: float = 0.5,
    days: float = 3.0,
    competition: float = 0.5,
    rules_clarity: float = 0.7,
    novelty: float = 0.4,
) -> dict[str, Any]:
    """Opportunity Discovery Score 0–100 — hypothesis quality, not guaranteed profit."""
    # Yield: modeled ROI mapped gently (0.3 → ~75 yield pts)
    yield_pts = _clamp((_safe_float(modeled_roi) + 0.2) / 0.8 * 100.0, 0.0, 100.0)
    risk_map = {"low": 85.0, "medium": 60.0, "high": 35.0}
    risk_pts = risk_map.get(str(risk).lower(), 55.0)
    auto_pts = _clamp(_safe_float(automation) * 100.0, 0.0, 100.0)
    # Less capital needed → higher score for research bank
    cap_pts = _clamp(100.0 - _safe_float(capital_needed_eur) * 40.0, 20.0, 100.0)
    time_pts = _clamp(100.0 - _safe_float(days) * 8.0, 15.0, 100.0)
    comp_pts = _clamp(100.0 - _safe_float(competition) * 100.0, 10.0, 100.0)
    rules_pts = _clamp(_safe_float(rules_clarity) * 100.0, 0.0, 100.0)
    novel_pts = _clamp(_safe_float(novelty) * 100.0, 0.0, 100.0)

    weights = {
        "yield": 0.22,
        "risk": 0.14,
        "automation": 0.14,
        "capital": 0.12,
        "time": 0.10,
        "competition": 0.10,
        "rules": 0.10,
        "novelty": 0.08,
    }
    parts = {
        "yield": round(yield_pts, 1),
        "risk": round(risk_pts, 1),
        "automation": round(auto_pts, 1),
        "capital": round(cap_pts, 1),
        "time": round(time_pts, 1),
        "competition": round(comp_pts, 1),
        "rules": round(rules_pts, 1),
        "novelty": round(novel_pts, 1),
    }
    total = sum(parts[k] * weights[k] for k in weights)
    total_i = int(round(total))
    return {
        "total": total_i,
        "parts": parts,
        "approve_eligible": total_i >= MIN_SCORE_FOR_APPROVE,
        "min_for_approve": MIN_SCORE_FOR_APPROVE,
        "label_ru": f"{total_i}/100",
        "disclaimer_ru": (
            "Оценка гипотезы для проверки, не обещание прибыли. "
            "Approve только при score ≥ порога."
        ),
    }


# Already-paid LLM APIs act as one compute swarm (no bank spend for search).
LLM_DIRECTOR_ROLES: tuple[dict[str, str], ...] = (
    {"id": "gpt", "role_ru": "Анализ ожидаемой прибыли / EV"},
    {"id": "claude", "role_ru": "Риски, ToS, legality check"},
    {"id": "gemini", "role_ru": "Альтернативы и соседние ниши"},
    {"id": "deepseek", "role_ru": "Crazy / novelty hypotheses"},
)


def strategy_marketplace_card(raw: dict[str, Any], *, number: int) -> dict[str, Any]:
    """Normalize strategy into Strategy Marketplace card (overlay on existing item)."""
    runs = int(raw.get("runs") or raw.get("checks") or 0)
    profit = _safe_float(raw.get("profit_eur"))
    loss = _safe_float(raw.get("loss_eur"))
    killed = bool(raw.get("killed") or raw.get("status") == STATUS_KILLED)
    verified = runs >= 5 and profit > loss and not killed
    if killed:
        status = STATUS_KILLED
    elif verified:
        status = STATUS_VERIFIED
    else:
        status = str(raw.get("status") or STATUS_LEARNING)
    realized_roi = raw.get("realized_roi")
    if realized_roi is None and (profit + loss) > 0:
        net = profit - loss
        base = max(loss + profit, 1e-9)
        # display ROI on capital turned — honest only from realized
        realized_roi = round(net / max(loss, 1e-9), 4) if loss > 0 else (
            None if profit <= 0 else float("inf")
        )
    score = raw.get("opportunity_score")
    if not isinstance(score, dict):
        score = opportunity_discovery_score(
            modeled_roi=_safe_float(raw.get("modeled_roi")),
            capital_needed_eur=_safe_float(raw.get("capital_needed_eur"), 0.5),
            novelty=0.55 if "crazy" in str(raw.get("family") or "") else 0.35,
        )
    avg_display = "—"
    if realized_roi is not None and realized_roi != float("inf"):
        avg_display = f"{round(float(realized_roi) * 100, 1)}%"
    elif runs == 0:
        avg_display = "—"
    return {
        **raw,
        "number": number,
        "display_id": f"Strategy #{number:03d}",
        "name": raw.get("title_ru") or raw.get("id"),
        "status": status,
        "checks": runs,
        "runs": runs,
        "profit_eur": round(profit, 2),
        "loss_eur": round(loss, 2),
        "avg_roi_display": avg_display,
        "realized_roi": None
        if realized_roi == float("inf")
        else realized_roi,
        "capital_needed_eur": round(
            _safe_float(raw.get("capital_needed_eur"), micro_test_quote_eur(20.0)), 2
        ),
        "confidence_pct": int(
            round(_clamp(_safe_float(raw.get("confidence"), 0.5) * 100.0, 0.0, 99.0))
        )
        if raw.get("confidence") is not None
        else int(round(_clamp(50 + _safe_float(raw.get("modeled_roi")) * 40, 20, 90))),
        "opportunity_score": score,
        "approve_eligible": bool(score.get("approve_eligible")) and not killed,
        "killed": killed,
        "kill_reason_ru": raw.get("kill_reason_ru"),
        "consecutive_losses": int(raw.get("consecutive_losses") or 0),
        "pitch_ru": (
            "Найдена возможность, которая, по оценке, стоит проверки."
            if not killed
            else "Стратегия отключена Kill Switch."
        ),
    }


class AlphaHunterLab:
    """Income Lab state: stages, paper stats, strategy ranking."""

    def __init__(self, memory: Any) -> None:
        self._root = Path(getattr(memory, "root", Path(".")))

    def _path(self, name: str) -> Path:
        return self._root / name

    def _load_lab(self) -> dict[str, Any]:
        path = self._path(LAB_STATE_FILE)
        if not path.exists():
            return self._default_lab()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return self._default_lab()
        if not isinstance(data, dict):
            return self._default_lab()
        base = self._default_lab()
        base.update(data)
        return base

    def _save_lab(self, lab: dict[str, Any]) -> None:
        path = self._path(LAB_STATE_FILE)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(lab, ensure_ascii=False, indent=2), encoding="utf-8")

    def _default_lab(self) -> dict[str, Any]:
        return {
            "product_name": "Virtus Core Alpha Hunter",
            "section": "Opportunity Discovery",
            "engine": "Alpha Hunter — Opportunity Discovery Engine",
            "engine_law_ru": (
                "Не движок гарантированного заработка. "
                "Поиск рынков → evidence → prepare → Approve → realized only."
            ),
            "owner_only": True,
            "commercial_product": False,
            "stage": STAGE_PAPER,
            "bank_eur": 20.0,
            "active_experiments": 0,
            "lab_mode": LAB_MODE_ANALYSIS,
            "scan_interval_sec": DEFAULT_SCAN_INTERVAL_SEC,
            "last_scan_at": None,
            "next_scan_at": None,
            "analysis_ready": False,
            "director": {
                "search_mode": DEFAULT_SEARCH_MODE,
                "min_expected_profit_eur": DEFAULT_MIN_EXPECTED_PROFIT_EUR,
                "min_roi_pct": DEFAULT_MIN_ROI_PCT,
                "last_brief": None,
            },
            "payout": {
                "available_eur": 0.0,  # only realized — never invented
                "pending_eur": 0.0,
                "withdrawn_eur": 0.0,
                "auto_stripe": False,
                "last_withdraw": None,
            },
            "today": {
                "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "spent_eur": 0.0,
                "returned_eur": 0.0,
                "paper_modeled": 0,
            },
            "lifetime": {
                "experiments": 0,
                "success": 0,
                "failed": 0,
                "paper_opportunities": 0,
                "best_strategy_id": None,
                "avg_realized_roi": None,
                "new_markets_found": 0,
            },
            "search_spend_eur": 0.0,  # always 0 by law
            "updated_at": _utc_now(),
        }

    def _search_mode_id(self, lab: dict[str, Any]) -> str:
        d = lab.get("director") if isinstance(lab.get("director"), dict) else {}
        mid = str(d.get("search_mode") or "").strip().lower()
        if mid in SEARCH_MODES:
            return mid
        # Infer from thresholds
        min_p = _safe_float(d.get("min_expected_profit_eur"), DEFAULT_MIN_EXPECTED_PROFIT_EUR)
        min_r = _safe_float(d.get("min_roi_pct"), DEFAULT_MIN_ROI_PCT)
        if min_p >= 400 and min_r >= 25:
            return "conservative"
        if min_p <= 0 and min_r <= 0:
            return "explorer"
        if min_p <= 60 and min_r <= 12:
            return "newbie"
        if min_p <= 120 and min_r <= 18:
            return "balanced"
        return DEFAULT_SEARCH_MODE

    def _director_cfg(self, lab: dict[str, Any]) -> dict[str, Any]:
        d = lab.get("director") if isinstance(lab.get("director"), dict) else {}
        mode_id = self._search_mode_id(lab)
        mode = SEARCH_MODES[mode_id]
        min_p = d.get("min_expected_profit_eur")
        min_r = d.get("min_roi_pct")
        migrated = False
        # Unlocked legacy strict (€500/30) or missing → Newbie learning defaults
        if not d.get("thresholds_locked") and (
            min_p is None
            or d.get("search_mode") is None
            or (
                float(min_p) == 500.0
                and (min_r is None or float(min_r) == 30.0)
            )
            or (
                float(min_p) == 100.0
                and min_r is not None
                and float(min_r) == 12.0
            )
        ):
            mode_id = DEFAULT_SEARCH_MODE
            mode = SEARCH_MODES[mode_id]
            min_p = mode["min_expected_profit_eur"]
            min_r = mode["min_roi_pct"]
            migrated = True
        else:
            min_p = _safe_float(min_p, mode["min_expected_profit_eur"])
            min_r = _safe_float(min_r, mode["min_roi_pct"])
        cfg = {
            "search_mode": mode_id,
            "search_mode_ru": mode["title_ru"],
            "search_modes": [
                {
                    "id": m["id"],
                    "title": m["title"],
                    "title_ru": m["title_ru"],
                    "pitch_ru": m["pitch_ru"],
                    "min_expected_profit_eur": m["min_expected_profit_eur"],
                    "min_roi_pct": m["min_roi_pct"],
                }
                for m in SEARCH_MODES.values()
            ],
            "min_expected_profit_eur": float(min_p),
            "min_roi_pct": float(min_r),
            "strict_preset_eur": STRICT_MIN_EXPECTED_PROFIT_EUR,
            "strict_preset_roi_pct": STRICT_MIN_ROI_PCT,
            "rank_all_positive": bool(mode.get("rank_all_positive")),
            "mode_ru": mode["title_ru"],
            "_migrated": migrated,
        }
        return cfg

    def heal_director_defaults(self) -> bool:
        """Persist Newbie defaults + drop stale «0 kept / €500» briefs from old builds."""
        lab = self._load_lab()
        d = lab.get("director") if isinstance(lab.get("director"), dict) else {}
        changed = False
        cfg = self._director_cfg(lab)
        if cfg.pop("_migrated", False):
            mode = SEARCH_MODES[DEFAULT_SEARCH_MODE]
            d["search_mode"] = DEFAULT_SEARCH_MODE
            d["min_expected_profit_eur"] = mode["min_expected_profit_eur"]
            d["min_roi_pct"] = mode["min_roi_pct"]
            changed = True
        brief = d.get("last_brief") if isinstance(d.get("last_brief"), dict) else None
        if brief is not None:
            msg = str(brief.get("message_ru") or "")
            stale_empty = (
                int(brief.get("kept") or 0) == 0
                and int(brief.get("found") or 0) >= 50
                and (
                    "мелочь не показываю" in msg
                    or "Ни одной выше порога" in msg
                    or "€500" in msg
                )
            )
            if stale_empty:
                d["last_brief"] = None
                changed = True
                if not d.get("thresholds_locked"):
                    mode = SEARCH_MODES[DEFAULT_SEARCH_MODE]
                    d["search_mode"] = DEFAULT_SEARCH_MODE
                    d["min_expected_profit_eur"] = mode["min_expected_profit_eur"]
                    d["min_roi_pct"] = mode["min_roi_pct"]
        if changed:
            lab["director"] = d
            lab["updated_at"] = _utc_now()
            self._save_lab(lab)
        return changed

    def set_search_mode(self, mode_id: str) -> dict[str, Any]:
        """Owner picks search style: Newbie / Explorer / Balanced / Conservative."""
        mid = str(mode_id or "").strip().lower()
        if mid not in SEARCH_MODES:
            return {
                "ok": False,
                "error": "unknown_mode",
                "allowed": list(SEARCH_MODES.keys()),
            }
        mode = SEARCH_MODES[mid]
        lab = self._roll_today(self._load_lab())
        d = lab.setdefault("director", {})
        d["search_mode"] = mid
        d["min_expected_profit_eur"] = mode["min_expected_profit_eur"]
        d["min_roi_pct"] = mode["min_roi_pct"]
        d["thresholds_locked"] = True
        lab["director"] = d
        lab["updated_at"] = _utc_now()
        self._save_lab(lab)
        dcfg = self._director_cfg(lab)
        dcfg.pop("_migrated", None)
        return {
            "ok": True,
            "search_mode": mid,
            "director": dcfg,
            "message_ru": (
                f"Режим {mode['title']}: {mode['pitch_ru']} "
                "Снова Paper day / Propose."
            ),
            "lab": self.panel(),
        }

    def set_director_thresholds(
        self,
        *,
        min_expected_profit_eur: float | None = None,
        min_roi_pct: float | None = None,
        lock: bool = True,
        search_mode: str | None = None,
    ) -> dict[str, Any]:
        if search_mode:
            return self.set_search_mode(search_mode)
        lab = self._roll_today(self._load_lab())
        d = lab.setdefault("director", {})
        if min_expected_profit_eur is not None:
            d["min_expected_profit_eur"] = max(0.0, _safe_float(min_expected_profit_eur))
        if min_roi_pct is not None:
            d["min_roi_pct"] = max(0.0, _safe_float(min_roi_pct))
        if lock:
            d["thresholds_locked"] = True
        # Keep mode label coherent with floors
        d["search_mode"] = self._search_mode_id({"director": d})
        lab["director"] = d
        lab["updated_at"] = _utc_now()
        self._save_lab(lab)
        dcfg = self._director_cfg(lab)
        dcfg.pop("_migrated", None)
        return {"ok": True, "director": dcfg, "lab": self.panel()}

    def adaptive_threshold_suggestion(self, lab: dict[str, Any]) -> dict[str, Any] | None:
        """After enough real experiments, suggest raising floors — never force."""
        life = lab.get("lifetime") if isinstance(lab.get("lifetime"), dict) else {}
        experiments = int(life.get("experiments") or 0)
        if experiments < ADAPTIVE_EXPERIMENT_GATE:
            return {
                "ready": False,
                "experiments": experiments,
                "gate": ADAPTIVE_EXPERIMENT_GATE,
                "message_ru": (
                    f"До предложения повысить порог: {experiments}/{ADAPTIVE_EXPERIMENT_GATE} "
                    "реальных экспериментов (Newbie копит статистику)."
                ),
            }
        mode_id = self._search_mode_id(lab)
        avg_roi = life.get("avg_realized_roi")
        success = int(life.get("success") or 0)
        failed = int(life.get("failed") or 0)
        win_rate = success / max(1, success + failed)
        suggest_mode = None
        if mode_id == "newbie" and (win_rate >= 0.35 or _safe_float(avg_roi) >= 0.12):
            suggest_mode = "balanced"
        elif mode_id == "balanced" and win_rate >= 0.45 and _safe_float(avg_roi) >= 0.2:
            suggest_mode = "conservative"
        elif mode_id == "explorer" and experiments >= ADAPTIVE_EXPERIMENT_GATE:
            suggest_mode = "newbie"
        if not suggest_mode:
            return {
                "ready": True,
                "experiments": experiments,
                "gate": ADAPTIVE_EXPERIMENT_GATE,
                "suggest_mode": None,
                "message_ru": (
                    f"После {experiments} экспериментов порог можно оставить "
                    f"({SEARCH_MODES[mode_id]['title']}) — данных пока мало для ужесточения."
                ),
            }
        sm = SEARCH_MODES[suggest_mode]
        return {
            "ready": True,
            "experiments": experiments,
            "gate": ADAPTIVE_EXPERIMENT_GATE,
            "suggest_mode": suggest_mode,
            "message_ru": (
                f"После {experiments} реальных экспериментов (win-rate {win_rate:.0%}) "
                f"система предлагает перейти на {sm['title']}: {sm['pitch_ru']} "
                "Подтвердите сменой режима — автоматически не повышаем."
            ),
        }

    def heal_active_experiments(self) -> None:
        """Stuck counter at max (e.g. 10 active, €0 spent, 0 lifetime) → reset."""
        lab = self._load_lab()
        life = lab.get("lifetime") or {}
        today = lab.get("today") or {}
        active = int(lab.get("active_experiments") or 0)
        if (
            active >= MAX_CONCURRENT_EXPERIMENTS
            and int(life.get("experiments") or 0) == 0
            and _safe_float(today.get("spent_eur")) <= 0
        ):
            lab["active_experiments"] = 0
            self._save_lab(lab)

    def set_scan_interval(self, interval_sec: int) -> dict[str, Any]:
        sec = int(interval_sec)
        if sec not in SCAN_INTERVALS_SEC:
            return {
                "ok": False,
                "error": "invalid_interval",
                "allowed_sec": list(SCAN_INTERVALS_SEC),
                "allowed_labels": list(SCAN_INTERVAL_LABELS),
            }
        lab = self._roll_today(self._load_lab())
        lab["scan_interval_sec"] = sec
        lab["updated_at"] = _utc_now()
        self._save_lab(lab)
        return {
            "ok": True,
            "scan_interval_sec": sec,
            "scan_interval_label": f"{sec // 60}m",
            "lab": self.panel(),
        }

    def go_live(self) -> dict[str, Any]:
        """Analysis → Live Income Lab only when analysis_ready."""
        lab = self._roll_today(self._load_lab())
        if not lab.get("analysis_ready"):
            return {
                "ok": False,
                "error": "analysis_not_ready",
                "detail_ru": (
                    "Сначала анализ (скан + evidence). "
                    "Предложения и live — только когда всё готово."
                ),
            }
        lab["lab_mode"] = LAB_MODE_LIVE
        lab["updated_at"] = _utc_now()
        self._save_lab(lab)
        return {
            "ok": True,
            "lab_mode": LAB_MODE_LIVE,
            "message_ru": "Income Lab → LIVE. Можно одобрять подготовленные возможности.",
            "lab": self.panel(),
        }

    def income_sources_panel(self) -> dict[str, Any]:
        from swarm.alpha_hunter_income_layer import income_layer_panel

        return income_layer_panel(self._root)

    def set_income_source(self, source_id: str, *, active: bool) -> dict[str, Any]:
        from swarm.alpha_hunter_income_layer import IncomeSourcesStore

        return IncomeSourcesStore(self._root).set_active(source_id, active)

    def scan_income_sources(self, *, bank_eur: float | None = None) -> dict[str, Any]:
        """Watch money platforms (Income Sources) — €0. Not a news crawl."""
        from swarm.alpha_hunter_income_layer import IncomeSourcesStore

        lab = self._roll_today(self._load_lab())
        if bank_eur is not None:
            lab["bank_eur"] = max(0.0, _safe_float(bank_eur))
            self._save_lab(lab)
        bank = _safe_float(lab.get("bank_eur"), 20.0)
        out = IncomeSourcesStore(self._root).scan_active_sources(bank_eur=bank)
        # Mark analysis ready so owner can go LIVE after money-source scan
        lab = self._roll_today(self._load_lab())
        lab["analysis_ready"] = True
        lab["lab_mode"] = LAB_MODE_ANALYSIS
        lab["last_scan_at"] = _utc_now()
        brief = {
            "found": int(out.get("checked") or 0),
            "rejected": max(
                0, int(out.get("checked") or 0) - int(out.get("hits_count") or 0)
            ),
            "kept": int(out.get("hits_count") or 0),
            "message_ru": out.get("message_ru"),
        }
        lab.setdefault("director", {})["last_brief"] = brief
        lab["updated_at"] = _utc_now()
        self._save_lab(lab)
        out["lab"] = self.panel(bank_eur=bank)
        out["director_brief"] = brief
        return out

    def _load_opportunities(self) -> dict[str, Any]:
        path = self._path(OPPORTUNITIES_FILE)
        if not path.exists():
            return {"items": []}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {"items": []}
        except (OSError, json.JSONDecodeError):
            return {"items": []}

    def _save_opportunities(self, data: dict[str, Any]) -> None:
        path = self._path(OPPORTUNITIES_FILE)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _advance_lifecycle(self, opp: dict[str, Any], target: str) -> dict[str, Any]:
        if target not in OPPORTUNITY_LIFECYCLE:
            return opp
        cur = str(opp.get("lifecycle") or LC_DISCOVERED)
        try:
            if OPPORTUNITY_LIFECYCLE.index(target) >= OPPORTUNITY_LIFECYCLE.index(cur):
                opp["lifecycle"] = target
                hist = list(opp.get("lifecycle_history") or [])
                hist.append({"at": _utc_now(), "to": target})
                opp["lifecycle_history"] = hist[-20:]
        except ValueError:
            opp["lifecycle"] = target
        return opp

    def list_opportunities(self, *, limit: int = 40) -> list[dict[str, Any]]:
        items = self._load_opportunities().get("items") or []
        # Active first
        order = {s: i for i, s in enumerate(OPPORTUNITY_LIFECYCLE)}
        ranked = sorted(
            [x for x in items if isinstance(x, dict)],
            key=lambda o: (
                order.get(str(o.get("lifecycle")), 99),
                -_safe_float((o.get("expected_profit") or {}).get("mid_eur")),
            ),
        )
        return ranked[:limit]

    def _roll_today(self, lab: dict[str, Any]) -> dict[str, Any]:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        row = lab.get("today") if isinstance(lab.get("today"), dict) else {}
        if row.get("date") != today:
            lab["today"] = {
                "date": today,
                "spent_eur": 0.0,
                "returned_eur": 0.0,
                "paper_modeled": 0,
            }
        return lab

    def set_stage(self, stage: str) -> dict[str, Any]:
        stage = str(stage or "").strip()
        if stage not in (STAGE_PAPER, STAGE_PROPOSE, STAGE_MICRO):
            return {"ok": False, "error": "invalid_stage"}
        lab = self._roll_today(self._load_lab())
        lab["stage"] = stage
        lab["updated_at"] = _utc_now()
        self._save_lab(lab)
        return {"ok": True, "stage": stage, "lab": self.panel(bank_eur=lab.get("bank_eur"))}

    def set_bank(self, bank_eur: float) -> dict[str, Any]:
        lab = self._roll_today(self._load_lab())
        lab["bank_eur"] = max(0.0, _safe_float(bank_eur))
        lab["updated_at"] = _utc_now()
        self._save_lab(lab)
        return {"ok": True, "bank_eur": lab["bank_eur"]}

    def capital_laws(self, bank_eur: float) -> dict[str, Any]:
        bank = max(0.0, _safe_float(bank_eur))
        cap = experiment_cap_eur(bank)
        quote = micro_test_quote_eur(bank)
        return {
            "bank_eur": round(bank, 2),
            "max_experiment_eur": round(cap, 4),
            "max_experiment_pct": MAX_EXPERIMENT_PCT,
            "suggested_micro_test_eur": quote,
            "max_concurrent": MAX_CONCURRENT_EXPERIMENTS,
            "reserve_after_20_fails_eur": round(
                max(0.0, bank - 20 * cap), 2
            ),
            "search_spend_allowed": False,
            "toloka_requester_is_not_bank_ru": (
                "Депозит Toloka Requester — бюджет на исполнителей, "
                "не инвестиционный банк Alpha Hunter. Не автосписывать."
            ),
            "bank_pitch_ru": BANK_PITCH_RU,
        }

    def panel(self, *, bank_eur: float | None = None) -> dict[str, Any]:
        self.heal_active_experiments()
        self.heal_director_defaults()
        lab = self._roll_today(self._load_lab())
        if bank_eur is not None:
            lab["bank_eur"] = max(0.0, _safe_float(bank_eur))
        bank = _safe_float(lab.get("bank_eur"), 20.0)
        today = lab.get("today") or {}
        spent = _safe_float(today.get("spent_eur"))
        returned = _safe_float(today.get("returned_eur"))
        net = round(returned - spent, 2)
        life = lab.get("lifetime") or {}
        strategies = self._load_strategies()
        ranked = sorted(
            strategies.get("items") or [],
            key=lambda s: (-_safe_float(s.get("modeled_roi")), -int(s.get("trials") or 0)),
        )[:12]
        stage = str(lab.get("stage") or STAGE_PAPER)
        dcfg = self._director_cfg(lab)
        dcfg.pop("_migrated", None)
        pay = lab.get("payout") if isinstance(lab.get("payout"), dict) else {}
        available = _safe_float(pay.get("available_eur"))
        import os

        auto_stripe = os.environ.get("GENESIS_ALPHA_HUNTER_AUTO_STRIPE", "").strip().lower() in (
            "1",
            "true",
            "yes",
        )
        director_brief = (lab.get("director") or {}).get("last_brief")
        scan_sec = int(lab.get("scan_interval_sec") or DEFAULT_SCAN_INTERVAL_SEC)
        opps = self.list_opportunities(limit=30)
        lab_mode = str(lab.get("lab_mode") or LAB_MODE_ANALYSIS)
        analysis_ready = bool(lab.get("analysis_ready"))
        proposals_waiting = any(
            str(o.get("lifecycle") or "") == LC_WAITING_APPROVAL for o in opps
        )
        if not analysis_ready:
            next_action_ru = (
                "Сейчас: Paper day (или Scan Income Sources) — €0. "
                "Потом Propose top 3 → «→ LIVE» → Одобрить."
            )
            next_step = "paper"
        elif lab_mode != LAB_MODE_LIVE and not proposals_waiting:
            next_action_ru = (
                "Анализ готов. Нажмите «Propose top 3», затем «→ LIVE Income Lab», "
                "потом «Одобрить» на предложении."
            )
            next_step = "propose"
        elif lab_mode != LAB_MODE_LIVE:
            next_action_ru = (
                "Есть предложения. Нажмите «→ LIVE Income Lab» — тогда появится «Одобрить»."
            )
            next_step = "go_live"
        else:
            next_action_ru = (
                "LIVE. Нажмите «Одобрить» на карточке предложения (микро-тест ≤2% банка)."
            )
            next_step = "approve"
        return {
            "ok": True,
            "product_name": "Virtus Core Alpha Hunter",
            "section": "Opportunity Discovery",
            "engine": "Alpha Hunter — Opportunity Discovery Engine",
            "engine_law_ru": (
                "Не движок гарантированного заработка. "
                "Поиск рынков → evidence → prepare → Approve → realized only."
            ),
            "owner_only": True,
            "commercial_product": False,
            "law_ru": LAW_RU,
            "search_law_ru": SEARCH_SPEND_FORBIDDEN_RU,
            "bank_pitch_ru": BANK_PITCH_RU,
            "lab_mode": lab_mode,
            "analysis_ready": analysis_ready,
            "next_step": next_step,
            "next_action_ru": next_action_ru,
            "scan": {
                "interval_sec": scan_sec,
                "interval_label": f"{scan_sec // 60}m",
                "allowed_sec": list(SCAN_INTERVALS_SEC),
                "allowed_labels": list(SCAN_INTERVAL_LABELS),
                "last_scan_at": lab.get("last_scan_at"),
                "next_scan_at": lab.get("next_scan_at"),
                "law_ru": (
                    "Быстрый каденс 2м/5м/10м/15м/30м — больше шансов заметить рынок рано. "
                    "Сначала анализ, потом предложения, потом LIVE."
                ),
            },
            "lifecycle": list(OPPORTUNITY_LIFECYCLE),
            "opportunities": opps,
            "stage": stage,
            "stage_ru": {
                STAGE_PAPER: "Stage 1 — без риска: только моделирование, €0",
                STAGE_PROPOSE: "Stage 2 — топ стратегий на одобрение микро-теста",
                STAGE_MICRO: "Stage 3 — микро-эксперименты ≤2% банка после Approve",
            }.get(stage, stage),
            "pipeline": list(DIRECTOR_PIPELINE),
            "director": {
                **dcfg,
                "role_ru": "Инвестиционный директор: мелкие €2 не показывает",
                "last_brief": director_brief,
                "adaptive": self.adaptive_threshold_suggestion(lab),
                "edge_ru": (
                    "Настоящее преимущество — ранний поиск новых рынков/площадок, "
                    "подготовка публикации продукта и Approve — не автоматическое создание денег."
                ),
            },
            "payout": {
                "available_eur": round(available, 2),
                "pending_eur": round(_safe_float(pay.get("pending_eur")), 2),
                "withdrawn_eur": round(_safe_float(pay.get("withdrawn_eur")), 2),
                "auto_stripe_enabled": auto_stripe,
                "message_ru": (
                    f"Доступно €{available:,.2f}. Нажмите «Вывести»."
                    if available > 0 and not auto_stripe
                    else (
                        f"Доступно €{available:,.2f}. Авто-вывод на Stripe включён."
                        if available > 0 and auto_stripe
                        else "Нет подтверждённых выплат для вывода. (Не выдумываем баланс.)"
                    )
                ),
                "law_ru": (
                    "В desk попадает только realized оплата. "
                    "Фраза «ИИ заработал €X» запрещена без реального источника."
                ),
            },
            "capital": self.capital_laws(bank),
            "lab": {
                "capital_eur": round(bank, 2),
                "active_experiments": int(lab.get("active_experiments") or 0),
                "today": {
                    "spent_eur": round(spent, 2),
                    "returned_eur": round(returned, 2),
                    "net_eur": net,
                    "paper_modeled": int(today.get("paper_modeled") or 0),
                },
                "lifetime": {
                    "experiments": int(life.get("experiments") or 0),
                    "success": int(life.get("success") or 0),
                    "failed": int(life.get("failed") or 0),
                    "paper_opportunities": int(life.get("paper_opportunities") or 0),
                    "best_strategy_id": life.get("best_strategy_id"),
                    "avg_realized_roi": life.get("avg_realized_roi"),
                    "new_markets_found": int(life.get("new_markets_found") or 0),
                },
                "search_spend_eur": 0.0,
            },
            "venues": list(LEGAL_VENUES),
            "free_sources": list(FREE_SOURCES),
            "hunters": {
                "catalog_size": 1000,
                "families": [h[0] for h in HUNTER_SEEDS],
                "crazy_ru": (
                    "Crazy Hunter: каждый день ищет новый легальный способ. "
                    "До whitelist — только research, без spend."
                ),
                "new_market_ru": (
                    "New Market Hunter: новые AI/API маркетплейсы — "
                    "проверить правила, подготовить публикацию, показать на Approve."
                ),
            },
            "llm_director": {
                "law_ru": (
                    "Поиск идёт через уже оплаченные ИИ-API + бесплатные источники. "
                    "Банк не тратится на поиск."
                ),
                "roles": list(LLM_DIRECTOR_ROLES),
            },
            "strategies_ranked": ranked,
            "strategy_marketplace": [
                strategy_marketplace_card(s, number=i)
                for i, s in enumerate(ranked[:20], start=1)
            ],
            "honesty_ru": (
                "Нет легального рынка, где стабильно €0.50→€0.70 за минуты по кнопке. "
                "Alpha Hunter ищет рынки с деньгами (Income Sources) и готовит действия — "
                "не новостную ленту и не «волшебную кнопку»."
            ),
            "income_layer": self.income_sources_panel(),
        }

    def _load_strategies(self) -> dict[str, Any]:
        path = self._path(STRATEGIES_FILE)
        if not path.exists():
            return {"items": []}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {"items": []}
        except (OSError, json.JSONDecodeError):
            return {"items": []}

    def _save_strategies(self, data: dict[str, Any]) -> None:
        path = self._path(STRATEGIES_FILE)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def run_paper_day(
        self,
        *,
        bank_eur: float = 20.0,
        opportunities_target: int = 100,
        hunter_sample: int = 100,
    ) -> dict[str, Any]:
        """Stage 1 day: find/model N opportunities, spend €0, rank strategies."""
        lab = self._roll_today(self._load_lab())
        lab["bank_eur"] = max(0.0, _safe_float(bank_eur, lab.get("bank_eur") or 20))
        bank = _safe_float(lab["bank_eur"])
        cap = experiment_cap_eur(bank)
        hunters = build_hunters(max(hunter_sample, 9))[:hunter_sample]

        modeled: list[dict[str, Any]] = []
        rejects = 0
        rejection_reasons: list[str] = []
        dcfg_pre = self._director_cfg(lab)
        dcfg_pre.pop("_migrated", None)
        try:
            import importlib.util as _ilu

            has_browser = _ilu.find_spec("playwright") is not None
        except Exception:
            has_browser = False
        for i, h in enumerate(hunters):
            if len(modeled) >= opportunities_target:
                break
            venue = venue_for_hunter(h["family"])
            if venue is None:
                rejects += 1
                rejection_reasons.append("no_venue")
                continue
            # Deterministic paper model from hunter id (no invented confirmed €)
            digest = hashlib.sha256(
                f"{h['id']}:{lab['today']['date']}".encode()
            ).hexdigest()
            score = int(digest[:8], 16) / 0xFFFFFFFF
            # Modeled ROI if we hypothetically invested `cap` (or 1€ for ranking)
            unit = 1.0 if bank >= 1 else max(cap, 0.01)
            # Spread modeled ROI; many negative — honest
            modeled_roi = round((score - 0.55) * 1.2, 4)  # often negative
            modeled_return = round(unit * (1.0 + modeled_roi), 4)
            ev = round(modeled_return * (0.3 + score * 0.5) - unit, 4)
            row = {
                "id": f"paper_{h['id']}_{digest[:6]}",
                "hunter_id": h["id"],
                "hunter_family": h["family"],
                "hunter_title": h["title"],
                "venue_id": venue.get("id"),
                "venue_ru": venue.get("title_ru"),
                "hypothetical_invest_eur": unit,
                "modeled_return_eur": modeled_return,
                "modeled_roi": modeled_roi,
                "modeled_ev_eur": ev,
                "spend_eur": 0.0,
                "source": "paper_model",
                "note_ru": "Модель «что было бы» — денег не потрачено.",
            }
            market_discovery = h["family"] in ("crazy", "new_market")
            if market_discovery:
                row["novelty_ru"] = (
                    "Новый рынок / novelty: кандидат вне привычного списка. "
                    "Подготовить публикацию; spend только после whitelist + Approve."
                )
                row["market_discovery"] = True
            evidence = build_opportunity_evidence(
                family=str(h["family"]),
                venue=venue,
                score=score,
                digest=digest,
                market_discovery=market_discovery,
            )
            profit = expected_profit_range(
                modeled_roi=_safe_float(row.get("modeled_roi")),
                family=str(h["family"]),
                confidence=evidence.get("confidence"),
            )
            row["evidence"] = evidence
            row["expected_profit"] = profit
            row["expected_profit_eur"] = profit["mid_eur"]
            # Classify early if already fails floors (primary reason for breakdown)
            if not passes_director_threshold(
                expected_profit_eur=profit["mid_eur"],
                modeled_roi=modeled_roi,
                min_profit_eur=dcfg_pre["min_expected_profit_eur"],
                min_roi_pct=dcfg_pre["min_roi_pct"],
            ):
                row["reject_reason"] = classify_rejection_reason(
                    modeled_roi=modeled_roi,
                    expected_profit_mid=profit["mid_eur"],
                    min_profit_eur=dcfg_pre["min_expected_profit_eur"],
                    min_roi_pct=dcfg_pre["min_roi_pct"],
                    evidence=evidence,
                    has_browser=has_browser,
                )
            elif not evidence.get("signals", {}).get("tos_auto_publish_ok"):
                # Passes €/ROI but blocked on evidence gates in conservative review
                if dcfg_pre["min_expected_profit_eur"] >= 400:
                    row["reject_reason"] = "no_tos_confirmation"
            modeled.append(row)

        # Update strategy scores (paper only)
        strategies = self._load_strategies()
        items = {
            str(s.get("id")): s
            for s in (strategies.get("items") or [])
            if isinstance(s, dict) and s.get("id")
        }
        new_markets = 0
        for row in modeled:
            sid = f"strat_{row['hunter_family']}_{row['venue_id']}"
            cur = items.get(sid) or {
                "id": sid,
                "family": row["hunter_family"],
                "venue_id": row["venue_id"],
                "title_ru": f"{row['hunter_family']} @ {row['venue_ru']}",
                "trials": 0,
                "modeled_roi_sum": 0.0,
                "modeled_roi": 0.0,
                "positive_models": 0,
                "expected_profit_eur": 0.0,
                "market_discovery": False,
            }
            cur["trials"] = int(cur.get("trials") or 0) + 1
            cur["modeled_roi_sum"] = _safe_float(cur.get("modeled_roi_sum")) + _safe_float(
                row.get("modeled_roi")
            )
            cur["modeled_roi"] = round(
                cur["modeled_roi_sum"] / max(1, cur["trials"]), 4
            )
            cur["expected_profit_eur"] = director_expected_profit_eur(
                modeled_roi=cur["modeled_roi"],
                family=str(row["hunter_family"]),
            )
            if row.get("market_discovery"):
                cur["market_discovery"] = True
                new_markets += 1
            if _safe_float(row.get("modeled_ev_eur")) > 0:
                cur["positive_models"] = int(cur.get("positive_models") or 0) + 1
            items[sid] = cur

        ranked = sorted(
            items.values(),
            key=lambda s: (
                -_safe_float(s.get("modeled_roi")),
                -int(s.get("positive_models") or 0),
                -int(s.get("trials") or 0),
            ),
        )
        strategies["items"] = ranked
        strategies["updated_at"] = _utc_now()
        self._save_strategies(strategies)

        # Persist opportunity cards with Evidence + Lifecycle
        opp_store = self._load_opportunities()
        by_id = {
            str(o.get("id")): o
            for o in (opp_store.get("items") or [])
            if isinstance(o, dict) and o.get("id")
        }
        for row in modeled:
            fam = str(row.get("hunter_family"))
            oid = f"opp_{fam}_{row.get('venue_id')}_{str(row.get('id'))[-8:]}"
            profit = row.get("expected_profit") or expected_profit_range(
                modeled_roi=_safe_float(row.get("modeled_roi")), family=fam
            )
            evidence = row.get("evidence") or {}
            lifecycle = LC_DISCOVERED
            sig = evidence.get("signals") if isinstance(evidence.get("signals"), dict) else {}
            if sig.get("has_api") and sig.get("tos_auto_publish_ok"):
                lifecycle = LC_VERIFIED
            card = by_id.get(oid) or {"id": oid, "lifecycle_history": []}
            card.update(
                {
                    "id": oid,
                    "number": abs(hash(oid)) % 900 + 100,
                    "title_ru": f"{row.get('hunter_title')} · {row.get('venue_ru')}",
                    "family": fam,
                    "venue_id": row.get("venue_id"),
                    "strategy_id": f"strat_{fam}_{row.get('venue_id')}",
                    "market_discovery": bool(row.get("market_discovery")),
                    "evidence": evidence,
                    "expected_profit": profit,
                    "modeled_roi": row.get("modeled_roi"),
                    "lifecycle": lifecycle,
                    "updated_at": _utc_now(),
                }
            )
            if not card.get("lifecycle_history"):
                card = self._advance_lifecycle(card, lifecycle)
            by_id[oid] = card
        dcfg_tmp = self._director_cfg(lab)
        for card in list(by_id.values()):
            profit = card.get("expected_profit") or {}
            if passes_director_threshold(
                expected_profit_eur=_safe_float(profit.get("mid_eur")),
                modeled_roi=_safe_float(card.get("modeled_roi")),
                min_profit_eur=dcfg_tmp["min_expected_profit_eur"],
                min_roi_pct=dcfg_tmp["min_roi_pct"],
                expected_low_eur=_safe_float(profit.get("low_eur")),
            ):
                if card.get("lifecycle") in (LC_DISCOVERED, LC_VERIFIED):
                    card = self._advance_lifecycle(card, LC_PREPARED)
                    by_id[card["id"]] = card
        opp_store["items"] = list(by_id.values())
        opp_store["updated_at"] = _utc_now()
        self._save_opportunities(opp_store)

        # Persist paper log (no money)
        path = self._path(PAPER_LOG_FILE)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(
                json.dumps(
                    {
                        "at": _utc_now(),
                        "modeled": len(modeled),
                        "rejects": rejects,
                        "spend_eur": 0.0,
                        "top3": [
                            {
                                "id": s.get("id"),
                                "modeled_roi": s.get("modeled_roi"),
                                "trials": s.get("trials"),
                            }
                            for s in ranked[:3]
                        ],
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )

        today = lab["today"]
        today["paper_modeled"] = int(today.get("paper_modeled") or 0) + len(modeled)
        life = lab.setdefault("lifetime", {})
        life["paper_opportunities"] = int(life.get("paper_opportunities") or 0) + len(
            modeled
        )
        if ranked:
            life["best_strategy_id"] = ranked[0].get("id")
        life["new_markets_found"] = int(life.get("new_markets_found") or 0) + new_markets
        lab["search_spend_eur"] = 0.0
        dcfg = self._director_cfg(lab)
        dcfg.pop("_migrated", None)
        mode_meta = SEARCH_MODES.get(str(dcfg.get("search_mode")), SEARCH_MODES[DEFAULT_SEARCH_MODE])
        kept_dir = []
        for s in ranked:
            profit = expected_profit_range(
                modeled_roi=_safe_float(s.get("modeled_roi")),
                family=str(s.get("family") or ""),
            )
            s["expected_profit"] = profit
            s["expected_profit_eur"] = profit["mid_eur"]
            if bool(dcfg.get("rank_all_positive")):
                if _safe_float(s.get("modeled_roi")) > 0:
                    kept_dir.append(s)
            elif passes_director_threshold(
                expected_profit_eur=profit["mid_eur"],
                modeled_roi=_safe_float(s.get("modeled_roi")),
                min_profit_eur=dcfg["min_expected_profit_eur"],
                min_roi_pct=dcfg["min_roi_pct"],
            ):
                kept_dir.append(s)
        # Explorer ranks by discovery score; others keep ROI order
        if bool(dcfg.get("rank_all_positive")) and kept_dir:
            kept_dir = sorted(
                kept_dir,
                key=lambda s: -int(
                    opportunity_discovery_score(
                        modeled_roi=_safe_float(s.get("modeled_roi")),
                        novelty=0.55 if s.get("market_discovery") else 0.35,
                    ).get("total")
                    or 0
                ),
            )
        discovery_fallback = False
        # Newbie/Balanced: soft surface best positives so Approve path exists while learning
        if (
            not kept_dir
            and dcfg["min_expected_profit_eur"] < 400
            and not bool(dcfg.get("rank_all_positive"))
        ):
            positive = [s for s in ranked if _safe_float(s.get("modeled_roi")) > 0][:5]
            if not positive and ranked:
                positive = ranked[:3]
            kept_dir = positive
            discovery_fallback = bool(kept_dir)
            for s in kept_dir:
                for card in by_id.values():
                    if card.get("strategy_id") == s.get("id"):
                        self._advance_lifecycle(card, LC_PREPARED)
            opp_store["items"] = list(by_id.values())
            self._save_opportunities(opp_store)

        for row in modeled:
            reason = row.get("reject_reason")
            if reason:
                rejection_reasons.append(str(reason))
            elif not any(s.get("id") == f"strat_{row['hunter_family']}_{row['venue_id']}" for s in kept_dir):
                # Strategy not in kept — count as filter reject if not already tagged
                rejection_reasons.append(
                    classify_rejection_reason(
                        modeled_roi=_safe_float(row.get("modeled_roi")),
                        expected_profit_mid=_safe_float(
                            (row.get("expected_profit") or {}).get("mid_eur")
                        ),
                        min_profit_eur=dcfg["min_expected_profit_eur"],
                        min_roi_pct=dcfg["min_roi_pct"],
                        evidence=row.get("evidence") if isinstance(row.get("evidence"), dict) else {},
                        has_browser=has_browser,
                    )
                )

        # Cap breakdown length to modeled+rejects for honesty
        rejection_breakdown = build_rejection_breakdown(rejection_reasons)
        markets_checked = len({str(r.get("venue_id")) for r in modeled if r.get("venue_id")})
        coverage = {
            "sources_checked": len(FREE_SOURCES) + len(LEGAL_VENUES) + len(hunters),
            "strategies_modeled": len(ranked),
            "markets_checked": max(markets_checked, len(LEGAL_VENUES)),
            "hunters_sampled": len(hunters),
            "opportunities_modeled": len(modeled),
        }
        rejected_n = max(0, len(modeled) - len(kept_dir)) + rejects
        if not kept_dir:
            brief = honest_empty_brief(
                coverage=coverage,
                mode=mode_meta,
                rejection_breakdown=rejection_breakdown,
                found=len(modeled),
                rejected=rejected_n,
            )
        else:
            brief = {
                "found": len(modeled),
                "rejected": rejected_n,
                "kept": len(kept_dir),
                "empty_ok": False,
                "discovery_fallback": discovery_fallback,
                "coverage": coverage,
                "rejection_breakdown": rejection_breakdown,
                "search_mode": dcfg.get("search_mode"),
                "message_ru": (
                    (
                        f"Анализ: нашёл {len(modeled)}. Строгий отбор пуст — "
                        f"показываю {len(kept_dir)} лучших для prepare "
                        f"(режим {mode_meta.get('title')}: "
                        f"€{dcfg['min_expected_profit_eur']:.0f} / "
                        f"ROI {dcfg['min_roi_pct']:.0f}%). "
                        "Дальше: Propose top 3 → LIVE → Одобрить."
                    )
                    if discovery_fallback
                    else (
                        f"Анализ: нашёл {len(modeled)} возможностей. "
                        f"{rejected_n} отклонил "
                        f"(режим {mode_meta.get('title')}: "
                        f"€{dcfg['min_expected_profit_eur']:.0f} / "
                        f"ROI {dcfg['min_roi_pct']:.0f}%). "
                        f"{len(kept_dir)} подготовлено с Evidence. "
                        "Дальше: Propose top 3 → кнопка «→ LIVE» → Одобрить."
                    )
                ),
                "actions": [
                    {"id": "why", "label_ru": "Почему ничего не найдено?", "action": "show_breakdown"},
                    {"id": "continue", "label_ru": "Продолжить поиск", "action": "paper_day"},
                ],
            }
        from datetime import timedelta

        scan_sec = int(lab.get("scan_interval_sec") or DEFAULT_SCAN_INTERVAL_SEC)
        now = datetime.now(timezone.utc)
        lab["last_scan_at"] = now.isoformat()
        lab["next_scan_at"] = (now + timedelta(seconds=scan_sec)).isoformat()
        lab["analysis_ready"] = len(modeled) > 0
        lab["lab_mode"] = LAB_MODE_ANALYSIS
        lab.setdefault("director", {})["last_brief"] = brief
        lab["updated_at"] = _utc_now()
        self._save_lab(lab)

        top3 = []
        for s in (kept_dir or ranked)[:3]:
            profit = s.get("expected_profit") or expected_profit_range(
                modeled_roi=_safe_float(s.get("modeled_roi")),
                family=str(s.get("family") or ""),
            )
            roi_pct = round(_safe_float(s.get("modeled_roi")) * 100, 1)
            ev = None
            for o in self.list_opportunities(limit=80):
                if o.get("strategy_id") == s.get("id"):
                    ev = o.get("evidence")
                    break
            top3.append(
                {
                    "strategy_id": s.get("id"),
                    "title_ru": s.get("title_ru"),
                    "modeled_roi_pct": roi_pct,
                    "expected_profit": profit,
                    "evidence": ev,
                    "lifecycle": LC_PREPARED if s in kept_dir else LC_DISCOVERED,
                    "market_discovery": bool(s.get("market_discovery")),
                    "trials": s.get("trials"),
                    "test_cost_eur": micro_test_quote_eur(bank),
                    "pitch_ru": (
                        f"«{s.get('title_ru')}»: Expected Profit {profit['display_ru']}, "
                        f"Confidence {profit['confidence_pct']}%, "
                        f"Worst €{profit['worst_case_eur']:,.0f}, "
                        f"Best €{profit['best_case_eur']:,.0f}."
                    ),
                }
            )

        return {
            "ok": True,
            "stage": STAGE_PAPER,
            "lab_mode": LAB_MODE_ANALYSIS,
            "analysis_ready": True,
            "spend_eur": 0.0,
            "modeled_count": len(modeled),
            "rejects": rejects,
            "hunters_sampled": len(hunters),
            "director_brief": brief,
            "top_strategies": top3,
            "opportunities": self.list_opportunities(limit=20),
            "message_ru": brief["message_ru"] + " Paper spend: €0.",
            "lab": self.panel(bank_eur=bank),
        }

    def propose_top(self, *, bank_eur: float | None = None, n: int = 3) -> dict[str, Any]:
        """Stage 2 — after analysis: shortlist with Evidence + ranges (no single €)."""
        lab = self._roll_today(self._load_lab())
        if not lab.get("analysis_ready"):
            return {
                "ok": False,
                "error": "analysis_not_ready",
                "detail_ru": "Сначала анализ (Paper / скан). Предложения — только когда готово.",
                "lab": self.panel(),
            }
        if bank_eur is not None:
            lab["bank_eur"] = max(0.0, _safe_float(bank_eur))
            self._save_lab(lab)
        bank = _safe_float(lab.get("bank_eur"), 20)
        dcfg = self._director_cfg(lab)
        strategies = self._load_strategies()
        ranked = sorted(
            strategies.get("items") or [],
            key=lambda s: (
                -_safe_float(s.get("expected_profit_eur")),
                -_safe_float(s.get("modeled_roi")),
                -int(s.get("trials") or 0),
            ),
        )
        found_n = len(ranked)
        # Director: drop penny deals (use range low — never single promised €)
        eligible = []
        for s in ranked:
            if _safe_float(s.get("modeled_roi")) <= 0:
                continue
            profit = s.get("expected_profit") or expected_profit_range(
                modeled_roi=_safe_float(s.get("modeled_roi")),
                family=str(s.get("family") or ""),
            )
            s["expected_profit"] = profit
            s["expected_profit_eur"] = profit["mid_eur"]
            if passes_director_threshold(
                expected_profit_eur=profit["mid_eur"],
                modeled_roi=_safe_float(s.get("modeled_roi")),
                min_profit_eur=dcfg["min_expected_profit_eur"],
                min_roi_pct=dcfg["min_roi_pct"],
            ):
                eligible.append(s)
        rejected_n = found_n - len(eligible)
        shortlist = eligible[:n]
        # Discovery fallback (not in strict €500+ mode)
        if not shortlist and dcfg["min_expected_profit_eur"] < 400:
            shortlist = [
                s
                for s in ranked
                if _safe_float(s.get("modeled_roi")) > 0
            ][:n]
            if not shortlist:
                shortlist = ranked[:n]
            for s in shortlist:
                profit = expected_profit_range(
                    modeled_roi=_safe_float(s.get("modeled_roi")),
                    family=str(s.get("family") or ""),
                )
                s["expected_profit"] = profit
                s["expected_profit_eur"] = profit["mid_eur"]
        quote = micro_test_quote_eur(bank)
        if not shortlist:
            brief = {
                "found": found_n,
                "rejected": rejected_n,
                "kept": 0,
                "message_ru": (
                    f"Я нашёл {found_n} возможностей. {rejected_n} отклонил. "
                    "0 оставил — нет сделок выше порога директора "
                    f"(мин. €{dcfg['min_expected_profit_eur']:.0f} или ROI "
                    f"{dcfg['min_roi_pct']:.0f}%). Нажмите Paper day снова "
                    "или смягчите порог (Discovery €100 / 12%)."
                ),
            }
            lab.setdefault("director", {})["last_brief"] = brief
            self._save_lab(lab)
            return {
                "ok": True,
                "found": False,
                "director_brief": brief,
                "message_ru": brief["message_ru"],
                "proposals": [],
                "lab": self.panel(bank_eur=bank),
            }
        proposals = []
        opp_store = self._load_opportunities()
        opp_items = list(opp_store.get("items") or [])
        for idx, s in enumerate(shortlist, start=1):
            profit = expected_profit_range(
                modeled_roi=_safe_float(s.get("modeled_roi")),
                family=str(s.get("family") or ""),
            )
            roi_pct = round(_safe_float(s.get("modeled_roi")) * 100, 1)
            ev = s.get("evidence")
            opp_id = None
            for i, o in enumerate(opp_items):
                if not isinstance(o, dict):
                    continue
                if o.get("strategy_id") == s.get("id"):
                    ev = o.get("evidence") or ev
                    o = self._advance_lifecycle(o, LC_WAITING_APPROVAL)
                    opp_items[i] = o
                    opp_id = o.get("id")
                    break
            proposals.append(
                {
                    "rank": idx,
                    "opportunity_id": opp_id,
                    "strategy_id": s.get("id"),
                    "title_ru": s.get("title_ru"),
                    "modeled_roi_pct": roi_pct,
                    "expected_profit": profit,
                    "evidence": ev,
                    "lifecycle": LC_WAITING_APPROVAL,
                    "market_discovery": bool(s.get("market_discovery")),
                    "paper_trials": s.get("trials"),
                    "test_cost_eur": quote,
                    "venue_id": s.get("venue_id"),
                    "pipeline_ready_ru": (
                        "DISCOVERED→VERIFIED→PREPARED→WAITING APPROVAL · "
                        "затем RUNNING→PAYMENT→PAID→WITHDRAWN"
                    ),
                    "pitch_ru": (
                        f"✅ Opportunity #{idx}"
                        + (" · new market" if s.get("market_discovery") else "")
                        + f". Expected Profit {profit['display_ru']}. "
                        f"Confidence {profit['confidence_pct']}%. "
                        f"Worst €{profit['worst_case_eur']:,.0f} · "
                        f"Best €{profit['best_case_eur']:,.0f}. "
                        f"Микро-тест {quote}€. Одобрить?"
                    ),
                }
            )
        opp_store["items"] = opp_items
        self._save_opportunities(opp_store)
        best = proposals[0]["expected_profit"]
        brief = {
            "found": found_n,
            "rejected": rejected_n,
            "kept": len(shortlist),
            "expected_profit": best,
            "message_ru": (
                f"Я нашёл {found_n} возможностей. {rejected_n} отклонил. "
                f"{len(shortlist)} оставил. "
                f"Expected Profit {best['display_ru']} "
                f"(Confidence {best['confidence_pct']}%). "
                "Нужно ваше одобрение. Переведите Lab в LIVE, затем Approve."
            ),
        }
        lab["stage"] = STAGE_PROPOSE
        lab.setdefault("director", {})["last_brief"] = brief
        lab["updated_at"] = _utc_now()
        self._save_lab(lab)
        return {
            "ok": True,
            "found": True,
            "director_brief": brief,
            "message_ru": brief["message_ru"],
            "proposals": proposals,
            "opportunities": self.list_opportunities(limit=20),
            "lab": self.panel(bank_eur=bank),
        }

    def assert_experiment_allowed(
        self, *, bank_eur: float, cost_eur: float, active: int
    ) -> dict[str, Any]:
        """Gate before any real spend."""
        lab = self._load_lab()
        stage = str(lab.get("stage") or STAGE_PAPER)
        if stage == STAGE_PAPER:
            return {
                "ok": False,
                "error": "stage_paper",
                "detail_ru": "Stage 1: траты запрещены. Сначала paper, затем Propose → Approve.",
            }
        cap = experiment_cap_eur(bank_eur)
        if cost_eur > cap + 1e-9:
            return {
                "ok": False,
                "error": "over_2pct",
                "detail_ru": (
                    f"Нельзя потратить больше 2% капитала за эксперимент "
                    f"({cost_eur}€ > {cap}€)."
                ),
                "max_experiment_eur": cap,
            }
        if active >= MAX_CONCURRENT_EXPERIMENTS:
            return {
                "ok": False,
                "error": "max_concurrent",
                "detail_ru": f"Максимум {MAX_CONCURRENT_EXPERIMENTS} активных экспериментов.",
            }
        return {"ok": True, "max_experiment_eur": cap, "stage": stage}

    def record_experiment_result(
        self,
        *,
        spent_eur: float,
        returned_eur: float,
        success: bool,
        strategy_id: str | None = None,
    ) -> dict[str, Any]:
        """Record *realized* outcome only. Credits payout desk — never invents."""
        lab = self._roll_today(self._load_lab())
        today = lab["today"]
        today["spent_eur"] = round(
            _safe_float(today.get("spent_eur")) + max(0.0, spent_eur), 2
        )
        today["returned_eur"] = round(
            _safe_float(today.get("returned_eur")) + max(0.0, returned_eur), 2
        )
        life = lab.setdefault("lifetime", {})
        life["experiments"] = int(life.get("experiments") or 0) + 1
        if success:
            life["success"] = int(life.get("success") or 0) + 1
        else:
            life["failed"] = int(life.get("failed") or 0) + 1
        # avg realized ROI
        inv = max(spent_eur, 1e-9)
        sample = (returned_eur - spent_eur) / inv
        prev = life.get("avg_realized_roi")
        n = int(life["experiments"])
        if prev is None:
            life["avg_realized_roi"] = round(sample, 4)
        else:
            life["avg_realized_roi"] = round(
                (float(prev) * (n - 1) + sample) / n, 4
            )
        if strategy_id:
            life["best_strategy_id"] = strategy_id
        # Realized net → payout desk (never from modeled expected profit)
        net = max(0.0, _safe_float(returned_eur) - max(0.0, spent_eur))
        if success and net > 0:
            pay = lab.setdefault("payout", {})
            pay["available_eur"] = round(
                _safe_float(pay.get("available_eur")) + net, 2
            )
            lab["payout"] = pay
            if strategy_id:
                opp_store = self._load_opportunities()
                items = []
                for o in opp_store.get("items") or []:
                    if isinstance(o, dict) and o.get("strategy_id") == strategy_id:
                        o = self._advance_lifecycle(o, LC_WAITING_PAYMENT)
                        o = self._advance_lifecycle(o, LC_PAID)
                    items.append(o)
                opp_store["items"] = items
                self._save_opportunities(opp_store)
            # Optional auto Stripe path (still no invented €)
            import os

            if os.environ.get("GENESIS_ALPHA_HUNTER_AUTO_STRIPE", "").strip().lower() in (
                "1",
                "true",
                "yes",
            ):
                self._save_lab(lab)
                self.request_withdraw(amount_eur=net, confirm=True, auto=True)
                lab = self._load_lab()
        lab["active_experiments"] = max(
            0, int(lab.get("active_experiments") or 0) - 1
        )
        lab["updated_at"] = _utc_now()
        self._save_lab(lab)
        return {"ok": True, "lab": self.panel()}

    def request_withdraw(
        self,
        *,
        amount_eur: float | None = None,
        confirm: bool = True,
        auto: bool = False,
    ) -> dict[str, Any]:
        """Stripe desk: withdraw realized available only after confirm (or auto env)."""
        lab = self._roll_today(self._load_lab())
        pay = lab.setdefault("payout", {})
        available = _safe_float(pay.get("available_eur"))
        amount = available if amount_eur is None else _safe_float(amount_eur)
        if amount <= 0:
            return {
                "ok": False,
                "error": "nothing_to_withdraw",
                "detail_ru": "Нет подтверждённых средств. Не выдумываем баланс.",
            }
        if amount > available + 1e-9:
            return {
                "ok": False,
                "error": "above_available",
                "detail_ru": f"Доступно только €{available:,.2f}.",
                "available_eur": available,
            }
        if not confirm and not auto:
            return {
                "ok": False,
                "error": "confirm_required",
                "detail_ru": (
                    f"Доступно €{available:,.2f}. Нажмите «Вывести» для подтверждения."
                ),
                "available_eur": available,
            }
        # Record intent — live Stripe transfer is external (Farm/Payout Manager)
        pay["available_eur"] = round(available - amount, 2)
        pay["withdrawn_eur"] = round(
            _safe_float(pay.get("withdrawn_eur")) + amount, 2
        )
        pay["last_withdraw"] = {
            "at": _utc_now(),
            "amount_eur": round(amount, 2),
            "mode": "auto_stripe" if auto else "owner_confirm",
            "status": "queued_for_stripe",
            "note_ru": (
                "Заявка на вывод зафиксирована. Фактический Stripe payout — "
                "через Payout Manager / owner Stripe. Не считаем деньги «уже на счёте» "
                "пока Stripe не подтвердит."
            ),
        }
        lab["payout"] = pay
        lab["updated_at"] = _utc_now()
        self._save_lab(lab)
        opp_store = self._load_opportunities()
        items = []
        for o in opp_store.get("items") or []:
            if isinstance(o, dict) and o.get("lifecycle") in (LC_PAID, LC_WAITING_PAYMENT):
                o = self._advance_lifecycle(o, LC_WITHDRAWN)
            items.append(o)
        opp_store["items"] = items
        self._save_opportunities(opp_store)
        return {
            "ok": True,
            "withdrawn_eur": round(amount, 2),
            "available_eur": pay["available_eur"],
            "message_ru": (
                f"Вывод €{amount:,.2f} поставлен в очередь на Stripe. "
                f"Остаток доступно: €{pay['available_eur']:,.2f}."
            ),
            "last_withdraw": pay["last_withdraw"],
            "lab": self.panel(),
        }

    def bump_active(self, delta: int = 1) -> None:
        lab = self._load_lab()
        lab["active_experiments"] = max(
            0, int(lab.get("active_experiments") or 0) + delta
        )
        self._save_lab(lab)

    def approve_micro_test(
        self,
        strategy_id: str,
        *,
        bank_eur: float | None = None,
    ) -> dict[str, Any]:
        """Stage 2→3: owner approves one micro-test (≤2%). Search still €0.

        Default execution is prepare_dry_run — profit never invented.
        Live spend only if GENESIS_INCOME_ENGINE_LIVE=1 and stage is micro_spend.
        """
        import os

        lab = self._roll_today(self._load_lab())
        if bank_eur is not None:
            lab["bank_eur"] = max(0.0, _safe_float(bank_eur))
        bank = _safe_float(lab.get("bank_eur"), 20.0)
        sid = str(strategy_id or "").strip()
        strategies = self._load_strategies()
        item = next(
            (
                s
                for s in (strategies.get("items") or [])
                if isinstance(s, dict) and str(s.get("id")) == sid
            ),
            None,
        )
        if not item:
            return {"ok": False, "error": "strategy_not_found"}

        if str(lab.get("lab_mode") or LAB_MODE_ANALYSIS) != LAB_MODE_LIVE:
            return {
                "ok": False,
                "error": "not_live",
                "detail_ru": (
                    "Сначала анализ → Propose → кнопка «В LIVE Income Lab», "
                    "потом Approve."
                ),
            }

        quote = micro_test_quote_eur(bank)
        active = int(lab.get("active_experiments") or 0)
        stage = str(lab.get("stage") or STAGE_PAPER)
        if stage == STAGE_PAPER:
            # Approving a proposal implies move to propose gate, then prepare
            lab["stage"] = STAGE_PROPOSE
            self._save_lab(lab)
            stage = STAGE_PROPOSE

        gate = self.assert_experiment_allowed(
            bank_eur=bank, cost_eur=quote, active=active
        )
        if not gate.get("ok"):
            return gate

        venue = venue_for_hunter(str(item.get("family") or ""))
        if venue and not venue.get("spend_allowed_after_approve", True):
            return {
                "ok": False,
                "error": "venue_research_only",
                "detail_ru": (
                    f"Площадка «{venue.get('title_ru')}» — только research. "
                    "Spend запрещён, пока нет явного whitelist на оплату."
                ),
            }

        live = os.environ.get("GENESIS_INCOME_ENGINE_LIVE", "").strip().lower() in (
            "1",
            "true",
            "yes",
        )
        # Micro spend stage required for live; propose = prepare only
        mode = (
            "live_micro"
            if live and stage == STAGE_MICRO and quote > 0
            else "prepare_dry_run"
        )
        spent_now = quote if mode == "live_micro" else 0.0

        exp_id = f"exp_{sid}_{hashlib.sha256(f'{sid}:{_utc_now()}'.encode()).hexdigest()[:8]}"
        row = {
            "at": _utc_now(),
            "experiment_id": exp_id,
            "strategy_id": sid,
            "title_ru": item.get("title_ru"),
            "test_cost_eur": quote,
            "spent_eur": spent_now,
            "returned_eur": 0.0,
            "profit_recorded_eur": 0.0,
            "mode": mode,
            "search_spend_eur": 0.0,
            "status": "running" if mode == "live_micro" else "prepared",
            "pitch_ru": (
                f"Микро-тест стратегии «{item.get('title_ru')}» за {quote}€. "
                "Это проверка гипотезы, не гарантия прибыли."
            ),
        }
        hist = self._path(HISTORY_FILE)
        hist.parent.mkdir(parents=True, exist_ok=True)
        with hist.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

        lab["active_experiments"] = active + 1
        if spent_now > 0:
            today = lab["today"]
            today["spent_eur"] = round(
                _safe_float(today.get("spent_eur")) + spent_now, 2
            )
            lab["bank_eur"] = round(max(0.0, bank - spent_now), 2)
        # Promote to micro_spend after first approve so kill-switch / tracking apply
        if lab.get("stage") == STAGE_PROPOSE:
            lab["stage"] = STAGE_MICRO
        lab["updated_at"] = _utc_now()
        self._save_lab(lab)

        # Strategy card: mark a check started (not a win)
        item["runs"] = int(item.get("runs") or 0) + 1
        item["capital_needed_eur"] = quote
        item["status"] = STATUS_LEARNING
        items = [
            item if str(s.get("id")) == sid else s
            for s in (strategies.get("items") or [])
            if isinstance(s, dict)
        ]
        strategies["items"] = items
        self._save_strategies(strategies)

        # Lifecycle: WAITING_APPROVAL → RUNNING
        opp_store = self._load_opportunities()
        items = []
        for o in opp_store.get("items") or []:
            if isinstance(o, dict) and o.get("strategy_id") == sid:
                o = self._advance_lifecycle(o, LC_RUNNING)
            items.append(o)
        opp_store["items"] = items
        self._save_opportunities(opp_store)

        return {
            "ok": True,
            "experiment": row,
            "message_ru": (
                f"Одобрено. Микро-тест {quote}€ подготовлен"
                + (
                    f", списано {spent_now}€ с банка."
                    if spent_now
                    else " (dry-run: банк не тронут, пока нет LIVE)."
                )
                + " Прибыль не записывается, пока не будет реального возврата."
            ),
            "lab": self.panel(bank_eur=lab.get("bank_eur")),
        }
