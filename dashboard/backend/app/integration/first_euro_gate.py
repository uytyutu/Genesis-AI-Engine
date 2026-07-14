"""Verified Revenue Engine (VRE) — was first_euro_gate. Commercial proof, not one-off €."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

VRE_TITLE_RU = "Движок проверяемого дохода (Verified Revenue Engine)"
VRE_CORE_QUESTION = (
    "Может ли система воспроизводимо превращать выполненную работу в подтверждённый доход?"
)

MISSION1_FREEZE = {
    "title_ru": "Mission 1 Freeze · Verified Revenue",
    "pr_gate_question_ru": "Помогает получить VRE LEVEL ↑?",
    "pr_gate_rule_ru": "Любой PR / новый код → если «Нет» — не принимается до VRE LEVEL 4",
    "allowed_ru": [
        "Исправление багов",
        "Стабильность",
        "Коммерческие проверки",
        "Отчёты (Evidence, VRE, Finance Guard)",
    ],
    "forbidden_ru": [
        "Новые AI / Brain / агенты",
        "Новые биржи и архитектуры",
        "Масштабирование до VRE LEVEL 4",
    ],
    "until_ru": "Пока VRE LEVEL < 4 — verified revenue engine не доказан",
}

MONETIZATION_CHANNEL_WARNING_RU = (
    "СТОП: Pipeline Success без движения wallet после нескольких run — "
    "это не повод улучшать код. Смените канал монетизации (Toloka requester vs HIT / Scale / B2B)."
)


def _ceo_flags_path(memory_dir: Path) -> Path:
    return memory_dir / "first_euro_ceo_flags.json"


def load_ceo_flags(memory_dir: Path) -> dict[str, bool]:
    path = _ceo_flags_path(memory_dir)
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return {}
        return {str(k): bool(v) for k, v in data.items()}
    except (json.JSONDecodeError, OSError):
        return {}


def save_ceo_flag(memory_dir: Path, step_id: str, *, done: bool) -> dict[str, bool]:
    flags = load_ceo_flags(memory_dir)
    flags[step_id] = done
    path = _ceo_flags_path(memory_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(flags, ensure_ascii=False, indent=2), encoding="utf-8")
    return flags


def build_first_euro_gate(
    *,
    memory_dir: Path,
    toloka_status: dict[str, Any],
    farm_state: dict[str, Any],
    payment_monitor: dict[str, Any] | None = None,
    pipeline_success_count: int = 0,
) -> dict[str, Any]:
    """Verified Revenue Engine checklist — reproducible income proof."""
    ceo = load_ceo_flags(memory_dir)
    labels_export = memory_dir / "swarm_labels_export.jsonl"
    export_lines = 0
    if labels_export.is_file():
        export_lines = sum(1 for ln in labels_export.read_text(encoding="utf-8").splitlines() if ln.strip())

    submitted = int(toloka_status.get("submitted_count") or 0)
    run_status = str(toloka_status.get("last_run_status") or "")
    run_ok = run_status.lower() in {"succeeded", "success", "completed"}
    live = os.getenv("FARM_LIVE_MODE", "").strip().lower() == "live"

    from swarm.revenue_confidence import compute_revenue_confidence, compute_vre_level

    vre = compute_vre_level(
        toloka_status=toloka_status,
        ceo_flags=ceo,
        pipeline_success_count=pipeline_success_count,
    )
    vre_level = int(vre["level"])

    steps: list[dict[str, Any]] = [
        {
            "id": "live_mode",
            "title": "Live-контур включён",
            "detail": "FARM_LIVE_MODE=live · не sandbox",
            "done": live,
            "kind": "auto",
        },
        {
            "id": "toloka_api",
            "title": "Toloka API отвечает",
            "detail": toloka_status.get("message") or "Pipeline v2",
            "done": bool(toloka_status.get("connected")),
            "kind": "auto",
        },
        {
            "id": "labels_produced",
            "title": "Разметка произведена",
            "detail": f"export.jsonl: {export_lines} строк · tick tasks: {farm_state.get('total_tasks_done', 0)}",
            "done": export_lines > 0 or int(farm_state.get("total_tasks_done") or 0) > 0,
            "kind": "auto",
        },
        {
            "id": "toloka_submit",
            "title": "Пакет доставлен на Toloka",
            "detail": f"Отправлено: {submitted} · pending: {toloka_status.get('pending_count', 0)}",
            "done": submitted > 0,
            "kind": "auto",
        },
        {
            "id": "pipeline_run",
            "title": "Pipeline run завершился успешно",
            "detail": (
                f"run {toloka_status.get('last_run_id') or '—'} · status={run_status or 'нет run'}"
            ),
            "done": run_ok,
            "kind": "auto",
        },
        {
            "id": "wallet_toloka",
            "title": "CEO: движение на кошельке Toloka",
            "detail": "toloka.ai → Wallet — вручную проверь баланс/историю после run",
            "done": bool(ceo.get("wallet_toloka")),
            "kind": "manual",
        },
        {
            "id": "withdraw_path",
            "title": "CEO: путь вывода понятен",
            "detail": "Toloka → Stripe → банк (SEPA) — хотя бы один раз прошёл кликами",
            "done": bool(ceo.get("withdraw_path")),
            "kind": "manual",
        },
        {
            "id": "vre_cycle_repeat",
            "title": "CEO: цикл повторился ≥3 раз (VRE LEVEL 4)",
            "detail": "Или auto: ≥3 pipeline success + wallet + withdraw",
            "done": vre_level >= 4,
            "kind": "manual",
        },
    ]

    channel_review = (
        pipeline_success_count >= 3
        and run_ok
        and not ceo.get("wallet_toloka")
        and not ceo.get("vre_cycle_repeat")
    )

    auto_done = sum(1 for s in steps if s["kind"] == "auto" and s["done"])
    auto_total = sum(1 for s in steps if s["kind"] == "auto")
    manual_done = sum(1 for s in steps if s["kind"] == "manual" and s["done"])
    manual_total = sum(1 for s in steps if s["kind"] == "manual")
    all_auto = auto_done == auto_total
    first_euro = bool(ceo.get("first_euro"))

    if vre_level >= 4 or vre.get("engine_proven"):
        verdict = "PASS"
        headline = f"VRE LEVEL 4 — двигатель дохода доказан. Mission 1 Freeze можно снимать."
    elif channel_review:
        verdict = "CHANNEL_REVIEW"
        headline = MONETIZATION_CHANNEL_WARNING_RU
    elif vre_level >= 2:
        verdict = "COMMERCIAL_PROGRESS"
        headline = f"VRE LEVEL {vre_level} — деньги двигаются, проверь повторяемость цикла"
    elif all_auto and manual_done == 0:
        verdict = "COMMERCIAL_GATE"
        headline = "Технический цикл закрыт — проверь wallet Toloka (requester vs HIT?)"
    elif auto_done >= 3 or vre_level >= 1:
        verdict = "IN_PROGRESS"
        headline = f"VRE LEVEL {vre_level} — главный вопрос: платит ли выбранный канал?"
    else:
        verdict = "BLOCKED"
        headline = "Сначала закрой Spider → Queue → Workers → Export → Submit"

    return {
        "engine": "verified_revenue_engine",
        "title_ru": VRE_TITLE_RU,
        "verdict": verdict,
        "headline": headline,
        "core_question": VRE_CORE_QUESTION,
        "vre_level": vre_level,
        "vre": vre,
        "first_euro_confirmed": first_euro,
        "verified_revenue_confirmed": vre_level >= 4,
        "channel_review_required": channel_review,
        "channel_review_message_ru": MONETIZATION_CHANNEL_WARNING_RU if channel_review else None,
        "mission1_freeze": MISSION1_FREEZE,
        "auto_steps_done": auto_done,
        "auto_steps_total": auto_total,
        "manual_steps_done": manual_done,
        "manual_steps_total": manual_total,
        "steps": steps,
        "defer_until_verified_revenue": [
            "Prometheus/Grafana metrics",
            "Гарантированная очередь вместо JSONL",
            "Multi-VPS worker fleet",
            "Appen/MTurk adapters",
            "Новые AI / Brain модули",
        ],
        "ceo_action_now": (
            "СТОП-код · сменить канал монетизации или уточнить Toloka support"
            if channel_review
            else (
                "Не писать код 48ч — toloka.ai: dataset → run → wallet"
                if verdict in {"COMMERCIAL_GATE", "IN_PROGRESS"}
                else "Запустить ферму + feed + дождаться submit"
            )
        ),
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "revenue_confidence": compute_revenue_confidence(
            farm_state=farm_state,
            toloka_status=toloka_status,
            ceo_flags=ceo,
            pay_per_task_eur=float(os.getenv("TOLOKA_EXPECTED_PAY_EUR", "0") or 0),
        ),
    }


def attach_evidence_to_gate(gate: dict[str, Any], evidence: dict[str, Any] | None) -> dict[str, Any]:
    if not evidence:
        return gate
    out = dict(gate)
    out["commercial_evidence"] = evidence
    if evidence.get("verdict_ru"):
        out["evidence_verdict_ru"] = evidence["verdict_ru"]
    return out
