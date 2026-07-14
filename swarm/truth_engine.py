"""Truth Engine v0 — FACT / HYPOTHESIS / CEO_CONFIRMATION / ESTIMATE on program records."""

from __future__ import annotations

from typing import Any

TRUTH_KINDS = ("FACT", "HYPOTHESIS", "CEO_CONFIRMATION", "ESTIMATE")


def truth_record(
    *,
    key: str,
    label_ru: str,
    value: Any,
    kind: str,
    detail_ru: str = "",
) -> dict[str, Any]:
    k = kind if kind in TRUTH_KINDS else "HYPOTHESIS"
    return {
        "key": key,
        "label_ru": label_ru,
        "value": value,
        "truth_kind": k,
        "detail_ru": detail_ru or _default_detail(k),
    }


def _default_detail(kind: str) -> str:
    return {
        "FACT": "Подтверждено системой или API",
        "HYPOTHESIS": "Ожидание — требует проверки",
        "CEO_CONFIRMATION": "Подтверждено CEO вручную",
        "ESTIMATE": "Модель / прогноз — не факт выплаты",
    }.get(kind, "")


def build_truth_sheet(
    *,
    toloka_status: dict[str, Any],
    vre_gate: dict[str, Any],
    finance_guard: dict[str, Any],
    ceo_flags: dict[str, bool],
    error_ledger_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Classify key program signals — reality vs expectation."""
    run_status = str(toloka_status.get("last_run_status") or "").lower()
    run_ok = run_status in {"succeeded", "success", "completed"}
    forecast = (finance_guard or {}).get("forecast") or {}
    confidence = (
        vre_gate.get("revenue_confidence")
        or finance_guard.get("revenue_confidence")
        or {}
    )

    records: list[dict[str, Any]] = [
        truth_record(
            key="pipeline_finished",
            label_ru="Pipeline run завершился",
            value=run_ok,
            kind="FACT" if run_ok else "HYPOTHESIS",
            detail_ru=f"status={run_status or 'нет run'}",
        ),
        truth_record(
            key="toloka_api_connected",
            label_ru="Toloka API отвечает",
            value=bool(toloka_status.get("connected")),
            kind="FACT",
        ),
        truth_record(
            key="labels_submitted",
            label_ru="Пакет отправлен на Toloka",
            value=int(toloka_status.get("submitted_count") or 0),
            kind="FACT" if int(toloka_status.get("submitted_count") or 0) > 0 else "HYPOTHESIS",
        ),
        truth_record(
            key="expected_gross_revenue",
            label_ru="Expected Gross Revenue",
            value=forecast.get("expected_gross_revenue_eur") or forecast.get("expected_income_eur"),
            kind="ESTIMATE",
            detail_ru="Оборот до расходов — не гарантия Toloka",
        ),
        truth_record(
            key="net_profit_forecast",
            label_ru="Прогноз прибыли (net)",
            value=forecast.get("net_profit_forecast_eur"),
            kind="ESTIMATE",
        ),
        truth_record(
            key="revenue_confidence",
            label_ru="Revenue Confidence",
            value=f"{confidence.get('confidence_pct', 0)}%",
            kind="ESTIMATE",
            detail_ru=confidence.get("note_ru", ""),
        ),
        truth_record(
            key="wallet_changed",
            label_ru="Wallet Toloka изменился",
            value=bool(ceo_flags.get("wallet_toloka")),
            kind="CEO_CONFIRMATION" if ceo_flags.get("wallet_toloka") else "HYPOTHESIS",
            detail_ru="toloka.ai → Wallet — только CEO",
        ),
        truth_record(
            key="withdraw_path",
            label_ru="Путь вывода на карту",
            value=bool(ceo_flags.get("withdraw_path")),
            kind="CEO_CONFIRMATION" if ceo_flags.get("withdraw_path") else "HYPOTHESIS",
        ),
        truth_record(
            key="toloka_will_pay",
            label_ru="Toloka должна платить за эту модель",
            value="unknown",
            kind="HYPOTHESIS",
            detail_ru="Requester Pipeline ≠ performer HIT — проверить на platform.toloka.ai",
        ),
        truth_record(
            key="vre_level",
            label_ru="VRE LEVEL",
            value=int(vre_gate.get("vre_level") or 0),
            kind="FACT",
        ),
    ]

    if error_ledger_summary and error_ledger_summary.get("total_logged", 0) > 0:
        records.append(
            truth_record(
                key="exchange_rejects",
                label_ru="Reject биржи залогированы",
                value=error_ledger_summary.get("total_logged"),
                kind="FACT",
                detail_ru=error_ledger_summary.get("hint_ru") or "Error Ledger v0",
            )
        )

    return {
        "title_ru": "Truth Engine v0",
        "subtitle_ru": "FACT = реальность · ESTIMATE/HYPOTHESIS = ожидание · CEO_CONFIRMATION = вы подтвердили",
        "records": records,
        "kinds_ru": {
            "FACT": "Факт — система или API подтвердили",
            "HYPOTHESIS": "Гипотеза — нужна проверка",
            "CEO_CONFIRMATION": "CEO подтвердил вручную",
            "ESTIMATE": "Прогноз / модель — не факт денег",
        },
    }
