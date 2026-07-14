"""Revenue Confidence — насколько прогноз gross revenue соответствует реальности."""

from __future__ import annotations

import os
from typing import Any


def compute_revenue_confidence(
    *,
    farm_state: dict[str, Any],
    toloka_status: dict[str, Any],
    ceo_flags: dict[str, bool],
    pay_per_task_eur: float,
) -> dict[str, Any]:
    """Score 0–100 + human label. Не путать с вероятностью выплаты — это качество данных прогноза."""
    score = 0
    factors: list[str] = []

    live = os.getenv("FARM_LIVE_MODE", "").strip().lower() == "live"
    if live:
        score += 8
        factors.append("live mode")
    else:
        factors.append("sandbox снижает уверенность")

    if toloka_status.get("connected"):
        score += 12
        factors.append("Toloka API OK")
    if int(toloka_status.get("submitted_count") or 0) > 0:
        score += 15
        factors.append("submit был")
    run_ok = str(toloka_status.get("last_run_status") or "").lower() in {
        "succeeded",
        "success",
        "completed",
    }
    if run_ok:
        score += 18
        factors.append("pipeline succeeded")
    if pay_per_task_eur > 0:
        score += 15
        factors.append("TOLOKA_EXPECTED_PAY_EUR задан")
    else:
        factors.append("нет ставки Toloka — прогноз = ledger")

    if ceo_flags.get("wallet_toloka"):
        score += 22
        factors.append("CEO подтвердил wallet")
    if ceo_flags.get("withdraw_path"):
        score += 10
        factors.append("CEO подтвердил вывод")

    psc = int(toloka_status.get("pipeline_success_count") or 0)
    if psc >= 3:
        score += 10
        factors.append("≥3 успешных pipeline")

    score = max(0, min(100, score))

    if score >= 75:
        band = "high"
        label_ru = "Высокая — есть CEO + pipeline"
    elif score >= 40:
        band = "medium"
        label_ru = "Средняя — техника OK, деньги не подтверждены"
    else:
        band = "low"
        label_ru = "Низкая — прогноз гипотетический"

    return {
        "confidence_pct": score,
        "confidence_band": band,
        "label_ru": label_ru,
        "factors": factors,
        "note_ru": "Confidence = качество данных прогноза, не гарантия выплаты",
    }


def compute_vre_level(
    *,
    toloka_status: dict[str, Any],
    ceo_flags: dict[str, bool],
    pipeline_success_count: int,
) -> dict[str, Any]:
    run_ok = str(toloka_status.get("last_run_status") or "").lower() in {
        "succeeded",
        "success",
        "completed",
    }
    psc = max(pipeline_success_count, int(toloka_status.get("pipeline_success_count") or 0))
    wallet = bool(ceo_flags.get("wallet_toloka"))
    withdraw = bool(ceo_flags.get("withdraw_path"))
    repeat = bool(ceo_flags.get("vre_cycle_repeat")) or (
        psc >= 3 and wallet and withdraw
    )

    level = 0
    if run_ok or psc >= 1:
        level = 1
    if wallet:
        level = 2
    if withdraw:
        level = 3
    if repeat:
        level = 4

    levels_ru = {
        0: "LEVEL 0 — нет проверки",
        1: "LEVEL 1 — успешный pipeline",
        2: "LEVEL 2 — wallet изменился (CEO)",
        3: "LEVEL 3 — вывод средств (CEO)",
        4: "LEVEL 4 — цикл повторился ≥3 раз · двигатель дохода",
    }

    engine_proven = level >= 4

    return {
        "level": level,
        "level_label_ru": levels_ru.get(level, levels_ru[0]),
        "engine_proven": engine_proven,
        "pipeline_success_count": psc,
        "requirements": [
            {"level": 1, "need_ru": "Pipeline run succeeded"},
            {"level": 2, "need_ru": "CEO: wallet_toloka"},
            {"level": 3, "need_ru": "CEO: withdraw_path"},
            {"level": 4, "need_ru": "≥3 pipeline success + wallet + withdraw (или CEO vre_cycle_repeat)"},
        ],
    }
