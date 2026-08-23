"""RapidAPI revenue events — only PAID_OUT Hard REAL reaches FinanceLedger."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from swarm.farm_channels.rapidapi import SOURCE_ID
from swarm.farm_channels.rapidapi.models import (
    REV_EARNED,
    REV_ESTIMATED,
    REV_PAID_OUT,
    REV_PAYOUT_PENDING,
    REV_POTENTIAL,
)
from swarm.farm_channels.rapidapi.store import ApiFarmStore

# RapidAPI marketplace fee (docs: 25% on rapidapi.com)
DEFAULT_MARKETPLACE_FEE_RATE = 0.25


def normalize_revenue_event(payload: dict[str, Any]) -> dict[str, Any]:
    gross = round(float(payload.get("gross_amount") or payload.get("amount") or 0), 4)
    fee_rate = float(payload.get("fee_rate") or DEFAULT_MARKETPLACE_FEE_RATE)
    if payload.get("platform_fee") is not None:
        fee = round(float(payload["platform_fee"]), 4)
    else:
        fee = round(gross * fee_rate, 4)
    net = payload.get("net_amount")
    if net is None:
        net = round(gross - fee, 4)
    else:
        net = round(float(net), 4)
    status = str(payload.get("status") or REV_ESTIMATED).upper()
    if status in ("POTENTIAL",):
        status = REV_POTENTIAL
    elif status in ("ESTIMATED", "ESTIMATE"):
        status = REV_ESTIMATED
    elif status in ("EARNED", "GROSS"):
        status = REV_EARNED
    elif status in ("PAYOUT_PENDING", "PENDING"):
        status = REV_PAYOUT_PENDING
    elif status in ("PAID_OUT", "PAID", "SETTLED"):
        status = REV_PAID_OUT
    return {
        "id": str(payload.get("id") or uuid.uuid4().hex[:16]),
        "provider": SOURCE_ID,
        "external_id": str(payload.get("external_id") or "").strip(),
        "api_id": str(payload.get("api_id") or payload.get("candidate_id") or ""),
        "gross_amount": gross,
        "platform_fee": fee,
        "net_amount": net,
        "currency": str(payload.get("currency") or "USD").upper(),
        "status": status,
        "occurred_at": payload.get("occurred_at")
        or datetime.now(timezone.utc).isoformat(),
        "settled_at": payload.get("settled_at"),
        "payout_id": str(payload.get("payout_id") or ""),
        "evidence": payload.get("evidence") or {},
        "demo": bool(payload.get("demo")),
    }


def ingest_revenue_event(
    store: ApiFarmStore,
    payload: dict[str, Any],
    *,
    memory_dir=None,
) -> dict[str, Any]:
    """Idempotent ingest. PAID_OUT with Hard REAL fields → FinanceLedger."""
    event = normalize_revenue_event(payload)
    if event.get("demo"):
        event["status"] = REV_ESTIMATED
        event["evidence"] = {**(event.get("evidence") or {}), "marker": "DEMO / SIMULATED"}

    if not event.get("external_id"):
        return {"ok": False, "error": "external_id_required", "event": event}

    existing = store.get_revenue_by_external_id(event["external_id"])
    if existing:
        return {
            "ok": True,
            "duplicate": True,
            "event": existing,
            "ledger_appended": bool(existing.get("ledger_uuid")),
        }

    ledger_uuid = None
    if event["status"] == REV_PAID_OUT and not event.get("demo"):
        ledger_uuid = _try_append_ledger(event, memory_dir=memory_dir or store.memory_dir)
        event["ledger_uuid"] = ledger_uuid

    saved = store.append_revenue_event(event)
    return {
        "ok": True,
        "duplicate": False,
        "event": saved,
        "ledger_appended": bool(ledger_uuid),
        "actual_revenue_increased": bool(ledger_uuid),
    }


def _try_append_ledger(event: dict[str, Any], *, memory_dir) -> str | None:
    from pathlib import Path

    from swarm.finance_ledger import FinanceLedger
    from swarm.finance_reality_law import is_real_money_event
    from swarm.revenue_source import CONFIDENCE_WITHDRAWN

    paid_at = event.get("settled_at") or event.get("occurred_at")
    payout_id = event.get("payout_id") or event.get("external_id")
    passport = {
        "external_payout_id": payout_id,
        "amount": event.get("net_amount"),
        "currency": event.get("currency"),
        "paid_at": paid_at,
        "source_id": SOURCE_ID,
    }
    if not is_real_money_event(passport):
        return None
    ledger = FinanceLedger(Path(memory_dir))
    row = ledger.append(
        source_id=SOURCE_ID,
        amount=float(event["net_amount"]),
        currency=str(event["currency"]),
        description=f"RapidAPI payout {payout_id}",
        confidence=CONFIDENCE_WITHDRAWN,
        payout_id=str(payout_id),
        settlement_date=str(paid_at)[:10] if paid_at else None,
        proof_url=str((event.get("evidence") or {}).get("proof_url") or ""),
        status="paid_out",
    )
    return str(row.get("uuid") or "")


def revenue_summary(store: ApiFarmStore) -> dict[str, Any]:
    from swarm.farm_channels.rapidapi.lifecycle import theoretical_mrr_scenario

    events = store.list_revenue_events(limit=10_000)
    gross = fee = net_earned = pending = paid = 0.0
    potential = 0.0
    paid_subscribers = 0
    for e in events:
        if e.get("demo"):
            continue
        st = str(e.get("status") or "")
        g = float(e.get("gross_amount") or 0)
        f = float(e.get("platform_fee") or 0)
        n = float(e.get("net_amount") or 0)
        if st in (REV_POTENTIAL, REV_ESTIMATED):
            # Keep estimate events for audit only — never surface as MRR/pipeline hero.
            potential += n
            continue
        if st in (REV_EARNED, REV_PAYOUT_PENDING, REV_PAID_OUT):
            gross += g
            fee += f
        if st == REV_EARNED:
            net_earned += n
        elif st == REV_PAYOUT_PENDING:
            pending += n
            net_earned += n
        elif st == REV_PAID_OUT:
            paid += n
            net_earned += n

    for row in store.list_candidates():
        m = row.get("metrics") or {}
        if m.get("self_test_only") or m.get("provider_self_test"):
            continue
        paid_subscribers += int(m.get("paid_subscribers") or 0)

    # Never sum list prices of unpublished APIs into revenue/pipeline.
    pro_prices = []
    for row in store.list_candidates():
        if not str(row.get("rapidapi_api_id") or "").strip():
            continue
        pkg = row.get("publish_package") or {}
        pricing = pkg.get("pricing") or row.get("suggested_price") or {}
        try:
            pro_prices.append(float(pricing.get("PRO") or 0))
        except (TypeError, ValueError):
            continue
    primary_pro = pro_prices[0] if pro_prices else 0.0
    mrr = theoretical_mrr_scenario(pro_price=primary_pro, paid_subscribers=paid_subscribers)

    return {
        "provider": SOURCE_ID,
        "payout_channel": "RapidAPI → PayPal",
        "gross_revenue": round(gross, 4),
        "marketplace_fee": round(fee, 4),
        "net_earned": round(net_earned, 4),
        "pending_payout": round(pending, 4),
        "paid_out": round(paid, 4),
        "actual_revenue": round(paid, 4),  # only confirmed payouts
        "real_mrr": mrr["real_mrr"],
        "theoretical_mrr": mrr["theoretical_mrr"],
        "scenario_mrr_at_n": mrr["scenario_mrr_at_n"],
        "scenario_n": mrr["scenario_n"],
        "paid_subscribers": paid_subscribers,
        "potential_not_real": round(potential, 4),
        "list_price_sum_not_revenue": round(sum(pro_prices), 2),
        "event_count": len(events),
        "rule_ru": (
            "Actual Revenue / REAL MRR = только PAID_OUT / paid subscribers. "
            "List-price sum и scenario_mrr_at_n — НЕ pipeline и НЕ деньги. "
            "Potential/Estimated events не деньги."
        ),
    }
