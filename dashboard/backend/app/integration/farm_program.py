"""Unified Mission 1 program — VRE, Finance Guard, Evidence, Truth Engine, Force Vectors."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


PIPELINE_STAGES_RU = [
    {"id": "spider", "title": "Spider", "detail_ru": "Поиск URL / задач"},
    {"id": "queue", "title": "Queue", "detail_ru": "Очередь комбайнов"},
    {"id": "workers", "title": "Workers", "detail_ru": "AI-разметка (Groq/Gemini)"},
    {"id": "export", "title": "Export", "detail_ru": "swarm_labels_export.jsonl"},
    {"id": "submit", "title": "Submit", "detail_ru": "Toloka Pipeline v2"},
    {"id": "wallet", "title": "Wallet", "detail_ru": "CEO: движение на Toloka"},
    {"id": "withdraw", "title": "Withdraw", "detail_ru": "CEO: путь вывода"},
    {"id": "repeat", "title": "Repeat ×3", "detail_ru": "VRE LEVEL 4 — воспроизводимость"},
]

CEO_OPERATING_LOOP_RU = [
    "Поиск возможностей",
    "Оценка ROI",
    "Планирование",
    "Выполнение",
    "Контроль качества",
    "Финансы",
    "Отчёт CEO",
]

POST_FIRST_REVENUE_QUESTIONS_RU = [
    "Можно ли повторить этот результат завтра?",
    "Можно ли повторить его десять раз?",
    "Можно ли повторить с другим заказчиком или каналом?",
    "Сохраняется ли положительная экономика?",
]

FORCE_VECTORS_ROADMAP: list[dict[str, Any]] = [
    {
        "id": "truth_engine",
        "order": 0,
        "title_ru": "Truth Engine",
        "subtitle_ru": "FACT vs HYPOTHESIS vs ESTIMATE — не путать реальность и ожидания",
        "phase": "active_v0",
        "unlocked_at_vre": 0,
        "status_ru": "Активен (v0) — в farm_program",
    },
    {
        "id": "decision_memory",
        "order": 1,
        "title_ru": "Decision Memory",
        "subtitle_ru": "Память решений CEO (канал, смена модели) — не диалогов",
        "phase": "roadmap",
        "unlocked_at_vre": 4,
        "status_ru": "После VRE 4 · Toloka→Scale и почему",
    },
    {
        "id": "anti_fragility",
        "order": 2,
        "title_ru": "Anti-Fragility",
        "subtitle_ru": "Error Ledger → taxonomy → block rules (не повторять брак)",
        "phase": "active_v0",
        "unlocked_at_vre": 0,
        "status_ru": "Error Ledger v0 активен",
    },
    {
        "id": "explainability",
        "order": 3,
        "title_ru": "Explainability",
        "subtitle_ru": "Почему CHANNEL_REVIEW / COMMERCIAL_GATE — без LLM",
        "phase": "active_v0",
        "unlocked_at_vre": 0,
        "status_ru": "Активен (v0) — verdict explain",
    },
    {
        "id": "market_radar",
        "order": 4,
        "title_ru": "Market Radar",
        "subtitle_ru": "Карта ROI по биржам — та же работа, выше ставка",
        "phase": "roadmap",
        "unlocked_at_vre": 4,
        "status_ru": "Read-only при CHANNEL_REVIEW · full после VRE 4",
    },
    {
        "id": "multi_channel_revenue",
        "order": 5,
        "title_ru": "Multi-channel Revenue",
        "subtitle_ru": "Scale / MTurk / B2B adapters live",
        "phase": "roadmap",
        "unlocked_at_vre": 4,
        "status_ru": "После доказанной экономики одного канала",
    },
    {
        "id": "digital_ceo",
        "order": 6,
        "title_ru": "Digital CEO",
        "subtitle_ru": "Операционный центр — не чат",
        "phase": "roadmap",
        "unlocked_at_vre": 4,
        "status_ru": "Horizon",
    },
    {
        "id": "business_os",
        "order": 7,
        "title_ru": "Business Operating System",
        "subtitle_ru": "Virtus Core = ОС цифровой компании",
        "phase": "vision",
        "unlocked_at_vre": 4,
        "status_ru": "North star",
    },
]

POST_VRE4_SEQUENCE_RU = [
    "VRE LEVEL 4",
    "Truth Engine (full)",
    "Decision Memory",
    "Anti-Fragility (auto-block)",
    "Market Radar",
    "Multi-channel Revenue",
    "Digital CEO",
    "Business Operating System",
]


def build_revenue_path_map(
    *,
    vre_level: int,
    pipeline_stages: list[dict[str, Any]],
    ceo_flags: dict[str, bool],
) -> dict[str, Any]:
    """Карта пути € до карты CEO — с Truth kinds на каждом шаге."""
    wallet_ok = bool(ceo_flags.get("wallet_toloka"))
    withdraw_ok = bool(ceo_flags.get("withdraw_path"))

    steps = [
        {
            "id": "work",
            "title_ru": "Работа выполнена",
            "path_ru": "Spider → Workers → Export",
            "truth_kind": "FACT",
            "done": any(s.get("done") for s in pipeline_stages if s["id"] in {"workers", "export"}),
            "money_ru": "Пока 0 € на карте",
        },
        {
            "id": "delivered",
            "title_ru": "Пакет на бирже",
            "path_ru": "Submit → Toloka dataset",
            "truth_kind": "FACT",
            "done": any(s.get("done") for s in pipeline_stages if s["id"] == "submit"),
            "money_ru": "Пока 0 € на карте",
        },
        {
            "id": "pipeline",
            "title_ru": "Pipeline Success",
            "path_ru": "Toloka pipeline run",
            "truth_kind": "FACT",
            "done": vre_level >= 1,
            "money_ru": "Pipeline ≠ выплата (HYPOTHESIS до wallet)",
        },
        {
            "id": "wallet",
            "title_ru": "Wallet Toloka",
            "path_ru": "platform.toloka.ai → Wallet",
            "truth_kind": "CEO_CONFIRMATION" if wallet_ok else "HYPOTHESIS",
            "done": wallet_ok,
            "money_ru": "+€ на кошельке Toloka (CEO подтверждает)",
        },
        {
            "id": "withdraw",
            "title_ru": "Вывод",
            "path_ru": "Toloka → Stripe",
            "truth_kind": "CEO_CONFIRMATION" if withdraw_ok else "HYPOTHESIS",
            "done": withdraw_ok,
            "money_ru": "Деньги покидают Toloka",
        },
        {
            "id": "card",
            "title_ru": "Карта CEO",
            "path_ru": "Stripe → SEPA → банк",
            "truth_kind": "CEO_CONFIRMATION" if withdraw_ok and vre_level >= 3 else "HYPOTHESIS",
            "done": withdraw_ok and vre_level >= 3,
            "money_ru": "Реальный доход на счёте",
        },
        {
            "id": "repeat",
            "title_ru": "Повтор ×3",
            "path_ru": "VRE LEVEL 4",
            "truth_kind": "FACT" if vre_level >= 4 else "HYPOTHESIS",
            "done": vre_level >= 4,
            "money_ru": "Двигатель дохода доказан",
        },
    ]
    current = next((s for s in steps if not s["done"]), steps[-1])
    return {
        "title_ru": "Карта пути дохода → ваша карта",
        "diagram_ru": "Работа → Submit → Pipeline → Wallet → Withdraw → Карта → Repeat×3",
        "current_step_ru": current["title_ru"],
        "current_money_note_ru": current["money_ru"],
        "steps": steps,
        "blocker_ru": _revenue_blocker(vre_level, wallet_ok, pipeline_stages),
    }


def _revenue_blocker(vre_level: int, wallet_ok: bool, stages: list[dict[str, Any]]) -> str | None:
    if vre_level >= 4:
        return None
    if vre_level >= 1 and not wallet_ok:
        return "Pipeline OK, wallet = 0 → модель монетизации (requester vs HIT), не код"
    if not any(s.get("done") for s in stages if s["id"] == "submit"):
        return "Нет submit на Toloka — запустите ферму + submit"
    if not any(s.get("done") for s in stages if s["id"] == "export"):
        return "Нет export — workers не произвели разметку"
    return "Конвейер в процессе — см. VRE checklist"


def build_farm_program(
    *,
    vre_gate: dict[str, Any],
    finance_guard: dict[str, Any],
    commercial_evidence: dict[str, Any] | None,
    toloka_status: dict[str, Any],
    farm_state: dict[str, Any],
    labels_export_count: int = 0,
    ceo_flags: dict[str, bool] | None = None,
    error_ledger_summary: dict[str, Any] | None = None,
    commercial_experiments: list[dict[str, Any]] | None = None,
    revenue_replay: dict[str, Any] | None = None,
    production_platform: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Single bundle for CEO / agent audit — Digital Operating System view."""
    from swarm.farm_explainability import explain_vre_verdict
    from swarm.truth_engine import build_truth_sheet

    vre_level = int(vre_gate.get("vre_level") or vre_gate.get("vre", {}).get("level") or 0)
    freeze = vre_gate.get("mission1_freeze") or {}
    forecast = (finance_guard or {}).get("forecast") or {}
    confidence = (
        vre_gate.get("revenue_confidence")
        or finance_guard.get("revenue_confidence")
        or {}
    )
    ceo = ceo_flags or {}

    pipeline_live = {
        "spider": bool(farm_state.get("last_spider_scan") or farm_state.get("running")),
        "queue": int(farm_state.get("workers_target") or 0) > 0,
        "workers": int(farm_state.get("total_tasks_done") or 0) > 0,
        "export": labels_export_count > 0,
        "submit": int(toloka_status.get("submitted_count") or 0) > 0,
        "wallet": bool((vre_gate.get("vre") or {}).get("level", 0) >= 2),
        "withdraw": bool((vre_gate.get("vre") or {}).get("level", 0) >= 3),
        "repeat": vre_level >= 4,
    }

    stages = []
    for stage in PIPELINE_STAGES_RU:
        sid = stage["id"]
        done = pipeline_live.get(sid, False)
        stages.append({**stage, "done": done, "status": "ok" if done else "pending"})

    pr_gate = {
        "question_ru": freeze.get("pr_gate_question_ru", "Помогает получить VRE LEVEL ↑?"),
        "rule_ru": freeze.get("pr_gate_rule_ru", "Нет → PR не принимается до VRE LEVEL 4"),
        "active": vre_level < 4,
    }

    monetization = {
        "channel": "toloka_pipeline_v2",
        "warning_ru": vre_gate.get("channel_review_message_ru"),
        "channel_review_required": bool(vre_gate.get("channel_review_required")),
        "note_ru": (
            "Pipeline Success (requester) ≠ выплата performer. "
            "Wallet=0 после ≥3 run → CHANNEL_REVIEW, не код."
        ),
    }

    force_vectors = _build_force_vectors_view(vre_level=vre_level)

    truth_engine = build_truth_sheet(
        toloka_status=toloka_status,
        vre_gate=vre_gate,
        finance_guard=finance_guard,
        ceo_flags=ceo,
        error_ledger_summary=error_ledger_summary,
    )

    explainability = explain_vre_verdict(
        verdict=str(vre_gate.get("verdict") or ""),
        vre_gate=vre_gate,
        toloka_status=toloka_status,
        error_ledger_summary=error_ledger_summary,
    )

    revenue_path = build_revenue_path_map(
        vre_level=vre_level,
        pipeline_stages=stages,
        ceo_flags=ceo,
    )

    verified_status = "VERIFIED" if vre_level >= 4 else "NOT VERIFIED"

    return {
        "program_id": "mission1_verified_revenue",
        "title_ru": "Genesis · Digital Operating System · Mission 1",
        "subtitle_ru": "ИИ — компонент. Цель — воспроизводимый доход (VRE LEVEL 4).",
        "verified_revenue_status": verified_status,
        "verified_revenue_label_ru": (
            "Verified Revenue · VERIFIED" if verified_status == "VERIFIED" else "Verified Revenue · NOT VERIFIED"
        ),
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "vre_level": vre_level,
        "vre": vre_gate.get("vre"),
        "vre_verdict": vre_gate.get("verdict"),
        "vre_headline": vre_gate.get("headline"),
        "verified_revenue_confirmed": vre_level >= 4,
        "mission1_freeze": freeze,
        "pr_gate": pr_gate,
        "pipeline": {
            "diagram_ru": "Spider → Queue → Workers → Export → Submit → Toloka → Wallet → Withdraw → Repeat×3",
            "stages": stages,
        },
        "revenue_path_map": revenue_path,
        "truth_engine": truth_engine,
        "error_ledger": error_ledger_summary or {"total_logged": 0, "note_ru": "Reject ещё не было"},
        "explainability": explainability,
        "force_vectors": force_vectors,
        "commercial_experiments": commercial_experiments or [],
        "revenue_replay": revenue_replay,
        "production_platform": production_platform,
        "post_vre4_sequence_ru": POST_VRE4_SEQUENCE_RU,
        "finance_guard": {
            "forecast": forecast,
            "revenue_confidence": confidence,
            "negative_streak": finance_guard.get("negative_streak"),
        },
        "commercial_evidence": commercial_evidence,
        "monetization": monetization,
        "ceo_operating_loop_ru": CEO_OPERATING_LOOP_RU,
        "post_first_revenue_questions_ru": POST_FIRST_REVENUE_QUESTIONS_RU,
        "ceo_action_now": vre_gate.get("ceo_action_now"),
        "defer_until_vre_level_4": vre_gate.get("defer_until_verified_revenue", []),
    }


