"""Micro-Farm — distributed micro-agent swarm (Virtus Core orchestrator).

Each combiner runs a primitive task; earnings aggregate to one ledger.
External micro-task platforms connect via TaskAdapter stubs (API keys required).
"""

from __future__ import annotations

import json
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

    def start_swarm(self, *, workers: int = 10) -> dict[str, Any]:
        state = self._load_state()
        state["running"] = True
        state["workers_target"] = max(1, min(1000, int(workers)))
        state["workers_active"] = state["workers_target"]
        self._save_state(state)
        tick = self.run_tick()
        return {"ok": True, "message": f"Ферма запущена: {state['workers_target']} комбайнов", **tick}

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
            if not meta.get("farm_data_cleaned"):
                tasks.append(("data_clean", row))
            elif not meta.get("classified_niche"):
                tasks.append(("text_classify", row))
            elif not meta.get("farm_verified"):
                tasks.append(("record_verify", row))
        return tasks

    def _run_data_clean(self, row: dict[str, Any]) -> dict[str, Any]:
        meta = dict(row.get("meta") or {})
        issues = meta.get("issues") or meta.get("site_issues") or []
        cleaned = [str(i).strip() for i in issues if str(i).strip()][:12]
        meta["issues"] = cleaned
        meta["farm_data_cleaned"] = True
        meta["farm_cleaned_at"] = datetime.now(timezone.utc).isoformat()
        self._opportunity.update(str(row["id"]), {"meta": meta})
        return {"ok": True, "adapter": "data_clean", "detail": f"Очищено {len(cleaned)} записей"}

    def _run_text_classify(self, row: dict[str, Any]) -> dict[str, Any]:
        meta = dict(row.get("meta") or {})
        analysis = {
            "issues": meta.get("issues") or [],
            "title": meta.get("title") or row.get("company_name"),
            "tech_stack": meta.get("tech_stack") or [],
            "url": row.get("website_url"),
        }
        result = self._ai.classify_niche(
            analysis=analysis,
            company=str(row.get("company_name") or ""),
            url=str(row.get("website_url") or ""),
        )
        meta["classified_niche"] = result.get("niche")
        meta["classified_label"] = result.get("label")
        meta["classified_source"] = result.get("source")
        meta["farm_data_cleaned"] = meta.get("farm_data_cleaned", True)
        self._opportunity.update(str(row["id"]), {"meta": meta})
        llm_cost = 0.001 if result.get("source") == "llm" else 0.0
        return {
            "ok": True,
            "adapter": "text_classify",
            "detail": f"Ниша: {result.get('label')}",
            "llm_cost_eur": llm_cost,
        }

    def _run_record_verify(self, row: dict[str, Any]) -> dict[str, Any]:
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
        return {"ok": ok, "adapter": "record_verify", "detail": detail}

    def run_tick(self, *, workers: int | None = None) -> dict[str, Any]:
        state = self._load_state()
        self._reset_today_if_needed(state)
        batch = workers or (state["workers_active"] if state["running"] else 10)
        batch = max(1, min(200, int(batch)))

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
                workers=batch,
                concurrency=min(batch * 3, 150),
            )
            for lr in swarm.results:
                if not lr.ok:
                    continue
                done += 1
                earned += lr.pay_eur
                llm_cost += lr.llm_cost_eur
                event = {
                    "id": uuid.uuid4().hex[:12],
                    "at": datetime.now(timezone.utc).isoformat(),
                    "adapter": "ai_labeling",
                    "pay_eur": lr.pay_eur,
                    "target": lr.task_id,
                    "detail": lr.detail,
                    "ok": True,
                    "flow": lr.flow,
                }
                self._log_event(event)
                results.append(event)
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
                }
            )

        if done < batch:
            legacy = self._run_legacy_adapters(batch - done)
            done += legacy["tasks_done"]
            earned += legacy["earned_eur"]
            llm_cost += legacy["llm_cost_eur"]
            results.extend(legacy["results"])

        state["total_tasks_done"] = int(state.get("total_tasks_done") or 0) + done
        state["total_earned_eur"] = round(float(state.get("total_earned_eur") or 0) + earned, 4)
        state["today_earned_eur"] = round(float(state.get("today_earned_eur") or 0) + earned, 4)
        state["llm_cost_eur"] = round(float(state.get("llm_cost_eur") or 0) + llm_cost, 4)
        state["last_tick_at"] = datetime.now(timezone.utc).isoformat()
        if state["running"] and not state.get("workers_active"):
            state["workers_active"] = state.get("workers_target", 10)
        self._save_state(state)

        return {
            "ok": True,
            "tasks_done": done,
            "earned_eur": round(earned, 4),
            "llm_cost_eur": round(llm_cost, 4),
            "results": results[:10],
            "message": (
                f"Рой: {done} задач · +{earned:.2f} € (AI-labeling)"
                if done
                else "Нет сырья — нажмите «Запустить ферму» (поиск + разметка)"
            ),
        }

    def _run_legacy_adapters(self, limit: int) -> dict[str, Any]:
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
        for adapter_id, row in tasks:
            runner = runners.get(adapter_id)
            if not runner:
                continue
            try:
                outcome = runner(row)
                pay = _ADAPTER_PAY_EUR.get(adapter_id, 0.01)
                earned += pay
                llm_cost += float(outcome.get("llm_cost_eur") or 0)
                done += 1
                event = {
                    "id": uuid.uuid4().hex[:12],
                    "at": datetime.now(timezone.utc).isoformat(),
                    "adapter": adapter_id,
                    "pay_eur": pay,
                    "target": row.get("company_name") or row.get("website_url"),
                    "detail": outcome.get("detail"),
                    "ok": outcome.get("ok", True),
                }
                self._log_event(event)
                results.append(event)
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

    def dashboard(self, owner_name: str = "Владелец") -> dict[str, Any]:
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
                "detail": "Пакет уходит в swarm_labels_export.jsonl и в базу Genesis.",
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
