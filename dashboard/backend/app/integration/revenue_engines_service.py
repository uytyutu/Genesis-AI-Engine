"""Three revenue engines — B2B · Micro-services · Experiments lab.

Engine 3 (lab) is NEVER profit. Confirmed € promotes ideas to Engine 1 or 2.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ENGINE_B2B = "engine_1_b2b"
ENGINE_MICRO = "engine_2_microservices"
ENGINE_LAB = "engine_3_experiments"

_STATUS_ACTIVE = "active"
_STATUS_PROMOTED = "promoted"
_STATUS_FAILED = "failed"
_STATUS_DISABLED = "disabled"
_STATUS_RESEARCH = "research"

# Lab channels — farm / exchange / probes (never CEO profit)
_LAB_CHANNELS = frozenset(
    {
        "toloka_requester",
        "scale_ai",
        "farm_labeling",
        "global_spider",
        "experiment",
    }
)

_MICRO_CHANNELS = frozenset(
    {
        "ssl_monitor",
        "seo_report",
        "competitor_report",
        "micro_saas",
    }
)


def _format_eur(amount: float) -> str:
    return f"{amount:,.2f} €".replace(",", " ").replace(".", ",")


def _engine_defs() -> list[dict[str, Any]]:
    return [
        {
            "id": ENGINE_B2B,
            "number": 1,
            "label_ru": "B2B",
            "subtitle_ru": "Крупные сделки · лиды → Outbox → Stripe",
            "counts_as_profit": True,
            "wallet_ru": "Ваш Stripe → банк (SEPA)",
            "promotion_ru": "Подтверждённая оплата клиента через checkout/webhook",
        },
        {
            "id": ENGINE_MICRO,
            "number": 2,
            "label_ru": "Микросервисы",
            "subtitle_ru": "Подписки · SSL / SEO / мониторинг",
            "counts_as_profit": True,
            "wallet_ru": "Ваш Stripe → банк (recurring)",
            "promotion_ru": "Из лаборатории — когда есть повторяющийся €",
        },
        {
            "id": ENGINE_LAB,
            "number": 3,
            "label_ru": "Эксперименты",
            "subtitle_ru": "Лаборатория · поиск новых каналов",
            "counts_as_profit": False,
            "wallet_ru": "Не прибыль — только журнал и статистика",
            "promotion_ru": "0 € подтверждённых → auto disabled",
        },
    ]


def _confirmed_eur_by_channel(settlements: list[dict[str, Any]]) -> dict[str, float]:
    totals: dict[str, float] = {}
    for row in settlements:
        amount = round(float(row.get("amount_eur") or 0), 2)
        if amount <= 0:
            continue
        channel = str(row.get("channel") or row.get("label") or "b2b").lower()
        if "ssl" in channel or "seo" in channel or "monitor" in channel:
            key = "micro_saas"
        else:
            key = "direct_b2b"
        totals[key] = round(totals.get(key, 0) + amount, 2)
    return totals


def _evaluate_experiment(
    channel: str,
    *,
    confirmed_eur: float,
    outcome_code: str,
) -> dict[str, str]:
    if channel in _LAB_CHANNELS or channel not in _MICRO_CHANNELS and channel != "direct_b2b":
        if confirmed_eur >= 0.01:
            return {
                "status": _STATUS_PROMOTED,
                "status_ru": "Продвинут — есть подтверждённый €",
                "action_ru": "Перенести в двигатель 1 или 2",
            }
        if outcome_code in ("FAILED", "DISABLED"):
            return {
                "status": _STATUS_DISABLED,
                "status_ru": "Отключён — 0 €",
                "action_ru": "Не тратить время CEO",
            }
        if outcome_code == "PENDING":
            return {
                "status": _STATUS_RESEARCH,
                "status_ru": "Исследование",
                "action_ru": "Собрать факты, не считать прибылью",
            }
        return {
            "status": _STATUS_FAILED,
            "status_ru": "Не сработал — 0 € подтверждённых",
            "action_ru": "Авто-отключение · только лаборатория",
        }
    if confirmed_eur >= 0.01:
        return {
            "status": _STATUS_ACTIVE,
            "status_ru": "Активный — € подтверждены",
            "action_ru": "Масштабировать канал",
        }
    return {
        "status": _STATUS_RESEARCH,
        "status_ru": "Ожидает первую оплату",
        "action_ru": "Продолжить CEO-путь",
    }


def build_revenue_engines(
    *,
    memory_dir: Path,
    finance_snapshot: dict[str, Any],
    settlements: list[dict[str, Any]] | None = None,
    farm_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """CEO map: three engines + money routes to Stripe wallet."""
    from app.integration.commercial_experiment_journal import ensure_baseline_experiments, list_experiments

    ensure_baseline_experiments(memory_dir)
    settles = settlements or []
    farm = farm_state or {}
    confirmed_by_channel = _confirmed_eur_by_channel(settles)

    b2b_eur = round(float(finance_snapshot.get("paid_by_client_eur") or 0), 2)
    micro_eur = round(confirmed_by_channel.get("micro_saas", 0), 2)
    available = round(float(finance_snapshot.get("available_for_withdrawal_eur") or 0), 2)
    pending = round(float(finance_snapshot.get("pending_settlement_eur") or 0), 2)
    farm_journal = round(float(farm.get("total_earned_eur") or 0), 2)

    experiments_raw = list_experiments(memory_dir, limit=20)
    experiments: list[dict[str, Any]] = []
    for row in experiments_raw:
        ch = str(row.get("channel") or "")
        confirmed = confirmed_by_channel.get(ch, 0.0)
        ev = _evaluate_experiment(ch, confirmed_eur=confirmed, outcome_code=str(row.get("outcome_code") or ""))
        engine_id = ENGINE_LAB
        if ch == "direct_b2b":
            engine_id = ENGINE_B2B
        elif ch in _MICRO_CHANNELS:
            engine_id = ENGINE_MICRO
        experiments.append(
            {
                **row,
                "engine_id": engine_id,
                "confirmed_eur": confirmed,
                "confirmed_label_ru": _format_eur(confirmed),
                **ev,
            }
        )

    engines = []
    for spec in _engine_defs():
        eid = spec["id"]
        if eid == ENGINE_B2B:
            metrics = {
                "confirmed_eur": b2b_eur,
                "confirmed_label_ru": _format_eur(b2b_eur),
                "available_eur": available,
                "pending_settlement_eur": pending,
            }
        elif eid == ENGINE_MICRO:
            metrics = {
                "confirmed_eur": micro_eur,
                "confirmed_label_ru": _format_eur(micro_eur),
                "available_eur": 0.0,
                "pending_settlement_eur": 0.0,
            }
        else:
            metrics = {
                "confirmed_eur": 0.0,
                "confirmed_label_ru": "0,00 €",
                "lab_journal_eur": farm_journal,
                "lab_journal_label_ru": _format_eur(farm_journal),
            }
        engines.append({**spec, **metrics})

    return {
        "title_ru": "Три двигателя дохода",
        "subtitle_ru": "Прибыль = только двигатели 1–2 · Лаборатория никогда не смешивается",
        "engines": engines,
        "experiments": experiments,
        "money_route_ru": (
            "Клиент (B2B checkout) → Stripe → webhook → finance_settlements.jsonl → "
            "«Оплачено клиентом» → 3 раб. дня DE → «Доступно к выводу» → ваш банк. "
            "Ферма/Toloka: биржевой кошелёк → Withdraw на Stripe → банк (отдельно, не в Hero)."
        ),
        "lab_rule_ru": (
            "Двигатель 3: любая идея → эксперiment → если ≥0,01 € подтверждены Stripe/webhook → "
            "продвижение в №1 или №2; иначе status=disabled."
        ),
        "stripe_operational_note_ru": (
            "Hero и /finance показывают только confirmed из settlements — не журнал фермы."
        ),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
