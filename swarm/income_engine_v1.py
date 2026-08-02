"""Income Engine v1 / Virtus Core Alpha Hunter — Owner-only Income Lab.

Goal (honest):
  Find legal opportunities with positive *expected* ROI.
  Never invent profit. Never guarantee returns.
  Search costs €0. Spend only after owner approval on micro-experiments.

Capital (venture-style bank):
  Never «give €20, spend all».
  Take €0.20–€1 style tests; max 2% of bank per experiment.
  Max 10 concurrent experiments.
  Toloka Requester deposit is NOT this bank.

Stages (Alpha Hunter):
  1 paper — model only, €0
  2 propose — top strategies, ask Approve for micro-test
  3 micro_spend — tiny spend after Approve
"""

from __future__ import annotations

import json
import math
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from swarm.alpha_hunter_v1 import (
    AlphaHunterLab,
    BANK_PITCH_RU,
    MAX_CONCURRENT_EXPERIMENTS,
    MAX_EXPERIMENT_PCT,
    SEARCH_SPEND_FORBIDDEN_RU,
    STAGE_MICRO,
    STAGE_PAPER,
    STAGE_PROPOSE,
    experiment_cap_eur,
    micro_test_quote_eur,
)

STATE_FILE = "income_engine_v1_state.json"
MISSIONS_FILE = "income_engine_v1_missions.jsonl"
LEARNING_FILE = "income_engine_v1_learning.json"
EXEC_LOG_FILE = "income_engine_v1_exec.jsonl"

MISSION_DURATION_SEC = 300  # up to 5 minutes (sim: fast scan + staged status)
MIN_CONFIDENCE = 0.45
MAX_MISSION_PCT = 0.10  # legacy mission pool display
MAX_PARALLEL_RISK_PCT = 0.30
DEFAULT_SWARM_WORKERS = 16

