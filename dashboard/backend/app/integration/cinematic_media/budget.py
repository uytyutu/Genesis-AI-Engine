"""Payment gate + media budget enforcement (no auto-spend)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.integration.cinematic_media.config import (
    DEFAULT_PRODUCT_ID,
    get_product,
)
from app.integration.cinematic_media.ledger import MediaBudgetLedger

_PAID_ORDER_STATUSES = frozenset(
    {"paid", "in_production", "ready", "delivered"}
)


def order_is_payment_confirmed(order: dict[str, Any] | None) -> bool:
    """Only webhook/settlement-confirmed payment — not checkout create, not UI success."""
    if not order:
        return False
    if order.get("paid_at"):
        return True
    return str(order.get("status") or "").lower() in _PAID_ORDER_STATUSES


def attach_cinematic_to_order(
    order: dict[str, Any],
    *,
    enabled: bool,
    product_id: str | None = None,
    is_shop: bool = False,
    included_in_package: bool = False,
) -> dict[str, Any]:
    """Mutate order with cinematic commercial fields.

    When ``included_in_package`` (Premium), enable cinematic media without +99 €.
    """
    if not enabled:
        order["cinematic_enabled"] = False
        order["cinematic_product_id"] = None
        order["cinematic_price_eur"] = 0.0
        order["media_budget_eur"] = 0.0
        order["media_spent_eur"] = 0.0
        order["media_remaining_eur"] = 0.0
        order["media_status"] = "NOT_REQUESTED"
        return order

    pid = (product_id or "").strip()
    if not pid:
        base = get_product(DEFAULT_PRODUCT_ID) or {}
        if is_shop and base.get("shop_variant_product_id"):
            pid = str(base["shop_variant_product_id"])
        else:
            pid = DEFAULT_PRODUCT_ID
    product = get_product(pid)
    if not product or str(product.get("status") or "") != "available":
        raise ValueError("cinematic_product_unavailable")

    add_price = float(product.get("price_eur") or 0)
    budget = float(product.get("media_budget_eur") or 0)
    if add_price <= 0 or budget <= 0:
        raise ValueError("cinematic_product_misconfigured")

    charge = 0.0 if included_in_package else add_price
    base_price = float(order.get("price_eur") or 0)
    # Avoid double-adding if called twice
    if not order.get("cinematic_enabled") and charge > 0:
        order["price_eur"] = round(base_price + charge, 2)
        sym = order.get("symbol") or "€"
        order["price_label"] = f"{order['price_eur']:g} {sym}"

    order["cinematic_enabled"] = True
    order["cinematic_product_id"] = product["product_id"]
    order["cinematic_price_eur"] = charge
    order["cinematic_included_in_package"] = bool(included_in_package)
    order["media_budget_eur"] = budget
    order["media_spent_eur"] = float(order.get("media_spent_eur") or 0)
    order["media_remaining_eur"] = round(
        budget - float(order.get("media_spent_eur") or 0), 4
    )
    order["media_status"] = "AWAITING_PAYMENT"
    order["media_provider"] = None
    return order


def activate_media_budget_after_payment(
    order: dict[str, Any],
    memory_dir: Path,
) -> dict[str, Any]:
    """Call only after confirmed payment. Activates internal media budget."""
    if not order.get("cinematic_enabled"):
        return {"ok": True, "activated": False, "reason": "not_requested"}
    if not order_is_payment_confirmed(order):
        return {"ok": False, "activated": False, "error": "payment_not_confirmed"}

    budget = float(order.get("media_budget_eur") or 0)
    spent = float(order.get("media_spent_eur") or 0)
    order["media_remaining_eur"] = round(max(0.0, budget - spent), 4)
    order["media_status"] = "READY_FOR_GENERATION" if order["media_remaining_eur"] > 0 else "BUDGET_EXHAUSTED"
    order["media_budget_activated_at"] = order.get("paid_at")
    ledger = MediaBudgetLedger(memory_dir)
    ledger.record(
        order_id=str(order.get("order_id") or ""),
        op="RESERVE",
        amount_eur=0.0,
        status="budget_activated",
        meta={
            "media_budget_eur": budget,
            "cinematic_price_eur": order.get("cinematic_price_eur"),
            "note": "Client paid add-on; internal budget unlocked. Stripe revenue unchanged by this entry.",
        },
    )
    return {
        "ok": True,
        "activated": True,
        "media_status": order["media_status"],
        "media_budget_eur": budget,
        "media_remaining_eur": order["media_remaining_eur"],
    }


def can_start_media_job(
    order: dict[str, Any] | None,
    *,
    estimated_cost_eur: float | None,
) -> dict[str, Any]:
    """
    Hard gate before any future AI job.
    unknown cost → BLOCK + MANUAL_REVIEW (never treat as €0).
    """
    if not order or not order.get("cinematic_enabled"):
        return {"allow": False, "error": "cinematic_not_enabled", "media_status": "NOT_REQUESTED"}
    if not order_is_payment_confirmed(order):
        return {
            "allow": False,
            "error": "unpaid_order",
            "media_status": str(order.get("media_status") or "AWAITING_PAYMENT"),
            "detail": "AI generation NEVER starts before confirmed payment",
        }
    status = str(order.get("media_status") or "")
    if status in ("AWAITING_PAYMENT", "NOT_REQUESTED"):
        return {"allow": False, "error": "budget_not_activated", "media_status": status}
    if status == "BUDGET_EXHAUSTED":
        return {"allow": False, "error": "budget_exhausted", "media_status": status}

    if estimated_cost_eur is None:
        order["media_status"] = "MANUAL_REVIEW"
        return {
            "allow": False,
            "error": "unknown_cost",
            "media_status": "MANUAL_REVIEW",
            "detail": "Unknown cost must never be treated as 0 €",
        }

    cost = float(estimated_cost_eur)
    if cost < 0:
        return {"allow": False, "error": "invalid_cost", "media_status": status}

    remaining = float(order.get("media_remaining_eur") or 0)
    if cost > remaining + 1e-9:
        order["media_status"] = "BUDGET_EXHAUSTED"
        return {
            "allow": False,
            "error": "budget_exceeded",
            "media_status": "BUDGET_EXHAUSTED",
            "remaining_eur": remaining,
            "requested_eur": cost,
        }
    return {
        "allow": True,
        "media_status": status or "READY_FOR_GENERATION",
        "remaining_eur": remaining,
        "requested_eur": cost,
    }


def apply_media_charge(
    order: dict[str, Any],
    memory_dir: Path,
    *,
    amount_eur: float,
    provider: str,
    job_id: str = "",
    capability: str = "",
) -> dict[str, Any]:
    gate = can_start_media_job(order, estimated_cost_eur=amount_eur)
    if not gate.get("allow"):
        return {"ok": False, **gate}

    amount = round(float(amount_eur), 4)
    ledger = MediaBudgetLedger(memory_dir)
    ledger.record(
        order_id=str(order.get("order_id") or ""),
        op="CHARGE",
        amount_eur=amount,
        provider=provider,
        job_id=job_id,
        capability=capability,
        status="charged",
    )
    spent = float(order.get("media_spent_eur") or 0) + amount
    budget = float(order.get("media_budget_eur") or 0)
    order["media_spent_eur"] = round(spent, 4)
    order["media_remaining_eur"] = round(max(0.0, budget - spent), 4)
    if order["media_remaining_eur"] <= 0:
        order["media_status"] = "BUDGET_EXHAUSTED"
    else:
        order["media_status"] = "GENERATING"
    return {
        "ok": True,
        "media_spent_eur": order["media_spent_eur"],
        "media_remaining_eur": order["media_remaining_eur"],
        "media_status": order["media_status"],
    }


def release_or_refund(
    order: dict[str, Any],
    memory_dir: Path,
    *,
    amount_eur: float,
    op: str = "RELEASE",
    provider: str = "",
    job_id: str = "",
) -> dict[str, Any]:
    amount = round(float(amount_eur), 4)
    if amount <= 0:
        return {"ok": False, "error": "invalid_amount"}
    if op not in ("RELEASE", "REFUND"):
        return {"ok": False, "error": "invalid_op"}
    ledger = MediaBudgetLedger(memory_dir)
    ledger.record(
        order_id=str(order.get("order_id") or ""),
        op=op,  # type: ignore[arg-type]
        amount_eur=amount,
        provider=provider,
        job_id=job_id,
        status="released" if op == "RELEASE" else "refunded",
    )
    spent = max(0.0, float(order.get("media_spent_eur") or 0) - amount)
    budget = float(order.get("media_budget_eur") or 0)
    order["media_spent_eur"] = round(spent, 4)
    order["media_remaining_eur"] = round(max(0.0, budget - spent), 4)
    if order.get("media_status") == "BUDGET_EXHAUSTED" and order["media_remaining_eur"] > 0:
        order["media_status"] = "READY_FOR_GENERATION"
    return {
        "ok": True,
        "media_spent_eur": order["media_spent_eur"],
        "media_remaining_eur": order["media_remaining_eur"],
        "media_status": order.get("media_status"),
    }


def admin_media_view(order: dict[str, Any] | None) -> dict[str, Any]:
    if not order:
        return {"ok": False, "error": "order_not_found"}
    return {
        "ok": True,
        "order_id": order.get("order_id"),
        "cinematic_enabled": bool(order.get("cinematic_enabled")),
        "cinematic_product_id": order.get("cinematic_product_id"),
        "client_paid_cinematic_eur": float(order.get("cinematic_price_eur") or 0),
        "payment_confirmed": order_is_payment_confirmed(order),
        "paid_at": order.get("paid_at"),
        "media_budget_eur": float(order.get("media_budget_eur") or 0),
        "media_spent_eur": float(order.get("media_spent_eur") or 0),
        "media_remaining_eur": float(order.get("media_remaining_eur") or 0),
        "media_status": order.get("media_status") or "NOT_REQUESTED",
        "media_provider": order.get("media_provider"),
        "note": "media_budget is internal; Stripe actual revenue is separate",
    }
