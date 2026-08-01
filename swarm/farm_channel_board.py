"""Farm channel board — Earn / Spend / B2B from capability facts (not marketing)."""

from __future__ import annotations

from typing import Any

from swarm.revenue_source_capabilities import audit_sources


def _mode_for(row: dict[str, Any]) -> str | None:
    """Return earn | spend | b2b | None (skip cost-only / local training)."""
    role = str(row.get("role") or "")
    if role in {"cost_provider", "local_training", "local_simulator"}:
        return None
    if row.get("can_earn_via_virtus") is True or role == "payment_processor":
        return "b2b"
    if role in {"requester", "customer_requester"}:
        return "spend"
    if "performer" in role or role in {"worker", "contributor"}:
        return "earn"
    if row.get("registry_only"):
        return "earn"
    if row.get("adapter_implemented"):
        return "spend"
    return "earn"


def _status_on(row: dict[str, Any], mode: str) -> bool:
    if mode == "b2b":
        return bool(row.get("can_earn_via_virtus") and row.get("adapter_implemented"))
    if mode == "spend":
        return bool(row.get("adapter_implemented") and not row.get("registry_only"))
    # earn ON only when Virtus can receive performer payouts
    return bool(row.get("can_earn_via_virtus") is True and "performer" in str(row.get("role") or ""))


def build_farm_channel_board() -> dict[str, Any]:
    """CEO-facing board: which channels earn, spend, or take B2B money — facts only."""
    earn: list[dict[str, Any]] = []
    spend: list[dict[str, Any]] = []
    b2b: list[dict[str, Any]] = []

    for row in audit_sources():
        mode = _mode_for(row)
        if mode is None:
            continue
        on = _status_on(row, mode)
        entry = {
            "id": row["id"],
            "name": row["platform"],
            "role": row.get("role"),
            "mode": mode,
            "status": "on" if on else "off",
            "status_label_ru": "ON" if on else "OFF",
            "adapter_implemented": bool(row.get("adapter_implemented")),
            "can_earn_via_virtus": bool(row.get("can_earn_via_virtus")),
            "note_ru": row.get("note_ru") or "",
        }
        if mode == "earn":
            earn.append(entry)
        elif mode == "spend":
            spend.append(entry)
        else:
            b2b.append(entry)

    earn_on = sum(1 for e in earn if e["status"] == "on")
    spend_wired = sum(1 for e in spend if e["adapter_implemented"])
    b2b_on = sum(1 for e in b2b if e["status"] == "on")

    return {
        "title_ru": "Каналы фермы · Earn / Spend / B2B",
        "rule_ru": (
            "Только факты из кода. Earn ON = Virtus получает выплату исполнителя. "
            "Spend = Virtus платит за разметку (requester). B2B = Stripe Path A."
        ),
        "earn_channels": earn,
        "spend_channels": spend,
        "b2b_channels": b2b,
        "summary": {
            "earn_on_count": earn_on,
            "earn_total": len(earn),
            "spend_wired": spend_wired,
            "spend_total": len(spend),
            "b2b_on_count": b2b_on,
            "performer_path_wired": earn_on > 0,
            "verdict_ru": (
                "Earn-каналы OFF — пути «биржа платит ферме → Withdraw → Stripe» в коде нет. "
                "Toloka/Scale = Spend (requester). Реальный вход денег — B2B Stripe."
                if earn_on == 0
                else "Есть хотя бы один Earn-канал с выплатой в Virtus."
            ),
        },
    }


# Alias for older import name
build_channel_board = build_farm_channel_board


def build_money_truth(
    *,
    real_eur: float,
    spent_eur: float,
    prediction_eur: float,
) -> dict[str, Any]:
    """REAL / SPENT / PREDICTION — never mix forecast into REAL."""
    real = round(float(real_eur or 0), 2)
    spent = round(float(spent_eur or 0), 2)
    prediction = round(float(prediction_eur or 0), 2)
    roi: float | None = None
    roi_label = "—"
    if spent > 0 and real > 0:
        roi = round((real - spent) / spent * 100.0, 1)
        roi_label = f"{roi} %"
    elif spent > 0 and real == 0:
        roi_label = "расход без REAL"
    return {
        "real_eur": real,
        "real_label_ru": f"{real:,.2f} €".replace(",", " ").replace(".", ","),
        "spent_eur": spent,
        "spent_label_ru": f"{spent:,.2f} €".replace(",", " ").replace(".", ","),
        "prediction_eur": prediction,
        "prediction_label_ru": f"{prediction:,.2f} €".replace(",", " ").replace(".", ","),
        "roi_pct": roi,
        "roi_label_ru": roi_label,
        "legend_ru": {
            "real": "Деньги уже получены (Stripe / confirmed)",
            "spent": "Вложено в эксперименты / API / LLM (не прогноз)",
            "prediction": "Модель — не баланс и не кошелёк биржи",
        },
    }