# Framing for owner UI — never "guaranteed profit"
OWNER_LAW_RU = (
    "Virtus Core Alpha Hunter / Income Lab — оптимизатор ожидаемого ROI. "
    "Поиск бесплатен. Каждый € на эксперимент — только после одобрения. "
    "Прибыль не гарантируется."
)
EMPTY_RESULT_RU = "Подходящих сделок не найдено"
PITCH_TEMPLATE_RU = (
    "Я нашёл возможность с ожидаемой доходностью выше других доступных вариантов. "
    "Вот почему я считаю её лучшей. Одобрить микро-эксперимент?"
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


# ---------------------------------------------------------------------------
# Swarm role catalog (~100 specialists). Each asks one question:
# "Can I legally create more value than the required investment?"
# ---------------------------------------------------------------------------

_ROLE_SEEDS: tuple[tuple[str, str, str], ...] = (
    ("api_marketplace", "API Marketplace", "Новые API-маркетплейсы и провайдерские слоты"),
    ("affiliate", "Affiliate", "Партнёрские программы с измеримым CPA/RevShare"),
    ("bounty", "Bounty", "Баунти и bug-bounty с легальной выплатой"),
    ("grant", "Grant", "Гранты и фонды для digital-продуктов"),
    ("digital_product", "Digital Product", "Цифровые товары с низким CAPEX"),
    ("lead", "Lead", "Запросы компаний на услуги (B2B leads)"),
    ("marketplace", "Marketplace", "Площадки для публикации / продажи услуг"),
    ("dev_program", "Developer Program", "Программы для разработчиков и кредиты"),
    ("research", "Research", "Исследование новых легальных каналов Earn"),
    ("freelance_api", "Freelance API", "Официальные API фриланс-платформ"),
    ("content_license", "Content License", "Лицензирование контента / шаблонов"),
    ("saas_trial", "SaaS Trial", "Партнёрские trial→paid воронки"),
    ("data_label", "Data Label", "Легальная разметка через официальный API"),
    ("ocr_service", "OCR Service", "Продажа OCR/parse как услуги"),
    ("audit_service", "Audit Service", "Website/SEO audit как продукт"),
    ("invoice_parse", "Invoice Parse", "Парсинг счетов как B2B skill"),
    ("rapidapi_slot", "RapidAPI Slot", "Публикация API на RapidAPI (официально)"),
    ("stripe_product", "Stripe Product", "Оформление sellable SKU через Stripe"),
    ("partner_dir", "Partner Directory", "Каталоги партнёров / агентств"),
    ("opensource_sponsor", "OSS Sponsor", "Спонсорские / bounty у open-source"),
)


def build_swarm_roles(target: int = 100) -> list[dict[str, str]]:
    """Expand seed specialties into a swarm of N named agents."""
    roles: list[dict[str, str]] = []
    n = 0
    while len(roles) < target:
        seed_id, title, mission = _ROLE_SEEDS[n % len(_ROLE_SEEDS)]
        variant = (n // len(_ROLE_SEEDS)) + 1
        agent_id = f"{seed_id}_{variant:02d}"
        roles.append(
            {
                "id": agent_id,
                "family": seed_id,
                "title": f"{title} #{variant}",
                "mission": mission,
                "question": "Can I legally create more value than the required investment?",
            }
        )
        n += 1
    return roles


SWARM_ROLES = build_swarm_roles(100)


# Legal opportunity templates — estimates are labeled; no fabricated "confirmed €".
# evidence: none → auto-reject for spend; catalog → research_only; historical → rankable
_OPPORTUNITY_TEMPLATES: tuple[dict[str, Any], ...] = (
    {
        "family": "rapidapi_slot",
        "title": "RapidAPI — publish existing digital skill",
        "title_ru": "RapidAPI — публикация готового digital skill",
        "legal_ok": True,
        "investment_eur": 0.0,
        "expected_return_eur": 0.0,  # unknown until live — EV filter rejects unless learning boosts
        "probability": 0.35,
        "confidence": 0.40,
        "risk": "medium",
        "execution_days": 3,
        "reason_ru": "Официальная публикация API; выплата только после реальных вызовов.",
        "actions": ("configure", "publish", "register"),
        "evidence": "catalog",
        "spend_required": False,
    },
    {
        "family": "affiliate",
        "title": "Affiliate — register + one tracked campaign",
        "title_ru": "Affiliate — регистрация + одна кампания с трекингом",
        "legal_ok": True,
        "investment_eur": 0.50,
        "expected_return_eur": 1.20,
        "probability": 0.55,
        "confidence": 0.50,
        "risk": "medium",
        "execution_days": 2,
        "reason_ru": "Микро-тест партнёрки (не весь банк); CPA без спама и фейковых аккаунтов.",
        "actions": ("register", "configure", "submit"),
        "evidence": "catalog",
        "spend_required": True,
    },
    {
        "family": "audit_service",
        "title": "Website audit — one paid pilot offer",
        "title_ru": "Website audit — одно платное пилотное предложение",
        "legal_ok": True,
        "investment_eur": 0.0,
        "expected_return_eur": 49.0,
        "probability": 0.25,
        "confidence": 0.42,
        "risk": "medium",
        "execution_days": 5,
        "reason_ru": "B2B-пилот на существующем skill; оплата только от реального клиента.",
        "actions": ("generate", "send", "configure"),
        "evidence": "catalog",
        "spend_required": False,
    },
    {
        "family": "bounty",
        "title": "Public bounty — eligible legal program",
        "title_ru": "Публичный bounty — подходящая легальная программа",
        "legal_ok": True,
        "investment_eur": 0.0,
        "expected_return_eur": 0.0,
        "probability": 0.20,
        "confidence": 0.30,
        "risk": "high",
        "execution_days": 7,
        "reason_ru": "Без гарантии выплаты; только официальные программы.",
        "actions": ("research", "submit"),
        "evidence": "none",
        "spend_required": False,
    },
    {
        "family": "grant",
        "title": "Digital grant / credit program",
        "title_ru": "Грант / кредитная программа для digital",
        "legal_ok": True,
        "investment_eur": 0.0,
        "expected_return_eur": 0.0,
        "probability": 0.15,
        "confidence": 0.28,
        "risk": "high",
        "execution_days": 30,
        "reason_ru": "Исследование грантов; деньги не тратятся до одобрения владельца.",
        "actions": ("research", "submit"),
        "evidence": "none",
        "spend_required": False,
    },
    {
        "family": "dev_program",
        "title": "Cloud / API developer credits",
        "title_ru": "Developer credits (cloud / API)",
        "legal_ok": True,
        "investment_eur": 0.0,
        "expected_return_eur": 25.0,
        "probability": 0.40,
        "confidence": 0.48,
        "risk": "low",
        "execution_days": 2,
        "reason_ru": "Официальные кредиты снижают CAPEX; это не вывод € на счёт.",
        "actions": ("register", "configure"),
        "evidence": "catalog",
        "spend_required": False,
    },
    {
        "family": "marketplace",
        "title": "List service on official marketplace",
        "title_ru": "Листинг услуги на официальном маркетплейсе",
        "legal_ok": True,
        "investment_eur": 0.40,
        "expected_return_eur": 1.10,
        "probability": 0.30,
        "confidence": 0.46,
        "risk": "medium",
        "execution_days": 7,
        "reason_ru": "Микро-листинг по правилам площадки; без накрутки и фейковых отзывов.",
        "actions": ("register", "upload", "publish"),
        "evidence": "catalog",
        "spend_required": True,
    },
    {
        "family": "lead",
        "title": "Qualified B2B lead outreach (opt-in / public RFP)",
        "title_ru": "Квалифицированный B2B lead (opt-in / публичный RFP)",
        "legal_ok": True,
        "investment_eur": 0.40,
        "expected_return_eur": 2.00,
        "probability": 0.22,
        "confidence": 0.46,
        "risk": "high",
        "execution_days": 10,
        "reason_ru": "Микро-тест публичного/opt-in запроса; спам запрещён.",
        "actions": ("research", "send"),
        "evidence": "catalog",
        "spend_required": True,
    },
    {
        "family": "digital_product",
        "title": "Package existing deliverable as digital SKU",
        "title_ru": "Упаковать существующий deliverable в digital SKU",
        "legal_ok": True,
        "investment_eur": 0.0,
        "expected_return_eur": 29.0,
        "probability": 0.35,
        "confidence": 0.47,
        "risk": "low",
        "execution_days": 3,
        "reason_ru": "SKU из уже существующего навыка; продажа только через легальный checkout.",
        "actions": ("generate", "configure", "publish"),
        "evidence": "catalog",
        "spend_required": False,
    },
    {
        "family": "api_marketplace",
        "title": "Scan new API marketplaces for provider slots",
        "title_ru": "Скан новых API-маркетплейсов на слоты провайдера",
        "legal_ok": True,
        "investment_eur": 0.0,
        "expected_return_eur": 15.0,
        "probability": 0.28,
        "confidence": 0.44,
        "risk": "medium",
        "execution_days": 5,
        "reason_ru": "Исследование + подготовка листинга; без обхода ToS.",
        "actions": ("research", "configure"),
        "evidence": "catalog",
        "spend_required": False,
    },
)


def expected_value_eur(
    *,
    investment_eur: float,
    expected_return_eur: float,
    probability: float,
) -> float:
    """E[profit] = P(success)*return - investment. Reject if <= 0."""
    p = _clamp(probability, 0.0, 1.0)
    return round(p * expected_return_eur - investment_eur, 4)


def expected_roi_ratio(
    *,
    investment_eur: float,
    expected_return_eur: float,
    probability: float,
) -> float | None:
    """Expected ROI relative to investment; None if no capital at risk."""
    ev = expected_value_eur(
        investment_eur=investment_eur,
        expected_return_eur=expected_return_eur,
        probability=probability,
    )
    if investment_eur <= 0:
        return None if ev <= 0 else float("inf")
    return round(ev / investment_eur, 4)


class IncomeEngineV1:
    """Owner-only swarm opportunity optimizer."""

    def __init__(self, memory: Any, *, swarm_size: int = 100) -> None:
        self._memory = memory
        self._root = Path(getattr(memory, "root", Path(".")))
        self._lock = threading.RLock()
        self._swarm = build_swarm_roles(swarm_size)
        self._lab = AlphaHunterLab(memory)
        self._templates_by_family = {
            str(t["family"]): t for t in _OPPORTUNITY_TEMPLATES
        }

    # ----- persistence -----

    def _state_path(self) -> Path:
        return self._root / STATE_FILE

    def _load_state(self) -> dict[str, Any]:
        path = self._state_path()
        if not path.exists():
            return self._default_state()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return self._default_state()
        if not isinstance(data, dict):
            return self._default_state()
        base = self._default_state()
        base.update(data)
        return base

    def _save_state(self, state: dict[str, Any]) -> None:
        path = self._state_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(state, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _default_state(self) -> dict[str, Any]:
        return {
            "version": "1.0",
            "module": "income_engine",
            "owner_only": True,
            "commercial_product": False,
            "balance_eur": 0.0,
            "auto_approve_limit_eur": 0.0,
            "reinvest_enabled": False,
            "realized_profit_eur": 0.0,
            "open_risk_eur": 0.0,
            "mission": None,
            "updated_at": _utc_now(),
        }

    def _append_jsonl(self, filename: str, row: dict[str, Any]) -> None:
        path = self._root / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    def _load_learning(self) -> dict[str, Any]:
        path = self._root / LEARNING_FILE
        if not path.exists():
            return {
                "platforms": {},
                "missions_total": 0,
                "approvals": 0,
                "rejects": 0,
                "empty_missions": 0,
                "success_rate": None,
            }
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except (OSError, json.JSONDecodeError):
            return {}

    def _save_learning(self, data: dict[str, Any]) -> None:
        path = self._root / LEARNING_FILE
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    # ----- capital -----

    def capital_limits(self, balance_eur: float) -> dict[str, Any]:
        bal = max(0.0, balance_eur)
        laws = self._lab.capital_laws(bal)
        return {
            "balance_eur": round(bal, 2),
            "max_mission_pool_eur": round(bal * MAX_MISSION_PCT, 2),
            "max_parallel_risk_eur": round(bal * MAX_PARALLEL_RISK_PCT, 2),
            "reserve_eur": round(bal * (1.0 - MAX_PARALLEL_RISK_PCT), 2),
            "max_experiment_eur": laws["max_experiment_eur"],
            "max_experiment_pct": MAX_EXPERIMENT_PCT,
            "suggested_micro_test_eur": laws["suggested_micro_test_eur"],
            "max_concurrent_experiments": MAX_CONCURRENT_EXPERIMENTS,
            "bank_pitch_ru": BANK_PITCH_RU,
            "search_spend_allowed": False,
        }

    # ----- panel / status -----

    def panel(self) -> dict[str, Any]:
        with self._lock:
            state = self._load_state()
            mission = state.get("mission")
            if isinstance(mission, dict) and mission.get("status") == "running":
                mission = self._tick_mission(state, mission)
                state["mission"] = mission
                self._save_state(state)
            learning = self._load_learning()
            bal = _safe_float(state.get("balance_eur"))
            if bal <= 0:
                bal = _safe_float(self._lab._load_lab().get("bank_eur"), 20.0)
            alpha = self._lab.panel(bank_eur=bal)
            return {
                "ok": True,
                "module": "income_engine",
                "product_name": "Virtus Core Alpha Hunter",
                "section": "Income Lab",
                "owner_only": True,
                "commercial_product": False,
                "law_ru": OWNER_LAW_RU,
                "search_law_ru": SEARCH_SPEND_FORBIDDEN_RU,
                "bank_pitch_ru": BANK_PITCH_RU,
                "empty_result_ru": EMPTY_RESULT_RU,
                "pitch_template_ru": PITCH_TEMPLATE_RU,
                "alpha_hunter": alpha,
                "swarm": {
                    "size": len(self._swarm),
                    "families": sorted({r["family"] for r in self._swarm}),
                    "hunter_catalog": alpha.get("hunters"),
                },
                "capital": self.capital_limits(bal),
                "auto_approve_limit_eur": _safe_float(
                    state.get("auto_approve_limit_eur")
                ),
                "reinvest_enabled": bool(state.get("reinvest_enabled")),
                "realized_profit_eur": _safe_float(state.get("realized_profit_eur")),
                "open_risk_eur": _safe_float(state.get("open_risk_eur")),
                "mission": mission,
                "learning": {
                    "missions_total": int(learning.get("missions_total") or 0),
                    "approvals": int(learning.get("approvals") or 0),
                    "rejects": int(learning.get("rejects") or 0),
                    "empty_missions": int(learning.get("empty_missions") or 0),
                    "success_rate": learning.get("success_rate"),
                    "platforms_tracked": len(
                        learning.get("platforms")
                        if isinstance(learning.get("platforms"), dict)
                        else {}
                    ),
                },
                "approval_modes_ru": [
                    "Одобрить один раз — только этот микро-эксперимент",
                    "Одобрить все сделки до €X — без повторного вопроса",
                    "Всё выше лимита / 2% банка — только после подтверждения",
                ],
                "safety_ru": [
                    "Не тратить деньги на поиск",
                    "Не выдумывать прибыль",
                    "Не фейкать ROI",
                    "Только whitelist площадок",
                    "Не спамить / не фейковые аккаунты",
                    "Не обходить платёжные системы",
                    "Не гарантировать прибыль",
                    "Toloka Requester ≠ инвестиционный банк",
                ],
            }

    def status(self) -> dict[str, Any]:
        return self.panel()

    def set_stage(self, stage: str) -> dict[str, Any]:
        return self._lab.set_stage(stage)

    def paper_day(
        self,
        *,
        balance_eur: float = 20.0,
        opportunities_target: int = 100,
    ) -> dict[str, Any]:
        """Stage 1 — hunt + model, spend €0."""
        with self._lock:
            state = self._load_state()
            state["balance_eur"] = max(0.0, _safe_float(balance_eur))
            self._save_state(state)
            self._lab.set_bank(state["balance_eur"])
            out = self._lab.run_paper_day(
                bank_eur=state["balance_eur"],
                opportunities_target=opportunities_target,
                hunter_sample=min(200, max(100, opportunities_target)),
            )
            return out

    def propose_top(self, *, balance_eur: float | None = None, n: int = 3) -> dict[str, Any]:
        """Stage 2 — show top strategies + micro-test quote."""
        with self._lock:
            if balance_eur is not None:
                state = self._load_state()
                state["balance_eur"] = max(0.0, _safe_float(balance_eur))
                self._save_state(state)
            return self._lab.propose_top(bank_eur=balance_eur, n=n)

    def approve_micro_test(
        self, strategy_id: str, *, balance_eur: float | None = None
    ) -> dict[str, Any]:
        """Owner Approve on a Stage-2 strategy → micro-test ≤2% (search still €0)."""
        with self._lock:
            if balance_eur is not None:
                state = self._load_state()
                state["balance_eur"] = max(0.0, _safe_float(balance_eur))
                self._save_state(state)
                self._lab.set_bank(state["balance_eur"])
            return self._lab.approve_micro_test(
                strategy_id, bank_eur=balance_eur
            )

    def set_director_thresholds(
        self,
        *,
        min_expected_profit_eur: float | None = None,
        min_roi_pct: float | None = None,
    ) -> dict[str, Any]:
        return self._lab.set_director_thresholds(
            min_expected_profit_eur=min_expected_profit_eur,
            min_roi_pct=min_roi_pct,
        )

    def request_withdraw(
        self, *, amount_eur: float | None = None, confirm: bool = True
    ) -> dict[str, Any]:
        return self._lab.request_withdraw(amount_eur=amount_eur, confirm=confirm)

    def set_scan_interval(self, interval_sec: int) -> dict[str, Any]:
        return self._lab.set_scan_interval(interval_sec)

    def go_live(self) -> dict[str, Any]:
        return self._lab.go_live()

    # ----- mission -----

    def start_mission(
        self,
        *,
        balance_eur: float,
        auto_approve_limit_eur: float | None = None,
        duration_sec: int = MISSION_DURATION_SEC,
        simulate_fast: bool = True,
    ) -> dict[str, Any]:
        """Start a swarm mission. Owner presses START INCOME ENGINE."""
        with self._lock:
            state = self._load_state()
            cur = state.get("mission")
            if isinstance(cur, dict) and cur.get("status") == "running":
                return {
                    "ok": False,
                    "error": "mission_already_running",
                    "mission": cur,
                }

            bal = max(0.0, _safe_float(balance_eur))
            state["balance_eur"] = bal
            if auto_approve_limit_eur is not None:
                state["auto_approve_limit_eur"] = max(
                    0.0, _safe_float(auto_approve_limit_eur)
                )

            caps = self.capital_limits(bal)
            open_risk = _safe_float(state.get("open_risk_eur"))
            if open_risk >= caps["max_parallel_risk_eur"] and bal > 0:
                return {
                    "ok": False,
                    "error": "parallel_risk_cap",
                    "detail_ru": (
                        "Открытый риск уже на лимите. Сначала закройте сделки "
                        "или дождитесь результата."
                    ),
                    "capital": caps,
                }

            mission_id = f"ie_{uuid.uuid4().hex[:12]}"
            started = time.time()
            # Fast path for tests / local UX; live UI can still show staged ticks.
            scan_budget_sec = 2.0 if simulate_fast else min(30.0, duration_sec * 0.1)

            agent_events: list[dict[str, Any]] = []
            candidates, rejects = self._run_swarm(
                balance_eur=bal,
                mission_pool_eur=caps["max_mission_pool_eur"],
                learning=self._load_learning(),
                events_out=agent_events,
            )

            ranked = self._rank(candidates)
            auto_limit = _safe_float(state.get("auto_approve_limit_eur"))
            for opp in ranked:
                inv = _safe_float(opp.get("investment_eur"))
                if (
                    auto_limit > 0
                    and inv > 0
                    and inv <= auto_limit
                    and opp.get("lane") == "executable_candidate"
                ):
                    opp["auto_eligible"] = True
                else:
                    opp["auto_eligible"] = False

            status = "awaiting_approval" if ranked else "failed_empty"
            result_ru = (
                PITCH_TEMPLATE_RU
                if ranked
                else f"{EMPTY_RESULT_RU}. Spent: 0 EUR. Ожидаемый ROI > 0 не найден."
            )

            mission = {
                "mission_id": mission_id,
                "status": "running",
                "started_at": _utc_now(),
                "started_ts": started,
                "duration_sec": int(duration_sec),
                "ends_ts": started + float(duration_sec),
                "scan_complete_ts": started + scan_budget_sec,
                "balance_eur": bal,
                "capital": caps,
                "swarm_size": len(self._swarm),
                "agent_events": agent_events[-40:],
                "rejected_count": len(rejects),
                "opportunities_found": len(ranked),
                "opportunities": ranked,
                "rejects_sample": rejects[:12],
                "spent_eur": 0.0,
                "estimated_return_eur": round(
                    sum(_safe_float(o.get("expected_return_eur")) for o in ranked), 2
                ),
                "result_ru": result_ru,
                "final_status": status,
                "live": {
                    "phase": "searching",
                    "message_ru": "Searching…",
                    "time_remaining_sec": int(duration_sec),
                    "current_opportunities": len(ranked),
                },
            }
            state["mission"] = mission
            state["updated_at"] = _utc_now()
            self._save_state(state)

            # Immediate tick so first poll already advances
            mission = self._tick_mission(state, mission)
            state["mission"] = mission
            self._save_state(state)

            return {"ok": True, "mission": mission}

    def _tick_mission(
        self, state: dict[str, Any], mission: dict[str, Any]
    ) -> dict[str, Any]:
        if mission.get("status") != "running":
            return mission
        now = time.time()
        ends = _safe_float(mission.get("ends_ts"), now)
        scan_done = _safe_float(mission.get("scan_complete_ts"), now)
        remaining = max(0, int(ends - now))
        found = int(mission.get("opportunities_found") or 0)

        if now < scan_done:
            mission["live"] = {
                "phase": "searching",
                "message_ru": "Searching… рой агентов сканирует легальные возможности",
                "time_remaining_sec": remaining,
                "current_opportunities": found,
            }
            return mission

        # After scan window → finalize to approval or empty
        final = str(mission.get("final_status") or "failed_empty")
        mission["status"] = final
        mission["finished_at"] = _utc_now()
        mission["live"] = {
            "phase": "done",
            "message_ru": (
                "Mission Success — жду одобрения владельца"
                if final == "awaiting_approval"
                else "Mission Failed — подходящих сделок не найдено"
            ),
            "time_remaining_sec": 0,
            "current_opportunities": found,
        }

        learning = self._load_learning()
        learning["missions_total"] = int(learning.get("missions_total") or 0) + 1
        if final == "failed_empty":
            learning["empty_missions"] = int(learning.get("empty_missions") or 0) + 1
        self._save_learning(learning)

        self._append_jsonl(
            MISSIONS_FILE,
            {
                "at": _utc_now(),
                "mission_id": mission.get("mission_id"),
                "status": final,
                "found": found,
                "rejected": int(mission.get("rejected_count") or 0),
                "balance_eur": mission.get("balance_eur"),
                "spent_eur": 0.0,
            },
        )

        # Auto-approve under limit (once pool allows)
        if final == "awaiting_approval":
            self._maybe_auto_approve(state, mission)

        return mission

    def _run_swarm(
        self,
        *,
        balance_eur: float,
        mission_pool_eur: float,
        learning: dict[str, Any],
        events_out: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        accepted: list[dict[str, Any]] = []
        rejected: list[dict[str, Any]] = []
        seen_families: set[str] = set()

        def _work(role: dict[str, str]) -> dict[str, Any]:
            return self._agent_evaluate(
                role,
                balance_eur=balance_eur,
                mission_pool_eur=mission_pool_eur,
                learning=learning,
            )

        workers = min(DEFAULT_SWARM_WORKERS, max(4, len(self._swarm) // 8))
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futs = {pool.submit(_work, role): role for role in self._swarm}
            for fut in as_completed(futs):
                role = futs[fut]
                try:
                    result = fut.result()
                except Exception as exc:  # noqa: BLE001 — agent isolation
                    result = {
                        "agent_id": role["id"],
                        "decision": "reject",
                        "reason_ru": f"agent_error: {exc}",
                    }
                events_out.append(
                    {
                        "agent_id": result.get("agent_id"),
                        "title": role.get("title"),
                        "decision": result.get("decision"),
                        "at": _utc_now(),
                    }
                )
                if result.get("decision") == "accept" and result.get("opportunity"):
                    opp = result["opportunity"]
                    fam = str(opp.get("family") or "")
                    # One best candidate per family after merge
                    if fam and fam in seen_families:
                        rejected.append(
                            {
                                "agent_id": role["id"],
                                "reason_ru": "duplicate_family_merge",
                                "family": fam,
                            }
                        )
                        continue
                    if fam:
                        seen_families.add(fam)
                    accepted.append(opp)
                else:
                    rejected.append(
                        {
                            "agent_id": role["id"],
                            "reason_ru": result.get("reason_ru")
                            or "expected_roi_not_positive",
                            "family": role.get("family"),
                        }
                    )
        return accepted, rejected

    def _agent_evaluate(
        self,
        role: dict[str, str],
        *,
        balance_eur: float,
        mission_pool_eur: float,
        learning: dict[str, Any],
    ) -> dict[str, Any]:
        family = role["family"]
        tmpl = self._templates_by_family.get(family)
        if not tmpl:
            # Specialist without a concrete template → research reject (honest)
            return {
                "agent_id": role["id"],
                "decision": "reject",
                "reason_ru": "Нет подтверждённого шаблона с положительным ожидаемым ROI",
            }

        if not tmpl.get("legal_ok"):
            return {
                "agent_id": role["id"],
                "decision": "reject",
                "reason_ru": "legal_block",
            }

        inv = _safe_float(tmpl.get("investment_eur"))
        ret = _safe_float(tmpl.get("expected_return_eur"))
        prob = _safe_float(tmpl.get("probability"))
        conf = _safe_float(tmpl.get("confidence"))
        evidence = str(tmpl.get("evidence") or "none")

        # Venture law: cap spend templates at ≤2% of bank (scale return pro-rata)
        exp_cap = experiment_cap_eur(balance_eur)
        if inv > 0 and exp_cap > 0 and inv > exp_cap:
            scale = exp_cap / inv
            inv = round(exp_cap, 4)
            ret = round(ret * scale, 4)
        elif inv > 0 and exp_cap <= 0:
            return {
                "agent_id": role["id"],
                "decision": "reject",
                "reason_ru": "bank_too_small_for_experiment",
            }

        # Learning adjusts probability/confidence from history (never invents €)
        plat = (learning.get("platforms") or {}).get(family) or {}
        if isinstance(plat, dict) and plat.get("trials"):
            trials = max(1, int(plat.get("trials") or 1))
            wins = int(plat.get("wins") or 0)
            hist_p = wins / trials
            # Blend cautiously toward history
            prob = _clamp(0.7 * prob + 0.3 * hist_p, 0.05, 0.95)
            conf = _clamp(conf + min(0.15, trials * 0.02), 0.0, 0.95)
            if plat.get("avg_realized_roi") is not None:
                evidence = "historical"

        if evidence == "none" or (ret <= 0 and evidence != "historical"):
            return {
                "agent_id": role["id"],
                "decision": "reject",
                "reason_ru": "Недостаточно данных — система не выдумывает прибыль",
            }

        if conf < MIN_CONFIDENCE:
            return {
                "agent_id": role["id"],
                "decision": "reject",
                "reason_ru": f"confidence_too_low ({conf:.2f} < {MIN_CONFIDENCE})",
            }

        if inv > mission_pool_eur + 1e-9:
            return {
                "agent_id": role["id"],
                "decision": "reject",
                "reason_ru": (
                    f"investment {inv}€ > mission pool {mission_pool_eur}€ "
                    "(reserve capital)"
                ),
            }

        if inv > balance_eur + 1e-9:
            return {
                "agent_id": role["id"],
                "decision": "reject",
                "reason_ru": "insufficient_balance",
            }

        ev = expected_value_eur(
            investment_eur=inv, expected_return_eur=ret, probability=prob
        )
        if ev <= 0:
            return {
                "agent_id": role["id"],
                "decision": "reject",
                "reason_ru": f"expected_roi_not_positive (EV={ev}€)",
            }

        roi = expected_roi_ratio(
            investment_eur=inv, expected_return_eur=ret, probability=prob
        )
        lane = (
            "executable_candidate"
            if evidence == "historical"
            else "research_prepare"
        )

        opp = {
            "id": f"opp_{family}_{uuid.uuid4().hex[:8]}",
            "family": family,
            "agent_id": role["id"],
            "title": tmpl.get("title"),
            "title_ru": tmpl.get("title_ru"),
            "investment_eur": inv,
            "expected_return_eur": ret,
            "expected_value_eur": ev,
            "expected_roi": None if roi is None or math.isinf(roi) else roi,
            "probability": round(prob, 4),
            "confidence": round(conf, 4),
            "risk": tmpl.get("risk"),
            "execution_days": int(tmpl.get("execution_days") or 1),
            "reason_ru": tmpl.get("reason_ru"),
            "actions": list(tmpl.get("actions") or ()),
            "evidence": evidence,
            "lane": lane,
            "legal_ok": True,
            "owner_pitch_ru": PITCH_TEMPLATE_RU,
            "disclaimer_ru": (
                "Это оценка ожидаемого ROI, не гарантия прибыли. "
                "Исполнение только легальных действий после одобрения."
            ),
            "status": "proposed",
        }
        return {
            "agent_id": role["id"],
            "decision": "accept",
            "opportunity": opp,
        }

    def _rank(self, opps: list[dict[str, Any]]) -> list[dict[str, Any]]:
        def key(o: dict[str, Any]) -> tuple:
            roi = o.get("expected_roi")
            roi_v = _safe_float(roi, 0.0) if roi is not None else 999.0
            return (
                -_safe_float(o.get("expected_value_eur")),
                -_safe_float(o.get("confidence")),
                int(o.get("execution_days") or 99),
                _safe_float(o.get("investment_eur")),
                -roi_v,
            )

        return sorted(opps, key=key)

    # ----- approval -----

    def set_auto_approve_limit(self, limit_eur: float) -> dict[str, Any]:
        with self._lock:
            state = self._load_state()
            state["auto_approve_limit_eur"] = max(0.0, _safe_float(limit_eur))
            state["updated_at"] = _utc_now()
            self._save_state(state)
            return {
                "ok": True,
                "auto_approve_limit_eur": state["auto_approve_limit_eur"],
            }

    def set_reinvest(self, enabled: bool) -> dict[str, Any]:
        with self._lock:
            state = self._load_state()
            state["reinvest_enabled"] = bool(enabled)
            state["updated_at"] = _utc_now()
            self._save_state(state)
            return {"ok": True, "reinvest_enabled": state["reinvest_enabled"]}

    def approve(
        self,
        opportunity_id: str,
        *,
        mode: str = "once",
        note: str = "",
    ) -> dict[str, Any]:
        """Approve once | batch uses auto_approve_limit for siblings."""
        with self._lock:
            state = self._load_state()
            lab = self._lab._load_lab()
            stage = str(lab.get("stage") or STAGE_PAPER)
            if stage == STAGE_PAPER:
                return {
                    "ok": False,
                    "error": "stage_paper",
                    "detail_ru": (
                        "Stage 1 (paper): траты запрещены. "
                        "Сначала «Paper day» → «Propose top» → Stage 2/3 → Approve."
                    ),
                }
            mission = state.get("mission")
            if not isinstance(mission, dict):
                return {"ok": False, "error": "no_mission"}
            opps = list(mission.get("opportunities") or [])
            target = next(
                (o for o in opps if o.get("id") == opportunity_id), None
            )
            if not target:
                return {"ok": False, "error": "opportunity_not_found"}

            bal = _safe_float(state.get("balance_eur"))
            gate = self._lab.assert_experiment_allowed(
                bank_eur=bal,
                cost_eur=_safe_float(target.get("investment_eur")),
                active=int(lab.get("active_experiments") or 0),
            )
            if not gate.get("ok") and stage == STAGE_MICRO:
                return gate
            # Stage propose: allow prepare_dry_run even if micro gate strict on live
            if stage == STAGE_PROPOSE and not gate.get("ok"):
                if gate.get("error") == "over_2pct":
                    return gate

            limit = _safe_float(state.get("auto_approve_limit_eur"))
            to_run: list[dict[str, Any]] = []
            if mode == "batch_limit":
                for o in opps:
                    if o.get("status") not in (None, "proposed", "auto_eligible"):
                        if o.get("status") in ("approved", "prepared", "executed"):
                            continue
                    inv = _safe_float(o.get("investment_eur"))
                    if inv <= limit + 1e-9:
                        to_run.append(o)
                    elif o.get("id") == opportunity_id:
                        return {
                            "ok": False,
                            "error": "above_auto_limit",
                            "detail_ru": (
                                f"Сделка {inv}€ выше лимита {limit}€ — "
                                "нужно отдельное подтверждение (once)."
                            ),
                        }
            else:
                inv = _safe_float(target.get("investment_eur"))
                if limit > 0 and inv > limit + 1e-9 and mode != "once":
                    return {
                        "ok": False,
                        "error": "above_auto_limit",
                        "detail_ru": (
                            f"Всё выше €{limit} — только после явного подтверждения."
                        ),
                    }
                to_run = [target]

            results = []
            for o in to_run:
                results.append(self._execute_approved(state, mission, o, note=note))

            mission["opportunities"] = opps
            state["mission"] = mission
            state["updated_at"] = _utc_now()
            self._save_state(state)

            learning = self._load_learning()
            learning["approvals"] = int(learning.get("approvals") or 0) + len(results)
            self._save_learning(learning)

            return {
                "ok": True,
                "mode": mode,
                "executed": results,
                "mission": mission,
                "message_ru": (
                    "Одобрено. Система подготовила/выполнила только легальные действия. "
                    "Прибыль не гарантируется — ждём реальный результат источника."
                ),
            }

    def reject(self, opportunity_id: str, *, note: str = "") -> dict[str, Any]:
        with self._lock:
            state = self._load_state()
            mission = state.get("mission")
            if not isinstance(mission, dict):
                return {"ok": False, "error": "no_mission"}
            opps = list(mission.get("opportunities") or [])
            target = next(
                (o for o in opps if o.get("id") == opportunity_id), None
            )
            if not target:
                return {"ok": False, "error": "opportunity_not_found"}
            target["status"] = "rejected"
            target["reject_note"] = note
            mission["opportunities"] = opps
            state["mission"] = mission
            self._save_state(state)
            learning = self._load_learning()
            learning["rejects"] = int(learning.get("rejects") or 0) + 1
            self._save_learning(learning)
            return {"ok": True, "opportunity": target}

    def _maybe_auto_approve(
        self, state: dict[str, Any], mission: dict[str, Any]
    ) -> None:
        limit = _safe_float(state.get("auto_approve_limit_eur"))
        if limit <= 0:
            return
        for o in list(mission.get("opportunities") or []):
            if o.get("status") not in (None, "proposed"):
                continue
            inv = _safe_float(o.get("investment_eur"))
            if 0 < inv <= limit and o.get("auto_eligible"):
                self._execute_approved(
                    state, mission, o, note="auto_approve_limit"
                )

    def _execute_approved(
        self,
        state: dict[str, Any],
        mission: dict[str, Any],
        opp: dict[str, Any],
        *,
        note: str = "",
    ) -> dict[str, Any]:
        """Prepare legal actions. Live purchase only if env allows + owner approved.

        Default: dry_run prepare — never fabricate profit entries.
        """
        import os

        inv = _safe_float(opp.get("investment_eur"))
        caps = self.capital_limits(_safe_float(state.get("balance_eur")))
        open_risk = _safe_float(state.get("open_risk_eur"))
        if open_risk + inv > caps["max_parallel_risk_eur"] + 1e-9:
            opp["status"] = "blocked_risk_cap"
            return {
                "ok": False,
                "error": "parallel_risk_cap",
                "opportunity_id": opp.get("id"),
            }

        live = os.environ.get("GENESIS_INCOME_ENGINE_LIVE", "").strip() in (
            "1",
            "true",
            "yes",
        )
        stage = str(self._lab._load_lab().get("stage") or STAGE_PAPER)
        # Live micro-spend only in Stage 3 + env flag; search never spends
        allow_live = live and stage == STAGE_MICRO and inv > 0
        actions = list(opp.get("actions") or [])
        if not allow_live:
            actions = [a for a in actions if a != "purchase"]

        cap = experiment_cap_eur(_safe_float(state.get("balance_eur")))
        if inv > cap + 1e-9:
            opp["status"] = "blocked_2pct_cap"
            return {
                "ok": False,
                "error": "over_2pct",
                "opportunity_id": opp.get("id"),
                "max_experiment_eur": cap,
            }

        prepared = {
            "at": _utc_now(),
            "mission_id": mission.get("mission_id"),
            "opportunity_id": opp.get("id"),
            "actions": actions,
            "mode": "live" if allow_live else "prepare_dry_run",
            "stage": stage,
            "investment_eur": inv,
            "expected_return_eur": opp.get("expected_return_eur"),
            "expected_value_eur": opp.get("expected_value_eur"),
            "note": note,
            "profit_recorded_eur": 0.0,  # never invent
            "search_spend_eur": 0.0,
            "law_ru": (
                "Поиск = €0. Прибыль только после подтверждённой выплаты источника. "
                "Эксперимент ≤2% банка."
            ),
        }
        self._append_jsonl(EXEC_LOG_FILE, prepared)

        opp["status"] = "prepared" if prepared["mode"] == "prepare_dry_run" else "executed"
        opp["execution"] = prepared
        self._lab.bump_active(1)

        if inv > 0 and prepared["mode"] == "prepare_dry_run":
            # Reserve risk for tracking; do not deduct fake spend as profit
            state["open_risk_eur"] = round(open_risk + inv, 2)
            mission["spent_eur"] = round(
                _safe_float(mission.get("spent_eur")) + 0.0, 2
            )
        elif inv > 0 and allow_live:
            state["balance_eur"] = round(
                max(0.0, _safe_float(state.get("balance_eur")) - inv), 2
            )
            state["open_risk_eur"] = round(open_risk + inv, 2)
            mission["spent_eur"] = round(
                _safe_float(mission.get("spent_eur")) + inv, 2
            )
            self._lab.set_bank(state["balance_eur"])

        # Learning: mark trial (outcome unknown until real payout)
        learning = self._load_learning()
        platforms = learning.setdefault("platforms", {})
        fam = str(opp.get("family") or "unknown")
        row = platforms.setdefault(
            fam, {"trials": 0, "wins": 0, "losses": 0, "avg_realized_roi": None}
        )
        row["trials"] = int(row.get("trials") or 0) + 1
        platforms[fam] = row
        learning["platforms"] = platforms
        self._save_learning(learning)

        return {"ok": True, "opportunity_id": opp.get("id"), "execution": prepared}

    def record_realized_outcome(
        self,
        opportunity_id: str,
        *,
        profit_eur: float,
        success: bool,
    ) -> dict[str, Any]:
        """Owner/system records *real* payout only — never estimates."""
        with self._lock:
            state = self._load_state()
            mission = state.get("mission") or {}
            opps = list((mission or {}).get("opportunities") or [])
            opp = next((o for o in opps if o.get("id") == opportunity_id), None)
            if not opp:
                return {"ok": False, "error": "opportunity_not_found"}

            profit = _safe_float(profit_eur)
            inv = _safe_float(opp.get("investment_eur"))
            # Release risk
            state["open_risk_eur"] = max(
                0.0, _safe_float(state.get("open_risk_eur")) - inv
            )
            if success and profit > 0:
                state["realized_profit_eur"] = round(
                    _safe_float(state.get("realized_profit_eur")) + profit, 2
                )
                if state.get("reinvest_enabled"):
                    # Reinvest only realized profit
                    state["balance_eur"] = round(
                        _safe_float(state.get("balance_eur")) + profit, 2
                    )
                opp["status"] = "realized_profit"
            else:
                opp["status"] = "realized_loss_or_zero"
            opp["realized_profit_eur"] = profit if success else 0.0

            learning = self._load_learning()
            platforms = learning.setdefault("platforms", {})
            fam = str(opp.get("family") or "unknown")
            row = platforms.setdefault(
                fam, {"trials": 0, "wins": 0, "losses": 0, "avg_realized_roi": None}
            )
            if success and profit > 0:
                row["wins"] = int(row.get("wins") or 0) + 1
            else:
                row["losses"] = int(row.get("losses") or 0) + 1
            trials = max(1, int(row.get("trials") or 1))
            # Running average of realized ROI on investment
            prev = row.get("avg_realized_roi")
            sample = (profit - inv) / inv if inv > 0 else profit
            if prev is None:
                row["avg_realized_roi"] = round(sample, 4)
            else:
                row["avg_realized_roi"] = round(
                    (float(prev) * (trials - 1) + sample) / trials, 4
                )
            platforms[fam] = row
            wins = sum(
                int(p.get("wins") or 0)
                for p in platforms.values()
                if isinstance(p, dict)
            )
            total_t = sum(
                int(p.get("trials") or 0)
                for p in platforms.values()
                if isinstance(p, dict)
            )
            learning["success_rate"] = (
                round(wins / total_t, 4) if total_t else None
            )
            learning["platforms"] = platforms
            self._save_learning(learning)

            if isinstance(mission, dict):
                mission["opportunities"] = opps
                state["mission"] = mission
            state["updated_at"] = _utc_now()
            self._save_state(state)
            return {"ok": True, "opportunity": opp, "state": self.panel()}
