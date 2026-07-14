"""Finance Guard — факт tick + прогноз «Сегодня» (расход / ожидаемый доход / ROI)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

DEFAULT_NEGATIVE_STREAK_STOP = 3


def _truthy(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _pay_per_task() -> float:
    try:
        return max(0.0, float(os.getenv("TOLOKA_EXPECTED_PAY_EUR", "0") or 0))
    except (TypeError, ValueError):
        return 0.0


def _infra_today_eur() -> float:
    try:
        hour = float(os.getenv("FARM_INFRA_EUR_PER_HOUR", "0") or 0)
    except (TypeError, ValueError):
        hour = 0.0
    if hour <= 0:
        return 0.0
    # грубая оценка: ферма RUN ~8ч/день CEO-path
    return round(hour * 8, 4)


class FinanceGuard:
    """Сравнивает расход LLM с доходом и прогнозом — защита от работы в минус."""

    def __init__(self, memory_dir: Path) -> None:
        self._path = memory_dir / "finance_guard_state.json"

    def _load(self) -> dict[str, Any]:
        if not self._path.is_file():
            return {"negative_streak": 0, "last_actions": []}
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {"negative_streak": 0}
        except (json.JSONDecodeError, OSError):
            return {"negative_streak": 0}

    def _save(self, data: dict[str, Any]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        actions = data.get("last_actions") or []
        if len(actions) > 20:
            data["last_actions"] = actions[-20:]
        self._path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def daily_forecast(
        self,
        *,
        farm_state: dict[str, Any],
        pending_submit: int = 0,
        submitted_total: int = 0,
        verified_income_eur: float | None = None,
    ) -> dict[str, Any]:
        """Прогноз «Сегодня»: расход vs ожидаемый доход vs ROI %."""
        spend_llm = round(float(farm_state.get("llm_cost_eur") or 0), 4)
        spend_infra = _infra_today_eur()
        spend_total = round(spend_llm + spend_infra, 4)

        ledger_earned = round(float(farm_state.get("today_earned_eur") or 0), 4)
        tasks_today = int(farm_state.get("total_tasks_done") or 0)
        pay = _pay_per_task()

        pending_income = round(pay * pending_submit, 4) if pay > 0 else 0.0
        task_income = round(pay * max(0, tasks_today), 4) if pay > 0 else ledger_earned
        expected_gross = round(max(ledger_earned, task_income, pending_income), 4)

        if pay <= 0:
            expected_note_ru = (
                "Задай TOLOKA_EXPECTED_PAY_EUR — иначе gross = учебный ledger, не Toloka"
            )
        else:
            expected_note_ru = (
                f"Gross: {pay:.4f} €/задача · pending {pending_submit} · "
                f"ledger {ledger_earned:.4f} €"
            )

        net_forecast = round(expected_gross - spend_total, 4)
        roi_pct: float | None = None
        if spend_total > 0:
            roi_pct = round((net_forecast / spend_total) * 100, 1)

        outlook = "positive" if net_forecast >= 0 else "negative"
        if pay <= 0 and spend_total > 0 and ledger_earned <= 0:
            outlook = "unknown"

        net_profit_forecast_eur = net_forecast  # alias: прибыль после расходов

        confirmed = verified_income_eur
        if confirmed is None:
            confirmed = 0.0
        confirmed = round(max(0.0, float(confirmed)), 4)
        cost_per_verified_eur: float | None = None
        if confirmed > 0 and spend_total >= 0:
            cost_per_verified_eur = round(spend_total / confirmed, 4)
        cost_per_euro_note_ru: str | None = None
        if cost_per_verified_eur is not None:
            econ = "положительная" if cost_per_verified_eur < 1.0 else "отрицательная"
            cost_per_euro_note_ru = (
                f"Чтобы заработать 1 € (подтверждённо), потрачено {cost_per_verified_eur:.2f} €. "
                f"Экономика {econ}."
            )

        return {
            "label_ru": "Сегодня",
            "spend_eur": spend_total,
            "spend_llm_eur": spend_llm,
            "spend_infra_eur": spend_infra,
            "expected_gross_revenue_eur": expected_gross,
            "expected_income_eur": expected_gross,  # deprecated alias
            "ledger_earned_eur": ledger_earned,
            "net_profit_forecast_eur": net_profit_forecast_eur,
            "net_forecast_eur": net_forecast,
            "roi_pct": roi_pct,
            "outlook": outlook,
            "pay_per_task_eur": pay,
            "gross_vs_profit_note_ru": "Gross = оборот до расходов · Net = прибыль после LLM/VPS",
            "expected_note_ru": expected_note_ru,
            "summary_ru": (
                f"Сегодня · расход {spend_total:.2f} € · валовой доход {expected_gross:.2f} € · "
                f"прибыль ~{net_profit_forecast_eur:.2f} € · ROI {roi_pct if roi_pct is not None else '—'}%"
            ),
            "verified_income_eur": confirmed,
            "cost_per_verified_eur": cost_per_verified_eur,
            "cost_per_euro_note_ru": cost_per_euro_note_ru,
        }

    def evaluate_tick(
        self,
        *,
        earned_eur: float,
        llm_cost_eur: float,
        tasks_done: int,
        farm_state: dict[str, Any] | None = None,
        pending_submit: int = 0,
    ) -> dict[str, Any]:
        infra_hour = float(os.getenv("FARM_INFRA_EUR_PER_HOUR", "0") or 0)
        infra_tick = infra_hour / 360.0 if infra_hour > 0 else 0.0
        pay = _pay_per_task()
        expected_tick = pay * tasks_done if pay > 0 else earned_eur
        revenue = max(earned_eur, expected_tick)
        net = round(revenue - llm_cost_eur - infra_tick, 6)
        profitable = net >= 0 or tasks_done == 0

        state = self._load()
        streak = int(state.get("negative_streak") or 0)
        if tasks_done > 0 and net < 0 and pay > 0:
            streak += 1
        elif tasks_done > 0 and (net >= 0 or pay <= 0):
            streak = max(0, streak - 1) if net >= 0 else streak

        action = None
        stop_farm = False
        if streak >= DEFAULT_NEGATIVE_STREAK_STOP and _truthy("FARM_FINANCE_GUARD_STOP"):
            action = "stop_farm"
            stop_farm = True
        elif net < 0 and tasks_done > 0 and pay > 0:
            action = "warn_negative"

        forecast = None
        if farm_state is not None:
            forecast = self.daily_forecast(
                farm_state=farm_state,
                pending_submit=pending_submit,
            )

        result: dict[str, Any] = {
            "profitable": profitable,
            "net_eur": net,
            "earned_eur": earned_eur,
            "expected_eur": round(expected_tick, 4),
            "llm_cost_eur": llm_cost_eur,
            "infra_eur_tick": round(infra_tick, 6),
            "negative_streak": streak,
            "action": action,
            "stop_farm": stop_farm,
            "forecast": forecast,
            "message_ru": (
                forecast["summary_ru"]
                if forecast
                else (
                    f"Tick в минус: {net:.4f} € · серия {streak}"
                    if net < 0 and tasks_done > 0
                    else f"Tick OK: net {net:.4f} €"
                )
            ),
            "hint_ru": (
                "TOLOKA_EXPECTED_PAY_EUR — ставка Toloka для прогноза · "
                "FARM_FINANCE_GUARD_STOP=1 — стоп после 3 минус-tick (только при заданной ставке)"
            ),
        }

        state["negative_streak"] = streak
        state["last_net_eur"] = net
        if action:
            actions = list(state.get("last_actions") or [])
            actions.append({"action": action, "net_eur": net, "streak": streak})
            state["last_actions"] = actions
        self._save(state)
        return result

    def dashboard(
        self,
        *,
        farm_state: dict[str, Any],
        pending_submit: int = 0,
        submitted_total: int = 0,
        toloka_status: dict[str, Any] | None = None,
        ceo_flags: dict[str, bool] | None = None,
        verified_income_eur: float | None = None,
    ) -> dict[str, Any]:
        snap = self._load()
        flags = ceo_flags or {}
        if verified_income_eur is None and flags.get("wallet_toloka"):
            verified_income_eur = float(farm_state.get("total_earned_eur") or farm_state.get("today_earned_eur") or 0)
        forecast = self.daily_forecast(
            farm_state=farm_state,
            pending_submit=pending_submit,
            submitted_total=submitted_total,
            verified_income_eur=verified_income_eur if flags.get("wallet_toloka") else 0.0,
        )
        from swarm.revenue_confidence import compute_revenue_confidence

        ts = toloka_status or {
            "connected": submitted_total > 0,
            "submitted_count": submitted_total,
            "pending_count": pending_submit,
            "last_run_status": "",
            "pipeline_success_count": 0,
        }
        confidence = compute_revenue_confidence(
            farm_state=farm_state,
            toloka_status=ts,
            ceo_flags=ceo_flags or {},
            pay_per_task_eur=float(forecast.get("pay_per_task_eur") or _pay_per_task()),
        )
        return {
            **snap,
            "forecast": forecast,
            "revenue_confidence": confidence,
        }

    def snapshot(self) -> dict[str, Any]:
        return self._load()
