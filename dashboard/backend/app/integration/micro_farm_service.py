"""Micro-Farm — distributed micro-agent swarm (Virtus Core orchestrator).

Each combiner runs a primitive task; earnings aggregate to one ledger.
External micro-task platforms connect via TaskAdapter stubs (API keys required).
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.integration.business_mode_service import BusinessModeService
from app.integration.engine_ai_service import EngineAIService
from app.integration.finance_service import FinanceService
from app.integration.opportunity_service import OpportunityService
from app.integration.swarm_bridge import build_swarm_orchestrator
from app.integration.stealth_http import stealth_fetch_get

_DEFAULT_MEMORY = Path(__file__).resolve().parent.parent / "memory"
_farm_logger = logging.getLogger("genesis.farm")

_DASHBOARD_SECTION_CACHE: dict[str, tuple[float, Any]] = {}
_DASHBOARD_SECTION_TTL_SEC = 45.0

# Pay per completed micro-task (internal queue — real platforms override via adapters).
_ADAPTER_PAY_EUR: dict[str, float] = {
    "ai_labeling": 0.05,
    "data_clean": 0.02,
    "text_classify": 0.03,
    "record_verify": 0.01,
}

_PLATFORM_ADAPTERS: list[dict[str, Any]] = []  # filled from swarm.platform_registry in dashboard()

_DEFAULT_STATE: dict[str, Any] = {
    "running": False,
    "workers_target": 10,
    "workers_active": 0,
    "last_tick_at": None,
    "total_tasks_done": 0,
    "total_earned_eur": 0.0,
    "today_earned_eur": 0.0,
    "today_date": None,
    "llm_cost_eur": 0.0,
    "active_adapter": "ai_labeling",
    "scale_ai_last": None,
    "disabled_adapters": [],
    "disabled_nodes": [],
    "last_self_healing": None,
    "dry_run_streak": 0,
    "dry_run_total_potential_eur": 0.0,
    "dry_run_milestone_reached": False,
}


class MicroFarmService:
    """Orchestrates lightweight micro-workers — one primitive task per combiner."""

    def __init__(
        self,
        opportunity: OpportunityService,
        finance: FinanceService,
        *,
        business_mode: BusinessModeService | None = None,
        memory_dir: Path | None = None,
    ) -> None:
        self._opportunity = opportunity
        self._finance = finance
        self._business_mode = business_mode or BusinessModeService(memory_dir)
        self._memory = memory_dir or _DEFAULT_MEMORY
        self._ai = EngineAIService(self._memory)

    def _state_path(self) -> Path:
        return self._memory / "micro_farm_state.json"

    def _events_path(self) -> Path:
        return self._memory / "micro_farm_events.jsonl"

    def _load_state(self) -> dict[str, Any]:
        path = self._state_path()
        if not path.is_file():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(_DEFAULT_STATE, ensure_ascii=False, indent=2), encoding="utf-8")
            return dict(_DEFAULT_STATE)
        try:
            merged = dict(_DEFAULT_STATE)
            merged.update(json.loads(path.read_text(encoding="utf-8")))
            return merged
        except (json.JSONDecodeError, OSError):
            return dict(_DEFAULT_STATE)

    def _save_state(self, data: dict[str, Any]) -> dict[str, Any]:
        path = self._state_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return data

    def _log_event(self, event: dict[str, Any]) -> None:
        path = self._events_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, ensure_ascii=False) + "\n")

    def _log_lifecycle_event(
        self,
        *,
        stage: str,
        adapter: str,
        task_id: str,
        pay_eur: float = 0.0,
        ok: bool = True,
        balance_after_eur: float | None = None,
        platform: str | None = None,
    ) -> None:
        from app.integration.swarm_bridge import ensure_swarm_importable

        ensure_swarm_importable()
        from swarm.farm_lifecycle_ru import detail_for_stage, stage_title

        sandbox = self._business_mode.is_sandbox()
        vault = self._priority_manager().vault
        plat = platform or (
            "Toloka/Scale (live)" if vault.is_live() and not vault.is_dry_run() else "учебная ферма"
        )
        title_ru = stage_title(stage)
        detail = detail_for_stage(
            stage,
            task_label=str(task_id)[:48],
            pay_eur=pay_eur,
            platform=plat,
            sandbox=sandbox,
            balance_eur=balance_after_eur,
        )
        from swarm.farm_lifecycle_ru import (
            STAGE_BALANCE_INCREASED,
            STAGE_PAYMENT_CONFIRMED,
        )

        show_pay = stage in {STAGE_PAYMENT_CONFIRMED, STAGE_BALANCE_INCREASED}
        self._log_event(
            {
                "id": uuid.uuid4().hex[:12],
                "at": datetime.now(timezone.utc).isoformat(),
                "adapter": adapter,
                "pay_eur": pay_eur if show_pay else 0.0,
                "target": task_id,
                "detail": detail,
                "title_ru": title_ru,
                "lifecycle_stage": stage,
                "ok": ok,
            }
        )

    def _emit_task_lifecycle(
        self,
        *,
        adapter: str,
        task_id: str,
        pay_eur: float,
        ok: bool,
        balance_after_eur: float | None = None,
    ) -> None:
        from app.integration.swarm_bridge import ensure_swarm_importable

        ensure_swarm_importable()
        from swarm.farm_lifecycle_ru import STAGE_ACCEPTED, lifecycle_chain

        vault = self._priority_manager().vault
        live_ex = vault.is_live() and not vault.is_dry_run()
        self._log_lifecycle_event(
            stage=STAGE_ACCEPTED,
            adapter=adapter,
            task_id=task_id,
            pay_eur=0.0,
            ok=ok,
        )
        for stage in lifecycle_chain(
            ok=ok,
            sandbox=self._business_mode.is_sandbox(),
            live_exchange=live_ex,
            pay_eur=pay_eur,
        ):
            if stage == STAGE_ACCEPTED:
                continue
            self._log_lifecycle_event(
                stage=stage,
                adapter=adapter,
                task_id=task_id,
                pay_eur=pay_eur,
                ok=ok,
            )

    def _recent_events(self, limit: int = 20) -> list[dict[str, Any]]:
        path = self._events_path()
        if not path.is_file():
            return []
        lines = path.read_text(encoding="utf-8").strip().splitlines()
        out: list[dict[str, Any]] = []
        for line in lines[-limit:]:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return list(reversed(out))

    def _reset_today_if_needed(self, state: dict[str, Any]) -> None:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if state.get("today_date") != today:
            state["today_date"] = today
            state["today_earned_eur"] = 0.0

    def _scale_probe_ok(self, scale: dict[str, Any]) -> bool:
        """No Scale key is OK when farm runs Toloka-only."""
        if scale.get("connected"):
            return True
        if scale.get("status") == "no_key" or not scale.get("configured"):
            return True
        return False

    def _refresh_live_test_if_stale(self, state: dict[str, Any]) -> None:
        """Heal stale Live test UI — only via explicit CEO action, never on dashboard GET."""
        return

    def _cached_section(self, key: str, factory) -> Any:
        now = time.monotonic()
        hit = _DASHBOARD_SECTION_CACHE.get(key)
        if hit and now - hit[0] < _DASHBOARD_SECTION_TTL_SEC:
            return hit[1]
        value = factory()
        _DASHBOARD_SECTION_CACHE[key] = (now, value)
        return value

    def dashboard_lite(self, owner_name: str = "Владелец") -> dict[str, Any]:
        """Fast journal payload — no Toloka live probe, no heavy discovery scan."""
        from app.env_loader import load_local_env

        load_local_env()
        state = self._load_state()
        self._reset_today_if_needed(state)
        sandbox = self._business_mode.is_sandbox()
        net = round(
            float(state.get("today_earned_eur") or 0) - float(state.get("llm_cost_eur") or 0),
            4,
        )
        return {
            "mode": "micro_farm",
            "owner_name": owner_name,
            "running": bool(state.get("running")),
            "workers_active": int(state.get("workers_active") or 0),
            "today_earned_eur": float(state.get("today_earned_eur") or 0),
            "total_earned_eur": float(state.get("total_earned_eur") or 0),
            "total_tasks_done": int(state.get("total_tasks_done") or 0),
            "llm_cost_eur": float(state.get("llm_cost_eur") or 0),
            "net_profit_eur": max(0.0, net),
            "balance_label": (
                "Накоплено (учебный режим — не банк)"
                if sandbox
                else "Накоплено на счёте"
            ),
            "sandbox": sandbox,
            "dry_run": self.dry_run_status(),
            "global_spider": self.global_spider_vector(),
            "last_live_connection_test": state.get("last_live_connection_test"),
            "payout_guide": self._payout_guide(),
            "payment_monitor": {"monitor": None, "payout": None, "note": "lite"},
            "recent_tasks": self._recent_events(15),
            "last_tick_at": state.get("last_tick_at"),
        }

    def _refresh_live_test_legacy(self, state: dict[str, Any]) -> None:
        """CEO-only live Toloka probe — can take 30–90s; never call from dashboard GET."""
        if self._is_dry_run():
            return
        last = state.get("last_live_connection_test") or {}
        if last.get("ok"):
            return
        from app.integration.swarm_bridge import ensure_swarm_importable

        ensure_swarm_importable()
        from swarm.live_connection import test_connection_live

        result = test_connection_live(vault=self._priority_manager().vault)
        state["last_live_connection_test"] = {
            "at": datetime.now(timezone.utc).isoformat(),
            "ok": result.get("ok"),
            "log_line": result.get("log_line"),
            "message": result.get("message"),
        }

    def _check_scale_adapter(self) -> dict[str, Any]:
        from app.integration.swarm_bridge import ensure_swarm_importable

        ensure_swarm_importable()
        from swarm.adapter_scale_ai import check_scale_ai_connection

        key = self._priority_manager().vault.secret("SCALE_API_KEY")
        return check_scale_ai_connection(api_key=key or None)

    def payment_monitor_status(self) -> dict[str, Any]:
        from app.integration.swarm_bridge import ensure_swarm_importable

        ensure_swarm_importable()
        from swarm.payment_monitor import PaymentMonitor
        from swarm.payout_notifier import PayoutNotifier

        pm = self._priority_manager()
        monitor = PaymentMonitor(pm.vault)
        scan = monitor.scan_all()
        notifier = PayoutNotifier(self._memory)
        payout = notifier.snapshot(scan)
        return {"monitor": scan, "payout": payout}

    def _payment_monitor_for_dashboard(self) -> dict[str, Any]:
        vault = self.platform_vault_status()
        exchange_keys = any(
            p.get("configured")
            for p in vault.get("platforms", [])
            if p.get("env_var") in {"SCALE_API_KEY", "TOLOKA_API_TOKEN"}
        )
        if self._is_dry_run() and not exchange_keys:
            return {"monitor": None, "payout": None, "note": "Включи FARM_LIVE_MODE=live"}
        status = self.payment_monitor_status()
        if self._is_dry_run():
            status["note"] = "Ключи бирж видны · полный LIVE после FARM_LIVE_MODE=live"
        remote_missing = vault.get("missing_for_remote") or []
        if remote_missing:
            status["remote_warning"] = (
                "FARM_EXECUTION_MODE=remote без VPS — биржа подключена, "
                "удалённые комбайны ждут FARM_WORKER_POOL_URL"
            )
        return status

    def run_test_connection_live(self) -> dict[str, Any]:
        from app.env_loader import load_local_env

        load_local_env()
        from app.integration.swarm_bridge import ensure_swarm_importable

        ensure_swarm_importable()
        from swarm.live_connection import test_connection_live

        result = test_connection_live(vault=self._priority_manager().vault)
        state = self._load_state()
        state["last_live_connection_test"] = {
            "at": datetime.now(timezone.utc).isoformat(),
            "ok": result.get("ok"),
            "log_line": result.get("log_line"),
            "message": result.get("message"),
        }
        self._save_state(state)
        if result.get("ok"):
            payout = self.payment_monitor_status().get("payout") or {}
            if payout.get("has_withdraw_ready"):
                self._log_event(
                    {
                        "id": uuid.uuid4().hex[:12],
                        "at": datetime.now(timezone.utc).isoformat(),
                        "adapter": "payout_notifier",
                        "pay_eur": 0.0,
                        "target": "exchange",
                        "detail": payout["pending_alerts"][0].get("message"),
                        "ok": True,
                    }
                )
        return result

    def _priority_manager(self) -> Any:
        from app.integration.swarm_bridge import ensure_swarm_importable

        ensure_swarm_importable()
        from swarm.priority_manager import PriorityManager

        return PriorityManager(self._memory)

    def platform_vault_status(self) -> dict[str, Any]:
        return self._priority_manager().vault.snapshot()

    def global_spider_vector(self) -> dict[str, Any]:
        from app.integration.global_spider_service import GlobalSpiderService

        return GlobalSpiderService(self._memory).spider_dashboard()

    def _hunting_settings(self) -> dict[str, Any]:
        from app.integration.global_spider_service import GlobalSpiderService

        cfg = GlobalSpiderService(self._memory).load_config()
        from app.integration.farm_hunting_defaults import hunting_settings

        return hunting_settings(cfg)

    def _adapter_pay_eur(self, adapter_id: str) -> float:
        return float(_ADAPTER_PAY_EUR.get(adapter_id, 0.01))

    def _passes_min_task_price(self, adapter_id: str) -> bool:
        return self._adapter_pay_eur(adapter_id) >= self._hunting_settings()["min_task_price"]

    def _log_price_filter_skip(self, adapter_id: str, *, target: str) -> None:
        pay = self._adapter_pay_eur(adapter_id)
        min_p = self._hunting_settings()["min_task_price"]
        self._log_event(
            {
                "id": uuid.uuid4().hex[:12],
                "at": datetime.now(timezone.utc).isoformat(),
                "adapter": adapter_id,
                "pay_eur": 0.0,
                "target": target[:48],
                "detail": (
                    f"[Filter] Task too cheap, skipped · {adapter_id} · "
                    f"{pay:.4f} € < min {min_p:.4f} € · {target[:32]}"
                ),
                "title_ru": "Фильтр: задача слишком дешёвая",
                "lifecycle_stage": "price_filter",
                "ok": False,
                "skipped": True,
            }
        )

    def _payout_guide(self) -> dict[str, Any]:
        from app.integration.swarm_bridge import ensure_swarm_importable

        ensure_swarm_importable()
        from swarm.farm_lifecycle_ru import payout_ui_block
        from swarm.payout_notifier import PayoutNotifier

        threshold = PayoutNotifier(self._memory).snapshot().get("threshold_usd", 10.0)
        return payout_ui_block(threshold_usd=float(threshold or 10.0))

    def prepare_live_mode(self) -> dict[str, Any]:
        vault = self.platform_vault_status()
        cloud = self._priority_manager().dispatcher.snapshot()
        return {
            "ok": True,
            "live_ready": vault.get("live_ready"),
            "farm_mode": vault.get("farm_mode"),
            "checklist": [
                {
                    "step": 1,
                    "done": any(p.get("configured") for p in vault.get("platforms", []) if p.get("env_var") == "SCALE_API_KEY"),
                    "title": "Scale API ключ в .env.local",
                },
                {
                    "step": 2,
                    "done": any(
                        p.get("configured")
                        for p in vault.get("platforms", [])
                        if p.get("env_var") in {"GENESIS_GROQ_API_KEY", "GROQ_API_KEY"}
                    ),
                    "title": "Groq ключ для разметки",
                },
                {
                    "step": 3,
                    "done": cloud.get("pool_configured") or cloud.get("execution_mode") == "local",
                    "title": "VPS worker pool (remote) или local тест",
                },
                {
                    "step": 4,
                    "done": vault.get("farm_mode") == "live",
                    "title": "FARM_LIVE_MODE=live + перезапуск Genesis.exe",
                },
            ],
            "vault": vault,
            "next": vault.get("go_live_note"),
        }

    def _apply_self_healing(self, state: dict[str, Any]) -> dict[str, Any]:
        pm = self._priority_manager()
        healing = pm.run_self_healing(
            disabled_adapters=set(state.get("disabled_adapters") or []),
            disabled_nodes=set(state.get("disabled_nodes") or []),
        )
        state["disabled_adapters"] = healing.get("disabled_adapters") or []
        state["disabled_nodes"] = healing.get("disabled_nodes") or []
        state["last_self_healing"] = healing
        for action in healing.get("actions") or []:
            self._log_event(
                {
                    "id": uuid.uuid4().hex[:12],
                    "at": datetime.now(timezone.utc).isoformat(),
                    "adapter": "self_healing",
                    "pay_eur": 0.0,
                    "target": action.get("target"),
                    "detail": action.get("reason"),
                    "ok": True,
                    "action": action.get("action"),
                }
            )
        return healing

    def _is_dry_run(self) -> bool:
        return self._priority_manager().vault.is_dry_run()

    def _record_dry_run_completion(
        self,
        state: dict[str, Any],
        *,
        adapter_id: str,
        task_id: str,
        llm_cost_eur: float = 0.0,
    ) -> dict[str, Any] | None:
        if not self._is_dry_run():
            return None
        from app.integration.swarm_bridge import ensure_swarm_importable

        ensure_swarm_importable()
        from swarm.dry_run import log_potential_profit

        state["dry_run_streak"] = int(state.get("dry_run_streak") or 0) + 1
        entry = log_potential_profit(
            adapter_id=adapter_id,
            task_id=task_id,
            llm_cost_eur=llm_cost_eur,
            streak=int(state["dry_run_streak"]),
        )
        state["dry_run_total_potential_eur"] = round(
            float(state.get("dry_run_total_potential_eur") or 0) + float(entry["potential_profit_eur"]),
            4,
        )
        if entry.get("milestone_reached"):
            state["dry_run_milestone_reached"] = True
        self._log_event(
            {
                "id": uuid.uuid4().hex[:12],
                "at": datetime.now(timezone.utc).isoformat(),
                "adapter": "dry_run",
                "pay_eur": entry["potential_profit_eur"],
                "target": task_id,
                "detail": entry["log_line"],
                "ok": True,
                "streak": entry["streak"],
            }
        )
        return entry

    def dry_run_status(self) -> dict[str, Any]:
        state = self._load_state()
        pm = self._priority_manager()
        from app.integration.swarm_bridge import ensure_swarm_importable

        ensure_swarm_importable()
        from swarm.dry_run import MILESTONE_STREAK, explain_task_selection, is_dry_run_mode

        vault = pm.vault.snapshot()
        active = is_dry_run_mode(vault.get("farm_mode", "dry_run"))
        if not active:
            return {"active": False, "farm_mode": vault.get("farm_mode"), "note": "Live mode — dry-run logs off"}

        legacy_preview = [
            (aid, str(row.get("company_name") or row.get("id") or ""))
            for aid, row in self._pick_tasks(5)
        ]
        arbitrage = pm.arbitrage_decision()
        return {
            "active": True,
            "farm_mode": "dry_run",
            "execution_mode": "local",
            "streak": int(state.get("dry_run_streak") or 0),
            "milestone_target": MILESTONE_STREAK,
            "milestone_reached": bool(state.get("dry_run_milestone_reached")),
            "total_potential_eur": float(state.get("dry_run_total_potential_eur") or 0),
            "log_format": "[DRY RUN] Potential profit: €0.15",
            "task_selection": explain_task_selection(
                labeling_workers=int(state.get("workers_target") or 10),
                legacy_tasks=legacy_preview,
                allocation=pm.allocate_workers(
                    int(state.get("workers_target") or 10),
                    tuple(_ADAPTER_PAY_EUR.keys()),
                    disabled_adapters=set(state.get("disabled_adapters") or []),
                ),
                disabled_adapters=list(state.get("disabled_adapters") or []),
                arbitrage_winner=arbitrage.get("winner"),
            ),
            "note": (
                f"Смотри консоль Genesis — после {MILESTONE_STREAK} строк dry-run "
                "понятно, окупится ли VPS (~€5)"
            ),
        }

    def _record_learning(
        self,
        *,
        adapter_id: str,
        pay_eur: float,
        llm_cost_eur: float = 0.0,
        duration_ms: float = 0.0,
        cached: bool = False,
    ) -> None:
        self._priority_manager().learning.record(
            adapter_id=adapter_id,
            pay_eur=pay_eur,
            llm_cost_eur=llm_cost_eur,
            duration_ms=duration_ms,
            cached=cached,
        )

    def revenue_forecast(self, *, labeling_nodes: int = 50, passive_nodes: int = 0) -> dict[str, Any]:
        from app.integration.swarm_bridge import ensure_swarm_importable

        ensure_swarm_importable()
        from swarm.revenue_model import full_forecast

        state = self._load_state()
        events = self._recent_events(30)
        pay_samples = [float(e.get("pay_eur") or 0) for e in events if e.get("ok") and float(e.get("pay_eur") or 0) > 0]
        measured_pay = sum(pay_samples) / len(pay_samples) if pay_samples else 0.0
        measured_tasks_h = 0.0
        if state.get("last_tick_at") and pay_samples:
            measured_tasks_h = min(len(pay_samples) * 12.0, 60.0)

        pm = self._priority_manager()
        node_count = passive_nodes or pm.nodes.configured_count() or int(state.get("workers_target") or 1)
        return full_forecast(
            labeling_nodes=labeling_nodes,
            passive_nodes=node_count if pm.nodes.configured_count() > 0 else 0,
            measured_pay_eur_per_task=measured_pay,
            measured_tasks_per_hour=measured_tasks_h,
        )

    def run_battle_test(self) -> dict[str, Any]:
        """First-node combat test — one task, real log cents, honest checklist."""
        checks: list[dict[str, Any]] = []
        pm = self._priority_manager()

        ai_status = self._ai.setup_status()
        brain_ok = bool(ai_status.get("brain_ready"))
        checks.append(
            {
                "id": "ai_brain",
                "ok": brain_ok,
                "label": "AI Brain (Groq/Gemini)",
                "detail": ai_status.get("status_label") or "Нужен ключ",
            }
        )

        cloud = pm.dispatcher.snapshot()
        pool_ok = bool(cloud.get("pool", {}).get("ok"))
        mode = cloud.get("execution_mode", "local")
        checks.append(
            {
                "id": "cloud_pool",
                "ok": mode == "local" or pool_ok,
                "label": f"Cloud Dispatcher ({mode})",
                "detail": cloud.get("pool", {}).get("message") or cloud.get("local_note", ""),
            }
        )

        scale = self._check_scale_adapter()
        checks.append(
            {
                "id": "scale_ai",
                "ok": bool(scale.get("connected")) or not scale.get("configured"),
                "label": "Scale AI",
                "detail": scale.get("log_line") or scale.get("message", ""),
            }
        )

        started = time.perf_counter()
        tick = self.run_tick(workers=1)
        elapsed_sec = round(time.perf_counter() - started, 2)
        earned = float(tick.get("earned_eur") or 0)
        tasks = int(tick.get("tasks_done") or 0)
        execution = tick.get("execution") or {}
        target = execution.get("target", "local")

        if target == "remote" and pool_ok:
            pm.nodes.register_heartbeat(node_id="battle-test-remote", region="pool", online=True)

        checks.append(
            {
                "id": "tick",
                "ok": tasks >= 0,
                "label": "Пробный tick (1 комбайн)",
                "detail": f"{tasks} задач · +{earned:.4f} € · {elapsed_sec}s · {target}",
            }
        )

        pay_per_task = earned / tasks if tasks > 0 else 0.0
        tasks_per_hour = round(tasks * (3600 / max(elapsed_sec, 1)), 2) if tasks > 0 else 0.0
        forecast = self.revenue_forecast(labeling_nodes=1, passive_nodes=pm.nodes.configured_count())
        arbitrage = pm.arbitrage_decision()

        state = self._load_state()
        state["last_battle_test"] = {
            "at": datetime.now(timezone.utc).isoformat(),
            "earned_eur": earned,
            "tasks_done": tasks,
            "execution_target": target,
            "pay_per_task_eur": round(pay_per_task, 4),
            "tasks_per_hour_est": tasks_per_hour,
            "checks_passed": sum(1 for c in checks if c.get("ok")),
            "checks_total": len(checks),
        }
        self._save_state(state)

        all_ok = all(c.get("ok") for c in checks[:3])  # scale optional if no key
        return {
            "ok": True,
            "battle_ready": tasks > 0 or brain_ok,
            "verdict": (
                f"Боевой тест: +{earned:.4f} € за {tasks} задач ({target})"
                if tasks > 0
                else "Сырья нет — запусти feed/поиск, затем повтори тест"
            ),
            "measured": {
                "earned_eur": round(earned, 4),
                "tasks_done": tasks,
                "pay_per_task_eur": round(pay_per_task, 4),
                "tasks_per_hour_est": tasks_per_hour,
                "execution_target": target,
                "elapsed_sec": elapsed_sec,
            },
            "checks": checks,
            "forecast": forecast,
            "adaptive_arbitrage": arbitrage,
            "sandbox_note": (
                "В sandbox цифры учебные. Реальные центы — после Scale/Toloka + VPS remote."
            ),
            "next_steps": [
                "FARM_EXECUTION_MODE=remote + FARM_WORKER_POOL_URL на VPS",
                "SCALE_API_KEY в .env.local",
                "Повтори тест — смотри pay_per_task_eur в логах",
            ],
        }

    def start_swarm(self, *, workers: int = 10) -> dict[str, Any]:
        from app.env_loader import load_local_env

        load_local_env()
        state = self._load_state()
        scale = self._check_scale_adapter()
        state["scale_ai_last"] = scale
        state["running"] = True
        state["workers_target"] = max(1, min(1000, int(workers)))
        state["workers_active"] = state["workers_target"]
        self._save_state(state)
        scale_skip = scale.get("status") == "no_key" or not scale.get("configured")
        self._log_event(
            {
                "id": uuid.uuid4().hex[:12],
                "at": datetime.now(timezone.utc).isoformat(),
                "adapter": "scale_ai_probe",
                "pay_eur": 0.0,
                "target": "scale_ai",
                "detail": (
                    "Scale: SKIP — Toloka-only (ключ не задан)"
                    if scale_skip
                    else (scale.get("log_line") or scale.get("message"))
                ),
                "ok": self._scale_probe_ok(scale),
                "skipped": scale_skip,
            }
        )
        from app.integration.swarm_bridge import ensure_swarm_importable

        ensure_swarm_importable()
        from swarm.adapter_toloka import TolokaAdapter

        toloka_key = self._priority_manager().vault.secret("TOLOKA_API_TOKEN")
        if toloka_key:
            toloka = TolokaAdapter(api_key=toloka_key).check_connection()
            self._log_event(
                {
                    "id": uuid.uuid4().hex[:12],
                    "at": datetime.now(timezone.utc).isoformat(),
                    "adapter": "toloka_probe",
                    "pay_eur": 0.0,
                    "target": "toloka",
                    "detail": toloka.get("message") or "Toloka Pipeline API",
                    "ok": bool(toloka.get("connected")),
                }
            )
        if not self._is_dry_run():
            self._refresh_live_test_if_stale(state)
            self._save_state(state)
        tick = self.run_tick()
        base_msg = f"Ферма запущена: {state['workers_target']} комбайнов"
        scale_msg = (
            "Scale пропущен · Toloka-only"
            if scale_skip
            else (scale.get("log_line") or scale.get("message", ""))
        )
        return {
            "ok": True,
            "message": f"{base_msg} · {scale_msg}",
            "scale_ai": scale,
            **tick,
        }

    def stop_swarm(self) -> dict[str, Any]:
        state = self._load_state()
        state["running"] = False
        state["workers_active"] = 0
        self._save_state(state)
        return {"ok": True, "message": "Ферма остановлена", "running": False}

    def _pick_tasks(self, limit: int) -> list[tuple[str, dict[str, Any]]]:
        """(adapter_id, opportunity_row) tasks from internal queue."""
        rows = self._opportunity.list_opportunities(source_id="asset_scan", limit=limit * 4)
        tasks: list[tuple[str, dict[str, Any]]] = []
        for row in rows:
            if len(tasks) >= limit:
                break
            meta = row.get("meta") if isinstance(row.get("meta"), dict) else {}
            target = str(row.get("company_name") or row.get("website_url") or row.get("id") or "")
            if not meta.get("farm_data_cleaned"):
                adapter_id = "data_clean"
            elif not meta.get("classified_niche"):
                adapter_id = "text_classify"
            elif not meta.get("farm_verified"):
                adapter_id = "record_verify"
            else:
                continue
            if not self._passes_min_task_price(adapter_id):
                self._log_price_filter_skip(adapter_id, target=target or adapter_id)
                continue
            tasks.append((adapter_id, row))
        return tasks

    def _run_data_clean(self, row: dict[str, Any]) -> dict[str, Any]:
        started = time.perf_counter()
        meta = dict(row.get("meta") or {})
        issues = meta.get("issues") or meta.get("site_issues") or []
        cleaned = [str(i).strip() for i in issues if str(i).strip()][:12]
        meta["issues"] = cleaned
        meta["farm_data_cleaned"] = True
        meta["farm_cleaned_at"] = datetime.now(timezone.utc).isoformat()
        self._opportunity.update(str(row["id"]), {"meta": meta})
        pay = _ADAPTER_PAY_EUR.get("data_clean", 0.02)
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        self._record_learning(adapter_id="data_clean", pay_eur=pay, duration_ms=duration_ms)
        return {
            "ok": True,
            "adapter": "data_clean",
            "detail": f"Очищено {len(cleaned)} записей",
            "duration_ms": duration_ms,
        }

    def _run_text_classify(self, row: dict[str, Any]) -> dict[str, Any]:
        started = time.perf_counter()
        meta = dict(row.get("meta") or {})
        analysis = {
            "issues": meta.get("issues") or [],
            "title": meta.get("title") or row.get("company_name"),
            "tech_stack": meta.get("tech_stack") or [],
            "url": row.get("website_url"),
        }
        route = self._priority_manager().route_legacy(
            adapter_id="text_classify",
            raw_text=" ".join(str(i) for i in (meta.get("issues") or [])[:8]),
            meta=meta,
        )
        result = self._ai.classify_niche(
            analysis=analysis,
            company=str(row.get("company_name") or ""),
            url=str(row.get("website_url") or ""),
            router_task=str(route.get("router_task") or "simple"),
        )
        meta["classified_niche"] = result.get("niche")
        meta["classified_label"] = result.get("label")
        meta["classified_source"] = result.get("source")
        meta["farm_data_cleaned"] = meta.get("farm_data_cleaned", True)
        self._opportunity.update(str(row["id"]), {"meta": meta})
        llm_cost = 0.001 if result.get("source") in {"llm", "llm_router"} else 0.0
        pay = _ADAPTER_PAY_EUR.get("text_classify", 0.03)
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        self._record_learning(
            adapter_id="text_classify",
            pay_eur=pay,
            llm_cost_eur=llm_cost,
            duration_ms=duration_ms,
        )
        return {
            "ok": True,
            "adapter": "text_classify",
            "detail": f"Ниша: {result.get('label')}",
            "llm_cost_eur": llm_cost,
            "router_task": route.get("router_task"),
            "duration_ms": duration_ms,
        }

    def _run_record_verify(self, row: dict[str, Any]) -> dict[str, Any]:
        started = time.perf_counter()
        url = str(row.get("website_url") or "").strip()
        ok = False
        detail = "Нет URL"
        if url.startswith(("http://", "https://")):
            try:
                res = stealth_fetch_get(url, timeout=8.0)
                ok = res.status_code < 500
                detail = f"HTTP {res.status_code}"
            except Exception as exc:
                detail = str(exc)[:80]
        meta = dict(row.get("meta") or {})
        meta["farm_verified"] = ok
        meta["farm_verify_detail"] = detail
        meta["farm_verified_at"] = datetime.now(timezone.utc).isoformat()
        self._opportunity.update(str(row["id"]), {"meta": meta})
        pay = _ADAPTER_PAY_EUR.get("record_verify", 0.01)
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        self._record_learning(adapter_id="record_verify", pay_eur=pay if ok else 0.0, duration_ms=duration_ms)
        return {"ok": ok, "adapter": "record_verify", "detail": detail, "duration_ms": duration_ms}

    def execute_labeling_batch(self, *, workers: int, adapter_id: str = "ai_labeling") -> dict[str, Any]:
        """Worker-pool endpoint — runs labeling on this node (VPS/cloud)."""
        if adapter_id != "ai_labeling":
            return {"ok": False, "message": f"Adapter {adapter_id} not supported on pool", "tasks_done": 0}
        labeling_workers = max(1, min(200, int(workers)))
        done = 0
        earned = 0.0
        llm_cost = 0.0
        results: list[dict[str, Any]] = []
        try:
            orch = build_swarm_orchestrator(
                self._opportunity,
                self._ai,
                memory_dir=self._memory,
            )
            swarm = orch.run_labeling_swarm(
                workers=labeling_workers,
                concurrency=min(labeling_workers * 3, 150),
            )
            for lr in swarm.results:
                if not lr.ok:
                    continue
                done += 1
                earned += lr.pay_eur
                llm_cost += lr.llm_cost_eur
                self._record_learning(
                    adapter_id="ai_labeling",
                    pay_eur=lr.pay_eur,
                    llm_cost_eur=lr.llm_cost_eur,
                    duration_ms=float(lr.duration_ms or 0),
                    cached=bool(lr.cached),
                )
                results.append(
                    {
                        "task_id": lr.task_id,
                        "pay_eur": lr.pay_eur,
                        "detail": lr.detail,
                        "cached": lr.cached,
                    }
                )
        except Exception as exc:
            return {
                "ok": False,
                "tasks_done": done,
                "earned_eur": round(earned, 4),
                "llm_cost_eur": round(llm_cost, 4),
                "message": str(exc)[:120],
                "results": results,
                "role": "worker_pool",
            }
        return {
            "ok": True,
            "tasks_done": done,
            "earned_eur": round(earned, 4),
            "llm_cost_eur": round(llm_cost, 4),
            "results": results[:10],
            "message": f"Worker pool: {done} разметок · +{earned:.2f} €",
            "role": "worker_pool",
        }

    def _run_labeling_local(
        self,
        *,
        labeling_workers: int,
        results: list[dict[str, Any]],
        state: dict[str, Any] | None = None,
    ) -> tuple[int, float, float]:
        done = 0
        earned = 0.0
        llm_cost = 0.0
        orch = build_swarm_orchestrator(
            self._opportunity,
            self._ai,
            memory_dir=self._memory,
        )
        swarm = orch.run_labeling_swarm(
            workers=labeling_workers,
            concurrency=min(labeling_workers * 3, 150),
        )
        for lr in swarm.results:
            if not lr.ok:
                continue
            done += 1
            earned += lr.pay_eur
            llm_cost += lr.llm_cost_eur
            self._record_learning(
                adapter_id="ai_labeling",
                pay_eur=lr.pay_eur,
                llm_cost_eur=lr.llm_cost_eur,
                duration_ms=float(lr.duration_ms or 0),
                cached=bool(lr.cached),
            )
            event = {
                "id": uuid.uuid4().hex[:12],
                "at": datetime.now(timezone.utc).isoformat(),
                "adapter": "ai_labeling",
                "pay_eur": lr.pay_eur,
                "target": lr.task_id,
                "detail": lr.detail,
                "ok": True,
                "flow": lr.flow,
                "execution": "local",
            }
            self._log_event(event)
            results.append(event)
            if state is not None:
                self._record_dry_run_completion(
                    state,
                    adapter_id="ai_labeling",
                    task_id=lr.task_id,
                    llm_cost_eur=lr.llm_cost_eur,
                )
        if done > 0:
            self._emit_task_lifecycle(
                adapter="ai_labeling",
                task_id=f"{done} разметок",
                pay_eur=round(earned / done, 4),
                ok=True,
            )
        return done, earned, llm_cost

    def run_tick(self, *, workers: int | None = None) -> dict[str, Any]:
        state = self._load_state()
        self._reset_today_if_needed(state)
        self._apply_self_healing(state)
        batch = workers or (state["workers_active"] if state["running"] else 10)
        batch = max(1, min(200, int(batch)))
        pm = self._priority_manager()
        combiner_ids = tuple(_ADAPTER_PAY_EUR.keys())
        allocation = pm.allocate_workers(
            batch,
            combiner_ids,
            disabled_adapters=set(state.get("disabled_adapters") or []),
        )
        labeling_workers = allocation.get("ai_labeling", batch)

        done = 0
        earned = 0.0
        llm_cost = 0.0
        results: list[dict[str, Any]] = []
        execution_meta: dict[str, Any]
        remote_result: dict[str, Any] | None = None

        if self._is_dry_run():
            execution_meta = {
                "target": "local",
                "mode": "local",
                "adapter_id": "ai_labeling",
                "note": "DRY RUN — FARM_EXECUTION_MODE=local, remote отключён",
            }
            _farm_logger.info("[DRY RUN] Farm tick · local execution · potential profit logging ON")
        else:
            execution_meta = pm.dispatcher.resolve_execution(
                adapter_id="ai_labeling",
                profitable=True,
            )

        if not self._is_dry_run() and execution_meta.get("target") == "remote":
            remote_result = pm.dispatcher.dispatch_batch(
                workers=labeling_workers,
                adapter_id="ai_labeling",
            )
            if remote_result.get("ok"):
                done = int(remote_result.get("tasks_done") or 0)
                earned = float(remote_result.get("earned_eur") or 0)
                llm_cost = float(remote_result.get("llm_cost_eur") or 0)
                for item in remote_result.get("results") or []:
                    if not isinstance(item, dict):
                        continue
                    event = {
                        "id": uuid.uuid4().hex[:12],
                        "at": datetime.now(timezone.utc).isoformat(),
                        "adapter": "ai_labeling",
                        "pay_eur": float(item.get("pay_eur") or 0),
                        "target": item.get("task_id") or "remote",
                        "detail": item.get("detail") or remote_result.get("message"),
                        "ok": True,
                        "execution": "remote",
                    }
                    self._log_event(event)
                    results.append(event)
                self._log_event(
                    {
                        "id": uuid.uuid4().hex[:12],
                        "at": datetime.now(timezone.utc).isoformat(),
                        "adapter": "cloud_dispatch",
                        "pay_eur": earned,
                        "target": pm.dispatcher.pool_url(),
                        "detail": remote_result.get("message"),
                        "ok": True,
                        "execution": "remote",
                    }
                )

        if done < labeling_workers and (remote_result is None or remote_result.get("fallback_local")):
            try:
                local_done, local_earned, local_cost = self._run_labeling_local(
                    labeling_workers=labeling_workers - done if remote_result and remote_result.get("ok") else labeling_workers,
                    results=results,
                    state=state,
                )
                done += local_done
                earned += local_earned
                llm_cost += local_cost
            except Exception as exc:
                self._log_event(
                    {
                        "id": uuid.uuid4().hex[:12],
                        "at": datetime.now(timezone.utc).isoformat(),
                        "adapter": "ai_labeling",
                        "pay_eur": 0.0,
                        "target": "swarm",
                        "detail": str(exc)[:120],
                        "ok": False,
                        "execution": "local",
                    }
                )

        if done < batch:
            legacy = self._run_legacy_adapters(batch - done, state=state)
            done += legacy["tasks_done"]
            earned += legacy["earned_eur"]
            llm_cost += legacy["llm_cost_eur"]
            results.extend(legacy["results"])

        state["total_tasks_done"] = int(state.get("total_tasks_done") or 0) + done
        state["total_earned_eur"] = round(float(state.get("total_earned_eur") or 0) + earned, 4)
        state["today_earned_eur"] = round(float(state.get("today_earned_eur") or 0) + earned, 4)
        state["llm_cost_eur"] = round(float(state.get("llm_cost_eur") or 0) + llm_cost, 4)
        state["last_tick_at"] = datetime.now(timezone.utc).isoformat()
        state["last_execution"] = execution_meta
        if state["running"] and not state.get("workers_active"):
            state["workers_active"] = state.get("workers_target", 10)
        self._save_state(state)

        if earned > 0:
            from app.integration.swarm_bridge import ensure_swarm_importable

            ensure_swarm_importable()
            from swarm.farm_lifecycle_ru import STAGE_BALANCE_INCREASED

            self._log_lifecycle_event(
                stage=STAGE_BALANCE_INCREASED,
                adapter="farm_tick",
                task_id=f"tick-{state['last_tick_at'][:19]}",
                pay_eur=round(earned, 4),
                ok=True,
                balance_after_eur=float(state.get("total_earned_eur") or 0),
            )

        toloka_submit = self._auto_submit_toloka_if_ready()
        pending_submit = int((toloka_submit or {}).get("pending") or 0) if toloka_submit else 0

        tick_payload = {
            "tasks_done": done,
            "earned_eur": round(earned, 4),
            "llm_cost_eur": round(llm_cost, 4),
        }
        finance_guard = self._finance_guard_tick(
            state,
            earned=earned,
            llm_cost=llm_cost,
            tasks_done=done,
            pending_submit=pending_submit,
        )
        if finance_guard.get("stop_farm"):
            self._save_state(state)
        evidence = self._refresh_commercial_evidence(farm_state=state, tick_result=tick_payload)

        return {
            "ok": True,
            "tasks_done": done,
            "earned_eur": round(earned, 4),
            "llm_cost_eur": round(llm_cost, 4),
            "results": results[:10],
            "execution": execution_meta,
            "toloka_submit": toloka_submit,
            "finance_guard": finance_guard,
            "commercial_evidence": evidence,
            "message": (
                f"Рой ({execution_meta.get('target', 'local')}): {done} задач · +{earned:.2f} €"
                if done
                else "Нет сырья — нажмите «Запустить ферму» (поиск + разметка)"
            ),
        }

    def _run_legacy_adapters(self, limit: int, *, state: dict[str, Any] | None = None) -> dict[str, Any]:
        tasks = self._pick_tasks(limit)
        done = 0
        earned = 0.0
        llm_cost = 0.0
        results: list[dict[str, Any]] = []
        runners = {
            "data_clean": self._run_data_clean,
            "text_classify": self._run_text_classify,
            "record_verify": self._run_record_verify,
        }
        disabled = set(self._load_state().get("disabled_adapters") or [])
        for adapter_id, row in tasks:
            if adapter_id in disabled:
                continue
            runner = runners.get(adapter_id)
            if not runner:
                continue
            pay = _ADAPTER_PAY_EUR.get(adapter_id, 0.01)
            target = str(row.get("company_name") or row.get("website_url") or row.get("id") or adapter_id)
            if not self._passes_min_task_price(adapter_id):
                self._log_price_filter_skip(adapter_id, target=target)
                continue
            try:
                outcome = runner(row)
                earned += pay
                llm_cost += float(outcome.get("llm_cost_eur") or 0)
                done += 1
                target = str(row.get("company_name") or row.get("website_url") or row.get("id") or adapter_id)
                self._emit_task_lifecycle(
                    adapter=adapter_id,
                    task_id=target,
                    pay_eur=pay,
                    ok=bool(outcome.get("ok", True)),
                    balance_after_eur=(
                        float(state.get("total_earned_eur") or 0) + earned + pay if state is not None else None
                    ),
                )
                results.append(
                    {
                        "adapter": adapter_id,
                        "pay_eur": pay,
                        "target": target,
                        "detail": outcome.get("detail"),
                        "ok": outcome.get("ok", True),
                    }
                )
                if state is not None and outcome.get("ok", True):
                    self._record_dry_run_completion(
                        state,
                        adapter_id=adapter_id,
                        task_id=str(row.get("id") or row.get("company_name") or adapter_id),
                        llm_cost_eur=float(outcome.get("llm_cost_eur") or 0),
                    )
            except Exception:
                pass
        return {
            "tasks_done": done,
            "earned_eur": earned,
            "llm_cost_eur": llm_cost,
            "results": results,
        }

    def _platforms(self) -> list[dict[str, Any]]:
        from app.integration.swarm_bridge import ensure_swarm_importable

        ensure_swarm_importable()
        from swarm.platform_registry import list_platforms

        return list_platforms()

    def _ceo_checklist(self) -> list[dict[str, str]]:
        from app.integration.swarm_bridge import ensure_swarm_importable

        ensure_swarm_importable()
        from swarm.platform_registry import ceo_checklist

        return ceo_checklist()

    def labels_export_path(self) -> Path:
        return self._memory / "swarm_labels_export.jsonl"

    def labels_export_count(self) -> int:
        path = self.labels_export_path()
        if not path.is_file():
            return 0
        return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())

    def labels_export_text(self) -> str:
        path = self.labels_export_path()
        if not path.is_file():
            return ""
        return path.read_text(encoding="utf-8")

    def _toloka_submitter(self) -> Any:
        from app.integration.swarm_bridge import ensure_swarm_importable

        ensure_swarm_importable()
        from swarm.adapter_toloka import TolokaAdapter
        from swarm.toloka_submit import TolokaLabelSubmitter

        key = self._priority_manager().vault.secret("TOLOKA_API_TOKEN")
        adapter = TolokaAdapter(api_key=key) if key else TolokaAdapter()
        return TolokaLabelSubmitter(
            memory_dir=self._memory,
            adapter=adapter,
            opportunity_lookup=self._opportunity,
        )

    def toloka_submit_status(self) -> dict[str, Any]:
        status = self._toloka_submitter().status()
        run_id = status.get("last_run_id")
        if run_id and status.get("connected"):
            submitter = self._toloka_submitter()
            state = submitter.load_state()
            if state.get("last_run_status") not in {"succeeded", "success", "completed", "failed"}:
                submitter._poll_run_status(str(run_id), state)
                submitter.save_state(state)
                status = submitter.status()
        return status

    def first_euro_gate(self) -> dict[str, Any]:
        from app.integration.first_euro_gate import attach_evidence_to_gate, build_first_euro_gate, load_ceo_flags

        state = self._load_state()
        toloka = self.toloka_submit_status()
        gate = build_first_euro_gate(
            memory_dir=self._memory,
            toloka_status=toloka,
            farm_state=state,
            payment_monitor=self._payment_monitor_for_dashboard(),
            pipeline_success_count=int(toloka.get("pipeline_success_count") or 0),
        )
        return attach_evidence_to_gate(gate, self.commercial_evidence())

    def commercial_evidence(self) -> dict[str, Any] | None:
        from app.integration.commercial_evidence import load_latest_evidence

        return load_latest_evidence(self._memory)

    def _refresh_commercial_evidence(
        self,
        *,
        farm_state: dict[str, Any],
        tick_result: dict[str, Any],
        spider_meta: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        from app.integration.commercial_evidence import build_commercial_evidence, save_evidence
        from app.integration.first_euro_gate import load_ceo_flags

        report = build_commercial_evidence(
            memory_dir=self._memory,
            farm_state=farm_state,
            toloka_status=self.toloka_submit_status(),
            ceo_flags=load_ceo_flags(self._memory),
            last_tick=tick_result,
            spider_meta=spider_meta or farm_state.get("last_spider_scan"),
        )
        save_evidence(self._memory, report)
        return report

    def _finance_guard_tick(
        self,
        state: dict[str, Any],
        *,
        earned: float,
        llm_cost: float,
        tasks_done: int,
        pending_submit: int = 0,
    ) -> dict[str, Any]:
        from app.integration.swarm_bridge import ensure_swarm_importable

        ensure_swarm_importable()
        from swarm.finance_guard import FinanceGuard

        guard = FinanceGuard(self._memory).evaluate_tick(
            earned_eur=earned,
            llm_cost_eur=llm_cost,
            tasks_done=tasks_done,
            farm_state=state,
            pending_submit=pending_submit,
        )
        if guard.get("stop_farm") and state.get("running"):
            state["running"] = False
            state["workers_active"] = 0
            self._log_event(
                {
                    "id": uuid.uuid4().hex[:12],
                    "at": datetime.now(timezone.utc).isoformat(),
                    "adapter": "finance_guard",
                    "pay_eur": 0.0,
                    "target": "farm",
                    "detail": guard.get("message_ru") or "Finance Guard: стоп фермы",
                    "title_ru": "Финансовый сторож: остановка",
                    "ok": False,
                }
            )
        return guard

    def _finance_guard_snapshot(self) -> dict[str, Any]:
        from app.integration.swarm_bridge import ensure_swarm_importable

        ensure_swarm_importable()
        from swarm.finance_guard import FinanceGuard

        toloka = self.toloka_submit_status()
        from app.integration.first_euro_gate import load_ceo_flags

        return FinanceGuard(self._memory).dashboard(
            farm_state=self._load_state(),
            pending_submit=int(toloka.get("pending_count") or 0),
            submitted_total=int(toloka.get("submitted_count") or 0),
            toloka_status=toloka,
            ceo_flags=load_ceo_flags(self._memory),
        )

    def farm_program(self) -> dict[str, Any]:
        from app.integration.commercial_experiment_journal import ensure_baseline_experiments, list_experiments
        from app.integration.farm_program import build_farm_program, error_ledger_from_memory
        from app.integration.first_euro_gate import load_ceo_flags
        from app.integration.revenue_replay import load_replay_snapshot

        ensure_baseline_experiments(self._memory)
        state = self._load_state()
        toloka = self.toloka_submit_status()
        gate = self.first_euro_gate()
        return build_farm_program(
            vre_gate=gate,
            finance_guard=self._finance_guard_snapshot(),
            commercial_evidence=self.commercial_evidence(),
            toloka_status=toloka,
            farm_state=state,
            labels_export_count=self.labels_export_count(),
            ceo_flags=load_ceo_flags(self._memory),
            error_ledger_summary=error_ledger_from_memory(self._memory),
            commercial_experiments=list_experiments(self._memory),
            revenue_replay=load_replay_snapshot(self._memory),
            production_platform=self.production_platform(),
        )

    def production_platform(self) -> dict[str, Any]:
        return self._cached_section("production_platform", self._build_production_platform)

    def _build_production_platform(self) -> dict[str, Any]:
        from app.integration.production_platform import build_production_platform

        gate = self.first_euro_gate()
        return build_production_platform(
            farm_state={
                "labels_export_count": self.labels_export_count(),
                "total_tasks_done": int(self._load_state().get("total_tasks_done") or 0),
            },
            toloka_verdict=str(gate.get("verdict") or ""),
        )

    def auto_quote(self, *, service_id: str, volume: float, workers: int = 10) -> dict[str, Any]:
        from app.integration.production_platform import auto_quote_from_rows, cost_engine_quote

        if service_id == "svc_data_qa" and volume == int(volume):
            return auto_quote_from_rows(row_count=int(volume), workers=workers)
        q = cost_engine_quote(service_id=service_id, volume=volume, workers=workers)
        if not q.get("ok"):
            return q
        vol = int(volume) if volume == int(volume) else volume
        return {
            **q,
            "quote_type": "auto_quote",
            "input_ru": f"Объём · {vol:,} {q.get('volume_unit_ru', '')}".replace(",", " "),
            "invoice_line_ru": (
                f"Объём {vol:,} · Стоимость {q['sell_price_eur']:.2f} € · "
                f"Срок {q['duration_label_ru']}"
            ).replace(",", " "),
            "cta_ru": "Подтвердите заказ — конвейер запустится с тем же Workers/Export, выход B2B JSON/CSV",
        }

    def opportunity_discovery(self) -> dict[str, Any]:
        return self._cached_section("opportunity_discovery", self._build_opportunity_discovery)

    def _build_opportunity_discovery(self) -> dict[str, Any]:
        from app.integration.opportunity_discovery_engine import build_opportunity_discovery

        hunter_rows = 0
        ds_path = self._memory / "hunter_dataset.jsonl"
        if ds_path.is_file():
            hunter_rows = sum(1 for ln in ds_path.read_text(encoding="utf-8").splitlines() if ln.strip())

        gate = self.first_euro_gate()
        state = self._load_state()
        opportunities = self._opportunity.list_opportunities(limit=80)
        return build_opportunity_discovery(
            opportunities,
            farm_state={
                "labels_export_count": self.labels_export_count(),
                "hunter_dataset_rows": hunter_rows,
            },
            toloka_verdict=str(gate.get("verdict") or ""),
            workers=int(state.get("workers_target") or 10),
            memory_dir=self._memory,
        )

    def prepare_opportunity_proposal(self, opportunity_id: str) -> dict[str, Any]:
        from app.integration.opportunity_discovery_engine import prepare_commercial_proposal

        row = self._opportunity.get(opportunity_id)
        if not row:
            return {"ok": False, "message_ru": "Возможность не найдена"}
        all_rows = self._opportunity.list_opportunities(limit=500)
        prep = prepare_commercial_proposal(row, all_rows=all_rows)
        if prep.get("ok"):
            self._opportunity.update(
                opportunity_id,
                {
                    "proposed_message": prep["proposal_ru"],
                    "recommended_package_id": prep["recommended_package_id"],
                    "recommended_price_eur": prep["recommended_price_eur"],
                    "pricing_rationale": f"Win {prep.get('win_probability_pct')}%",
                    "status": "proposed",
                    "outreach_status": "pending_approval",
                },
            )
        return prep

    def record_opportunity_lost(self, opportunity_id: str, *, reason_code: str, note_ru: str = "") -> dict[str, Any]:
        from app.integration.opportunity_discovery_engine import record_lost_reason

        row = self._opportunity.get(opportunity_id)
        if not row:
            return {"ok": False, "message_ru": "Возможность не найдена"}
        entry = record_lost_reason(
            opportunity_id=opportunity_id,
            reason_code=reason_code,
            company_name=str(row.get("company_name") or ""),
            note_ru=note_ru,
            memory_dir=self._memory,
        )
        meta = dict(row.get("meta") or {})
        meta["lost_reason_code"] = entry["reason_code"]
        meta["lost_reason_ru"] = entry["reason_ru"]
        meta["lost_at"] = entry["at"]
        self._opportunity.update(
            opportunity_id,
            {"status": "lost", "notes": note_ru or entry["reason_ru"], "meta": meta},
        )
        return {"ok": True, "message_ru": f"Отказ записан: {entry['reason_ru']}", "entry": entry}

    def commercial_experiments(self) -> list[dict[str, Any]]:
        from app.integration.commercial_experiment_journal import ensure_baseline_experiments, list_experiments

        ensure_baseline_experiments(self._memory)
        return list_experiments(self._memory)

    def run_revenue_replay(self, *, workers: int = 10) -> dict[str, Any]:
        """Повторить последний полевой прогон: start → tick → submit (+ save snapshot)."""
        from app.integration.revenue_replay import (
            build_snapshot_from_run,
            load_replay_snapshot,
            save_replay_snapshot,
        )

        prev = load_replay_snapshot(self._memory)
        w = max(1, min(100, int((prev or {}).get("workers") or workers)))
        start = self.start_swarm(workers=w)
        tick = self.run_tick(workers=w)
        submit = self.submit_toloka_labels(limit=50)
        toloka = self.toloka_submit_status()
        snap = build_snapshot_from_run(
            workers=w,
            feed_ok=False,
            tick_tasks=int(tick.get("tasks_done") or 0),
            submit_result=submit,
            toloka_status=toloka,
        )
        save_replay_snapshot(self._memory, snap)
        return {
            "ok": True,
            "message": "Revenue Replay: start → tick → submit (snapshot сохранён)",
            "workers": w,
            "start": start,
            "tick": tick,
            "submit": submit,
            "replay_snapshot": snap,
            "program": self.farm_program(),
        }

    def verified_revenue_engine(self) -> dict[str, Any]:
        return self.first_euro_gate()

    def confirm_first_euro_step(self, step_id: str, *, done: bool = True) -> dict[str, Any]:
        from app.integration.commercial_experiment_journal import append_experiment
        from app.integration.first_euro_gate import save_ceo_flag

        flags = save_ceo_flag(self._memory, step_id, done=done)
        gate = self.first_euro_gate()
        if done and step_id == "wallet_toloka":
            append_experiment(
                self._memory,
                channel="toloka_requester",
                outcome_ru="CEO: wallet подтверждён",
                outcome_code="CEO_WALLET",
                detail_ru="Truth Engine → CEO_CONFIRMATION",
                vre_level=int(gate.get("vre_level") or 0),
            )
        elif done and step_id == "vre_cycle_repeat":
            append_experiment(
                self._memory,
                channel="toloka_requester",
                outcome_ru="Цикл повторён ≥3",
                outcome_code="VRE_L4",
                detail_ru="Verified Revenue Engine",
                vre_level=4,
            )
        return {"ok": True, "step_id": step_id, "done": done, "flags": flags, "gate": gate}

    def submit_toloka_labels(self, *, limit: int = 50, trigger_run: bool | None = None) -> dict[str, Any]:
        from app.env_loader import load_local_env

        load_local_env()
        submitter = self._toloka_submitter()
        result = submitter.submit_pending(limit=limit, trigger_run=trigger_run)
        submitted = int(result.get("submitted") or 0)
        if submitted > 0:
            detail = result.get("message") or f"Toloka приняла {submitted} разметок"
            self._log_lifecycle_event(
                stage="task_completed",
                adapter="toloka_submit",
                task_id=f"{submitted} разметок → Toloka",
                pay_eur=0.0,
                ok=True,
                platform="Toloka Pipeline",
            )
            self._log_event(
                {
                    "id": uuid.uuid4().hex[:12],
                    "at": datetime.now(timezone.utc).isoformat(),
                    "adapter": "toloka_submit",
                    "pay_eur": 0.0,
                    "target": str(result.get("dataset_id") or "toloka")[:48],
                    "detail": detail,
                    "title_ru": "Пакет отправлен на Toloka",
                    "lifecycle_stage": "task_completed",
                    "ok": True,
                }
            )
            state = self._load_state()
            self._refresh_commercial_evidence(
                farm_state=state,
                tick_result={"tasks_done": 0, "earned_eur": 0, "llm_cost_eur": 0},
            )
        elif not result.get("ok"):
            self._log_event(
                {
                    "id": uuid.uuid4().hex[:12],
                    "at": datetime.now(timezone.utc).isoformat(),
                    "adapter": "toloka_submit",
                    "pay_eur": 0.0,
                    "target": "toloka",
                    "detail": str(result.get("message") or "submit failed")[:160],
                    "title_ru": "Toloka: ошибка отправки",
                    "ok": False,
                }
            )
        return result

    def _auto_submit_toloka_if_ready(self) -> dict[str, Any] | None:
        submitter = self._toloka_submitter()
        if not submitter.auto_submit_enabled():
            return None
        if submitter.status().get("pending_count", 0) <= 0:
            return None
        return self.submit_toloka_labels(limit=50)

    def dashboard(self, owner_name: str = "Владелец") -> dict[str, Any]:
        from app.env_loader import load_local_env

        load_local_env()
        state = self._load_state()
        self._reset_today_if_needed(state)
        self._save_state(state)
        fin = self._finance.financial_view()
        sandbox = self._business_mode.is_sandbox()
        net = round(
            float(state.get("today_earned_eur") or 0) - float(state.get("llm_cost_eur") or 0),
            4,
        )

        combiner_labels = {
            "ai_labeling": "AI-разметка (главный комбайн)",
            "data_clean": "Чистка данных",
            "text_classify": "Классификация текста",
            "record_verify": "Проверка записи",
        }
        combiners = [
            {
                "id": aid,
                "label": combiner_labels.get(aid, aid),
                "pay_eur": pay,
                "pay_label": f"+{pay:.2f} € за задачу",
                "primary": aid == "ai_labeling",
            }
            for aid, pay in _ADAPTER_PAY_EUR.items()
        ]

        worker_flow = [
            {
                "step": 1,
                "id": "trigger",
                "title": "Находим задачу",
                "detail": "Сканеры и внутренняя очередь дают сырой текст для разметки.",
            },
            {
                "step": 2,
                "id": "compute",
                "title": "ИИ размечает",
                "detail": "Groq / Gemini Flash ставит теги, нишу и оценку качества.",
            },
            {
                "step": 3,
                "id": "execution",
                "title": "Отправляем результат",
                "detail": "Пакет уходит в swarm_labels_export.jsonl → auto-submit на Toloka (live).",
            },
            {
                "step": 4,
                "id": "result",
                "title": "Микро-оплата",
                "detail": "Копейки за задачу суммируются на счёт фермы.",
            },
        ]

        return {
            "mode": "micro_farm",
            "owner_name": owner_name,
            "running": bool(state.get("running")),
            "workers_active": int(state.get("workers_active") or 0),
            "workers_target": int(state.get("workers_target") or 10),
            "today_earned_eur": float(state.get("today_earned_eur") or 0),
            "total_earned_eur": float(state.get("total_earned_eur") or 0),
            "total_tasks_done": int(state.get("total_tasks_done") or 0),
            "llm_cost_eur": float(state.get("llm_cost_eur") or 0),
            "net_profit_eur": max(0.0, net),
            "available_for_withdraw_eur": fin.get("available_for_withdrawal_eur", 0.0),
            "withdraw_min_eur": 5.0,
            "sandbox": sandbox,
            "balance_label": (
                "Накоплено (учебный режим — не банк)"
                if sandbox
                else "Накоплено на счёте"
            ),
            "combiners": combiners,
            "worker_flow": worker_flow,
            "primary_combiner": "ai_labeling",
            "async_concurrency": min(int(state.get("workers_target") or 10) * 3, 150),
            "platforms": self._platforms(),
            "ceo_checklist": self._ceo_checklist(),
            "labels_export_count": self.labels_export_count(),
            "labels_export_ready": self.labels_export_count() > 0,
            "scale_ai": state.get("scale_ai_last")
            or self._cached_section("scale_ai", self._check_scale_adapter),
            "priority_manager": self._priority_manager().snapshot(),
            "revenue_forecast": self._cached_section(
                "revenue_forecast",
                lambda: self.revenue_forecast(
                    labeling_nodes=int(state.get("workers_target") or 10),
                ),
            ),
            "last_battle_test": state.get("last_battle_test"),
            "platform_vault": self.platform_vault_status(),
            "global_spider": self.global_spider_vector(),
            "prepare_live": self.prepare_live_mode(),
            "dry_run": self.dry_run_status(),
            "payment_monitor": self._cached_section(
                "payment_monitor",
                self._payment_monitor_for_dashboard,
            ),
            "last_live_connection_test": state.get("last_live_connection_test"),
            "payout_guide": self._payout_guide(),
            "toloka_submit": self.toloka_submit_status(),
            "first_euro_gate": self._cached_section("first_euro_gate", self.first_euro_gate),
            "verified_revenue_engine": self._cached_section(
                "verified_revenue_engine",
                self.verified_revenue_engine,
            ),
            "commercial_evidence": self.commercial_evidence(),
            "finance_guard": self._finance_guard_snapshot(),
            "farm_program": self._cached_section("farm_program", self.farm_program),
            "production_platform": self.production_platform(),
            "opportunity_discovery": self.opportunity_discovery(),
            "recent_tasks": self._recent_events(15),
            "last_tick_at": state.get("last_tick_at"),
            "honesty_note": (
                "Биржи (Scale, Toloka, MTurk…) подключаются только твоим API-ключом — "
                "без регистрации на площадке Genesis не может получать реальные €. "
                "Внутренняя ферма и экспорт разметки работают уже сейчас."
            ),
            "cost_ratio_note": (
                f"Расход ИИ: {float(state.get('llm_cost_eur') or 0):.3f} € · "
                f"доход сегодня: {float(state.get('today_earned_eur') or 0):.2f} €"
            ),
        }