def _build_force_vectors_view(*, vre_level: int) -> dict[str, Any]:
    vectors = []
    for v in FORCE_VECTORS_ROADMAP:
        unlocked = vre_level >= int(v.get("unlocked_at_vre") or 0)
        item = dict(v)
        item["unlocked"] = unlocked or v.get("phase") == "active_v0"
        item["locked_reason_ru"] = None if item["unlocked"] else f"Откроется после VRE LEVEL {v.get('unlocked_at_vre')}"
        vectors.append(item)
    return {
        "title_ru": "Force Vectors · Roadmap",
        "note_ru": "Read-only. Не генерация — фокус силы конвейера. v0 активен без нарушения Freeze.",
        "vectors": vectors,
    }


def error_ledger_from_memory(memory_dir: Path) -> dict[str, Any]:
    from swarm.farm_error_ledger import FarmErrorLedger

    return FarmErrorLedger(memory_dir).summary()


def attach_program_to_dashboard(
    dashboard: dict[str, Any],
    *,
    program_builder: Callable[..., dict[str, Any]] | None = None,
    memory_dir: Path | None = None,
    ceo_flags: dict[str, bool] | None = None,
) -> dict[str, Any]:
    builder = program_builder or build_farm_program
    err = error_ledger_from_memory(memory_dir) if memory_dir else None
    out = dict(dashboard)
    out["farm_program"] = builder(
        vre_gate=dashboard.get("first_euro_gate") or dashboard.get("verified_revenue_engine") or {},
        finance_guard=dashboard.get("finance_guard") or {},
        commercial_evidence=dashboard.get("commercial_evidence"),
        toloka_status=dashboard.get("toloka_submit") or {},
        farm_state={
            "running": dashboard.get("running"),
            "workers_target": dashboard.get("workers_target"),
            "total_tasks_done": dashboard.get("total_tasks_done"),
            "last_spider_scan": (dashboard.get("global_spider") or {}).get("last_scan"),
        },
        labels_export_count=int(dashboard.get("labels_export_count") or 0),
        ceo_flags=ceo_flags,
        error_ledger_summary=err,
    )
    return out
