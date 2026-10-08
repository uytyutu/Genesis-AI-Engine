"""Virtus Video AI billing — subscriptions, credit packs, demo + Stripe checkout."""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Any

from app.integration.payment_checkout_service import PaymentCheckoutService
from app.integration.viewora.product import (
    CREDIT_COSTS,
    get_credit_pack,
    get_plan,
)
from app.integration.viewora.store import VieworaStore


def _demo_payment_allowed() -> bool:
    """Ordinary customers may use demo when Stripe not ready (same spirit as Path A)."""
    if os.getenv("GENESIS_VIEWORA_DEMO_PAY", "").strip() == "0":
        return False
    return True


class VieworaBilling:
    def __init__(self, memory_dir: Path) -> None:
        self._store = VieworaStore(memory_dir)
        self._checkout = PaymentCheckoutService(memory_dir)

    def account_snapshot(self, account_id: str | None) -> dict[str, Any]:
        acc = self._store.get_or_create_account(account_id)
        plan = get_plan(str(acc.get("plan_id") or "free")) or get_plan("free")
        return {
            "account": acc,
            "plan": plan,
            "credit_costs": CREDIT_COSTS,
            "payment": {
                "stripe_ready": self._checkout.is_stripe_ready(),
                "public_checkout_ready": self._checkout.is_public_checkout_ready(),
                "demo_payment_available": _demo_payment_allowed(),
                "payment_mode_default": (
                    "stripe"
                    if self._checkout.is_stripe_ready()
                    else "demo"
                    if _demo_payment_allowed()
                    else "unavailable"
                ),
            },
        }

    def can_spend(
        self, account: dict[str, Any], *, action: str, amount: int | None = None
    ) -> tuple[bool, str]:
        cost = amount if amount is not None else int(CREDIT_COSTS.get(action, 1))
        plan_id = str(account.get("plan_id") or "free")
        if plan_id == "free":
            left = int(account.get("free_creations_left") or 0)
            if left < 1:
                return False, "free_limit_reached"
            return True, "ok"
        credits = int(account.get("credits") or 0)
        if credits < cost:
            return False, "insufficient_credits"
        return True, "ok"

    def spend(
        self, account: dict[str, Any], *, action: str, amount: int | None = None
    ) -> dict[str, Any]:
        ok, reason = self.can_spend(account, action=action, amount=amount)
        if not ok:
            raise ValueError(reason)
        cost = amount if amount is not None else int(CREDIT_COSTS.get(action, 1))
        plan_id = str(account.get("plan_id") or "free")
        if plan_id == "free":
            account["free_creations_left"] = max(
                0, int(account.get("free_creations_left") or 0) - 1
            )
        else:
            account["credits"] = max(0, int(account.get("credits") or 0) - cost)
        return self._store.save_account(account)

    def create_order(
        self,
        *,
        account_id: str,
        kind: str,
        sku: str,
        email: str = "",
        success_url: str,
        cancel_url: str,
        prefer_demo: bool = False,
    ) -> dict[str, Any]:
        acc = self._store.get_or_create_account(account_id)
        if email:
            acc["email"] = email.strip().lower()
            self._store.save_account(acc)

        if kind == "plan":
            plan = get_plan(sku)
            if not plan or float(plan.get("monthly_eur") or 0) <= 0:
                return {"ok": False, "reason": "invalid_plan", "http_status": 400}
            amount = float(plan["monthly_eur"])
            label = f"Virtus Video AI {plan['name']} · monthly"
            meta_kind = "viewora_plan"
        elif kind == "credits":
            pack = get_credit_pack(sku)
            if not pack:
                return {"ok": False, "reason": "invalid_pack", "http_status": 400}
            amount = float(pack["eur"])
            label = f"Virtus Video AI Credits · {pack['credits']}"
            meta_kind = "viewora_credits"
        else:
            return {"ok": False, "reason": "invalid_kind", "http_status": 400}

        order = self._store.append_order(
            {
                "account_id": acc["id"],
                "kind": kind,
                "sku": sku,
                "amount_eur": amount,
                "label": label,
                "email": acc.get("email") or email,
                "paid": False,
                "payment_mode": None,
                "meta_kind": meta_kind,
            }
        )

        success_url = (
            (success_url or "")
            .replace("{ORDER}", order["id"])
            .replace("{CHECKOUT_SESSION_ID}", "{CHECKOUT_SESSION_ID}")
        )
        if "order_id=" not in success_url:
            join = "&" if "?" in success_url else "?"
            success_url = f"{success_url}{join}order_id={order['id']}"

        use_demo = prefer_demo or (
            not self._checkout.is_public_checkout_ready() and _demo_payment_allowed()
        )
        if use_demo and _demo_payment_allowed():
            return {
                "ok": True,
                "order_id": order["id"],
                "amount_eur": amount,
                "label": label,
                "provider": "demo",
                "payment_mode": "demo",
                "demo_payment_available": True,
                "checkout_url": f"/viewora/checkout?order_id={order['id']}&mode=demo",
                "account_id": acc["id"],
            }

        try:
            session = self._checkout.create_checkout(
                order_id=order["id"],
                amount_eur=amount,
                label=label,
                success_url=success_url,
                cancel_url=cancel_url,
                currency="eur",
                market_code="DE",
                extra_metadata={
                    "product": "viewora",
                    "kind": kind,
                    "sku": sku,
                    "account_id": str(acc["id"])[:80],
                },
            )
        except ValueError as exc:
            if _demo_payment_allowed():
                return {
                    "ok": True,
                    "order_id": order["id"],
                    "amount_eur": amount,
                    "label": label,
                    "provider": "demo",
                    "payment_mode": "demo",
                    "demo_payment_available": True,
                    "checkout_url": f"/viewora/checkout?order_id={order['id']}&mode=demo",
                    "account_id": acc["id"],
                    "stripe_error": str(exc),
                }
            return {"ok": False, "reason": str(exc), "http_status": 503}

        if session.get("provider") == "sandbox":
            return {
                "ok": True,
                "order_id": order["id"],
                "amount_eur": amount,
                "label": label,
                "provider": "sandbox",
                "payment_mode": "sandbox",
                "checkout_url": f"/viewora/checkout?order_id={order['id']}&mode=sandbox",
                "session_id": session.get("session_id"),
                "account_id": acc["id"],
            }

        return {
            "ok": True,
            "order_id": order["id"],
            "amount_eur": amount,
            "label": label,
            "provider": session.get("provider"),
            "payment_mode": "stripe",
            "checkout_url": session.get("checkout_url"),
            "session_id": session.get("session_id"),
            "account_id": acc["id"],
        }

    def pay_demo(self, order_id: str) -> dict[str, Any]:
        if not _demo_payment_allowed():
            return {"ok": False, "reason": "demo_disabled", "http_status": 403}
        order = self._store.get_order(order_id)
        if not order:
            return {"ok": False, "reason": "order_not_found", "http_status": 404}
        if order.get("paid"):
            return {"ok": True, "already_paid": True, "order": order}
        paid = self._store.mark_order_paid(order_id, payment_mode="demo")
        fulfilled = self._fulfill(paid or order)
        return {
            "ok": True,
            "payment_mode": "demo",
            "order": paid,
            "account": fulfilled,
            "note": "Demo payment — not real revenue (payment_mode=demo)",
        }

    def pay_sandbox(self, order_id: str) -> dict[str, Any]:
        order = self._store.get_order(order_id)
        if not order:
            return {"ok": False, "reason": "order_not_found", "http_status": 404}
        if order.get("paid"):
            return {"ok": True, "already_paid": True, "order": order}
        paid = self._store.mark_order_paid(order_id, payment_mode="sandbox")
        fulfilled = self._fulfill(paid or order)
        return {"ok": True, "payment_mode": "sandbox", "order": paid, "account": fulfilled}

    def fulfill_from_stripe_metadata(self, meta: dict[str, str], order_id: str) -> dict[str, Any]:
        order = self._store.get_order(order_id)
        if not order:
            # Reconstruct minimal order from metadata
            order = self._store.append_order(
                {
                    "id": order_id,
                    "account_id": meta.get("account_id") or f"guest_{uuid.uuid4().hex[:8]}",
                    "kind": meta.get("kind") or "plan",
                    "sku": meta.get("sku") or "",
                    "amount_eur": 0,
                    "label": "Virtus Video AI",
                    "paid": False,
                }
            )
        paid = self._store.mark_order_paid(order_id, payment_mode="stripe")
        return self._fulfill(paid or order)

    def _fulfill(self, order: dict[str, Any]) -> dict[str, Any]:
        acc = self._store.get_or_create_account(str(order.get("account_id") or ""))
        kind = str(order.get("kind") or "")
        sku = str(order.get("sku") or "")
        if kind == "plan":
            plan = get_plan(sku)
            if plan:
                acc["plan_id"] = plan["id"]
                acc["credits"] = int(plan.get("credits") or 0)
                if plan["id"] != "free":
                    acc["free_creations_left"] = 0
        elif kind == "credits":
            pack = get_credit_pack(sku)
            if pack:
                acc["credits"] = int(acc.get("credits") or 0) + int(pack["credits"])
        orders = list(acc.get("orders") or [])
        orders.append(order.get("id"))
        acc["orders"] = orders[-50:]
        return self._store.save_account(acc)

    def order_status(self, order_id: str) -> dict[str, Any] | None:
        order = self._store.get_order(order_id)
        if not order:
            return None
        return {
            **order,
            "demo_payment_available": _demo_payment_allowed() and not order.get("paid"),
        }
