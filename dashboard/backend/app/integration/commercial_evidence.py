"""Commercial Evidence Report — доказательная таблица цикла Spider → € (RU)."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TOLOKA_MODEL_NOTE_RU = (
    "Toloka Pipeline API v2 — роль requester (заказчик разметки). "
    "Dataset + pipeline run организуют вашу разметку; это не то же самое, что выплата performer за HIT. "
    "Если pipeline succeeded, а wallet = 0 — вопрос не в коде Genesis, а в типе проекта Toloka "
    "(requester vs Human Intelligence Tasks). Уточни в документации или тикете поддержки Toloka."
)


def _status_icon(done: bool | None) -> str:
    if done is True:
        return "✅"
    if done is False:
        return "❌"
    return "⏳"


def build_commercial_evidence(
    *,
    memory_dir: Path,
    farm_state: dict[str, Any],
    toloka_status: dict[str, Any],
    ceo_flags: dict[str, bool] | None = None,
    last_tick: dict[str, Any] | None = None,
    spider_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Таблица доказательств после попытки полного цикла."""
    ceo = ceo_flags or {}
    export_path = memory_dir / "swarm_labels_export.jsonl"
    export_lines = 0
    if export_path.is_file():
        export_lines = sum(1 for ln in export_path.read_text(encoding="utf-8").splitlines() if ln.strip())

    tick = last_tick or {}
    tasks_tick = int(tick.get("tasks_done") or 0)
    earned_tick = float(tick.get("earned_eur") or 0)
    llm_tick = float(tick.get("llm_cost_eur") or 0)
    net_tick = round(earned_tick - llm_tick, 4)

    submitted = int(toloka_status.get("submitted_count") or 0)
    pending = int(toloka_status.get("pending_count") or 0)
    run_status = str(toloka_status.get("last_run_status") or "").lower()
    run_ok = run_status in {"succeeded", "success", "completed"}
    run_failed = run_status in {"failed", "error", "cancelled"}
    submit_ok = submitted > 0 and not toloka_status.get("last_error")
    spider = spider_meta or {}
    spider_ok = bool(spider.get("scanned") or spider.get("passed_gate") or export_lines > 0)

    rows: list[dict[str, Any]] = [
        {
            "step": "Spider",
            "title_ru": "Поиск сырья (Global Spider)",
            "status": _status_icon(True if spider_ok else None if not spider_meta else False),
            "ok": spider_ok,
            "detail": (
                f"скан: {spider.get('scanned', '—')} · в очередь: {spider.get('passed_gate', '—')}"
                if spider_meta
                else f"export строк: {export_lines} (косвенный признак сырья)"
            ),
        },
        {
            "step": "Queue",
            "title_ru": "Очередь",
            "status": _status_icon(export_lines > 0 or pending > 0),
            "ok": export_lines > 0 or pending > 0,
            "detail": f"export.jsonl: {export_lines} · pending submit: {pending}",
        },
        {
            "step": "Workers",
            "title_ru": "Комбайны (разметка)",
            "status": _status_icon(tasks_tick > 0 or int(farm_state.get("total_tasks_done") or 0) > 0),
            "ok": tasks_tick > 0 or int(farm_state.get("total_tasks_done") or 0) > 0,
            "detail": f"последний tick: {tasks_tick} задач · всего: {farm_state.get('total_tasks_done', 0)}",
        },
        {
            "step": "Export",
            "title_ru": "Экспорт разметки",
            "status": _status_icon(export_lines > 0),
            "ok": export_lines > 0,
            "detail": f"swarm_labels_export.jsonl · {export_lines} записей",
        },
        {
            "step": "Submit",
            "title_ru": "Отправка на Toloka",
            "status": _status_icon(submit_ok if submitted else None),
            "ok": submit_ok,
            "detail": f"отправлено: {submitted} · auto: {toloka_status.get('auto_submit_enabled')}",
        },
        {
            "step": "PipelineAccepted",
            "title_ru": "Pipeline принял данные",
            "status": _status_icon(submit_ok),
            "ok": submit_ok,
            "detail": f"dataset: {(toloka_status.get('dataset_id') or '—')[:20]}",
        },
        {
            "step": "PipelineFinished",
            "title_ru": "Pipeline run завершён",
            "status": _status_icon(True if run_ok else False if run_failed else None),
            "ok": run_ok,
            "detail": f"run={toloka_status.get('last_run_id') or '—'} · status={run_status or 'нет'}",
        },
        {
            "step": "WalletChanged",
            "title_ru": "Кошелёк Toloka изменился",
            "status": _status_icon(True if ceo.get("wallet_toloka") else None),
            "ok": bool(ceo.get("wallet_toloka")),
            "detail": "CEO вручную · toloka.ai → Wallet",
            "kind": "manual",
        },
        {
            "step": "WithdrawCompleted",
            "title_ru": "Вывод средств",
            "status": _status_icon(True if ceo.get("withdraw_path") else None),
            "ok": bool(ceo.get("withdraw_path")),
            "detail": "Toloka → Stripe → банк (CEO)",
            "kind": "manual",
        },
    ]

    tech_steps = [r for r in rows if r.get("kind") != "manual"]
    tech_ok = all(r["ok"] for r in tech_steps if r["ok"] is not False) and any(r["ok"] for r in tech_steps)
    commercial_ok = bool(ceo.get("first_euro"))

    if commercial_ok:
        verdict_ru = "Коммерческий результат подтверждён — первый € отмечен CEO."
        verdict_code = "COMMERCIAL_PASS"
    elif run_ok and submit_ok and not ceo.get("wallet_toloka"):
        verdict_ru = (
            "Технический цикл завершён, коммерческий результат не подтверждён. "
            "Pipeline Success ≠ выплата. Проверь тип проекта Toloka (requester vs HIT)."
        )
        verdict_code = "TECH_OK_COMMERCIAL_UNKNOWN"
    elif submit_ok:
        verdict_ru = "Submit выполнен — ждём pipeline run и проверку wallet CEO."
        verdict_code = "SUBMIT_OK"
    elif export_lines > 0:
        verdict_ru = "Разметка есть — submit на Toloka ещё не закрыт."
        verdict_code = "EXPORT_ONLY"
    else:
        verdict_ru = "Цикл не завершён — нет экспорта / submit."
        verdict_code = "INCOMPLETE"

    live = os.getenv("FARM_LIVE_MODE", "").strip().lower() == "live"
    return {
        "title": "Commercial Evidence Report",
        "title_ru": "Отчёт коммерческих доказательств",
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "live_mode": live,
        "toloka_project_model": "requester_pipeline_v2",
        "toloka_model_note_ru": TOLOKA_MODEL_NOTE_RU,
        "rows": rows,
        "tick_economics": {
            "earned_eur": earned_tick,
            "llm_cost_eur": llm_tick,
            "net_eur": net_tick,
            "note_ru": "earned — учебный ledger до подтверждения wallet; llm — реальный расход API",
        },
        "verdict_code": verdict_code,
        "verdict_ru": verdict_ru,
        "technical_cycle_complete": tech_ok and run_ok and submit_ok,
        "commercial_confirmed": commercial_ok,
    }


def save_evidence(memory_dir: Path, report: dict[str, Any]) -> Path:
    memory_dir.mkdir(parents=True, exist_ok=True)
    latest = memory_dir / "commercial_evidence_latest.json"
    latest.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    log_path = memory_dir / "commercial_evidence.jsonl"
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(report, ensure_ascii=False) + "\n")
    return latest


def load_latest_evidence(memory_dir: Path) -> dict[str, Any] | None:
    path = memory_dir / "commercial_evidence_latest.json"
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except (json.JSONDecodeError, OSError):
        return None
