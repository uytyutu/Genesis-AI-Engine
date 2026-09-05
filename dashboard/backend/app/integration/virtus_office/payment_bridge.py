"""CC-2 — Office Job → Core Order → Stripe Checkout bridge.

Reuses SalesOrderService + RevenuePipelineService + PaymentCheckoutService.
No parallel payment stack. OFFICE_PIPELINE_LIVE stays False until Commercial DoD.
"""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Any

from app.integration.virtus_office.job_engine import OfficeJobError
from app.integration.virtus_office.office_job_ssot import OFFICE_PRICE_MATRIX_EUR
from app.integration.virtus_office.understanding import ACTION_CATALOG, _price_for

logger = logging.getLogger("virtus.office.payment")

# price_key → Core package_id (registered in sales_order_service._PACKAGES)
PRICE_KEY_TO_PACKAGE: dict[str, str] = {
    "simple_op": "office_simple_op",
    "doc_quality": "office_doc_quality",
    "translate": "office_translate",
    "document": "office_document",
    "cv_bewerbung": "office_cv_bewerbung",
    "excel_calc": "office_excel_calc",
    "doc_analysis": "office_doc_analysis",
    "large_pack": "office_large_pack",
    "complex_from": "office_complex_from",
}

OFFICE_PACKAGE_IDS: frozenset[str] = frozenset(PRICE_KEY_TO_PACKAGE.values())


def is_office_order(order: dict[str, Any] | None) -> bool:
    if not isinstance(order, dict):
        return False
    pkg = str(order.get("package_id") or "").strip().lower()
    kind = str(order.get("product_kind") or "").strip().lower()
    return kind == "office" or pkg.startswith("office_") or bool(order.get("office_job_id"))


def package_id_for_action(action_id: str) -> str:
    action = next((a for a in ACTION_CATALOG if a["id"] == action_id), None)
    price_key = str((action or {}).get("price_key") or "document")
    return PRICE_KEY_TO_PACKAGE.get(price_key, "office_document")


def commercial_snapshot(job: dict[str, Any]) -> dict[str, Any]:
    """Immutable commercial parameters used for price lock + tamper checks."""
    understanding = dict(job.get("understanding") or {})
    intent = dict(understanding.get("intent") or {})
    proposal = dict(job.get("proposal") or {})
    action_id = str(intent.get("id") or proposal.get("task") or "").strip()
    price = proposal.get("price_eur")
    if price is None:
        price = intent.get("price_eur")
    if price is None and action_id:
        price = _price_for(action_id)
    pages = None
    detected = proposal.get("detected") if isinstance(proposal.get("detected"), dict) else {}
    if detected.get("pages") is not None:
        pages = detected.get("pages")
    elif understanding.get("page_count") is not None:
        pages = understanding.get("page_count")
    elif job.get("ingest") and isinstance(job["ingest"], dict):
        pages = job["ingest"].get("page_count")

    return {
        "job_id": str(job.get("job_id") or ""),
        "action_id": action_id,
        "source_language": str(
            intent.get("detected_source_language")
            or intent.get("source_language")
            or understanding.get("language")
            or "auto"
        ),
        "target_language": str(intent.get("target_language") or proposal.get("target_language") or "")
        or None,
        "output_format": str(
            intent.get("output_format") or proposal.get("result_format") or "pdf"
        ),
        "filename": str(job.get("filename") or ""),
        "file_kind": str(job.get("file_kind") or ""),
        "page_count": pages,
        "price_eur": round(float(price or 0), 2),
        "currency": "EUR",
    }


def lock_hash(snapshot: dict[str, Any]) -> str:
    payload = json.dumps(snapshot, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_price_lock(job: dict[str, Any], *, locked_at: str) -> dict[str, Any]:
    snap = commercial_snapshot(job)
    if not snap["action_id"]:
        raise OfficeJobError("action_required", "Bitte zuerst eine Aktion wählen")
    if snap["price_eur"] <= 0:
        raise OfficeJobError("invalid_price", "Preis fehlt")
    # Canonical matrix must match proposal (forged price rejection)
    expected = round(float(_price_for(snap["action_id"])), 2)
    if abs(snap["price_eur"] - expected) > 0.01:
        raise OfficeJobError(
            "price_mismatch",
            f"Preis stimmt nicht mit Matrix überein ({snap['price_eur']} ≠ {expected})",
        )
    return {
        **snap,
        "price_locked_at": locked_at,
        "lock_hash": lock_hash(snap),
        "package_id": package_id_for_action(snap["action_id"]),
    }


def assert_price_lock_intact(job: dict[str, Any]) -> None:
    payment = dict(job.get("payment") or {})
    lock = payment.get("price_lock")
    if not isinstance(lock, dict) or not lock.get("lock_hash"):
        raise OfficeJobError("price_lock_missing", "Preis-Sperre fehlt")
    current = commercial_snapshot(job)
    # Compare commercial fields only (ignore locked_at / package_id extras on lock)
    expected_hash = str(lock.get("lock_hash") or "")
    if lock_hash(current) != expected_hash:
        raise OfficeJobError(
            "price_lock_tampered",
            "Preis oder Parameter nach Sperre geändert — abgelehnt",
        )
    locked_price = round(float(lock.get("price_eur") or 0), 2)
    if abs(current["price_eur"] - locked_price) > 0.01:
        raise OfficeJobError("price_mismatch", "Gesperrter Preis stimmt nicht")


def payment_gate_blocks_execute(job: dict[str, Any]) -> bool:
    """CRA honesty: final execution always requires confirmed payment.

    Preview may exist on the proposal; unpaid jobs never produce a final artifact.
    """
    payment = dict(job.get("payment") or {})
    return not bool(payment.get("paid"))


def mark_payment_outcome(
    engine: Any,
    job_id: str,
    *,
    owner_token: str,
    outcome: str,
) -> dict[str, Any]:
    """Test / webhook helper: failed|cancelled keep execute locked."""
    job = engine._require_owner(job_id, owner_token)
    payment = dict(job.get("payment") or {})
    if not payment.get("price_lock") and not payment.get("requires_payment"):
        raise OfficeJobError("not_locked", "Keine Preis-Sperre")
    if payment.get("paid"):
        raise OfficeJobError("already_paid", "Bereits bezahlt")
    status = str(outcome or "").strip().lower()
    if status not in {"failed", "cancelled", "expired"}:
        raise OfficeJobError("invalid_outcome", "outcome muss failed|cancelled|expired sein")
    payment["status"] = status
    payment["paid"] = False
    job["payment"] = payment
    job["status"] = "awaiting_payment"
    from app.integration.virtus_office.job_engine import _utc_now

    job["updated_at"] = _utc_now()
    engine._write(job)
    return engine.public_view(job)


def build_checkout_services(memory_dir: Path) -> tuple[Any, Any]:
    """Lightweight Core stack bound to the same memory_dir as Office jobs."""
    from app.factory.factory_service import FactoryService
    from app.integration.factory_intent_service import FactoryIntentService
    from app.integration.finance_service import FinanceService
    from app.integration.owner_notification_service import OwnerNotificationService
    from app.integration.payment_checkout_service import PaymentCheckoutService
    from app.integration.revenue_pipeline_service import RevenuePipelineService
    from app.integration.sales_order_service import SalesOrderService

    factory = FactoryService(memory_dir)
    intent = FactoryIntentService(memory_dir, factory)
    sales = SalesOrderService(memory_dir, intent)
    checkout = PaymentCheckoutService(memory_dir)
    finance = FinanceService(memory_dir)
    notifications = OwnerNotificationService(memory_dir)
    revenue = RevenuePipelineService(
        sales, finance, checkout, notifications, work_farm=None
    )
    return sales, revenue


def lock_and_begin_checkout(
    engine: Any,
    job_id: str,
    *,
    owner_token: str,
    success_url: str,
    cancel_url: str,
    email: str | None = None,
    customer_id: str | None = None,
    client_price_eur: float | None = None,
    sales: Any | None = None,
    revenue: Any | None = None,
) -> dict[str, Any]:
    """Proposal → immutable Price Lock → Core Order → Checkout session."""
    from app.integration.virtus_office.job_engine import _utc_now

    job = engine._require_owner(job_id, owner_token)
    # Prefer checkout email, else job email, else Bewerbung profile email
    profile_email = None
    if isinstance(job.get("bewerbung_profile"), dict):
        pers = (job["bewerbung_profile"].get("personal") or {})
        profile_email = str(pers.get("email") or "").strip() or None
    email = (email or job.get("email") or profile_email or "").strip() or None
    # Bind identity early (Client Workspace reuse)
    if customer_id or email:
        engine.bind_customer(
            job_id,
            owner_token=owner_token,
            customer_id=customer_id,
            email=email,
        )
        job = engine._require_owner(job_id, owner_token)
    payment = dict(job.get("payment") or {})
    if payment.get("paid"):
        return {
            **engine.public_view(job),
            "checkout": {
                "ok": True,
                "already_paid": True,
                "order_id": payment.get("order_id"),
                "checkout_url": None,
            },
        }
    if job["status"] not in {"proposal_ready", "awaiting_payment"}:
        raise OfficeJobError("invalid_state", f"Job is {job['status']}")

    proposal = dict(job.get("proposal") or {})
    if proposal.get("next_step") in {
        "select_action",
        "configure_translate",
        "configure_document",
        "complete_profile",
    }:
        raise OfficeJobError("not_ready", "Vorschlag noch nicht zahlungsbereit")

    # Reject client-forged price
    if client_price_eur is not None:
        server_price = round(float(proposal.get("price_eur") or 0), 2)
        if abs(round(float(client_price_eur), 2) - server_price) > 0.01:
            raise OfficeJobError("price_mismatch", "Übermittelter Preis abgelehnt")

    now = _utc_now()
    if payment.get("price_lock") and payment.get("order_id"):
        # Resume existing checkout if still awaiting
        assert_price_lock_intact(job)
        lock = dict(payment["price_lock"])
        order_id = str(payment["order_id"])
    else:
        lock = build_price_lock(job, locked_at=now)
        payment["price_lock"] = lock
        payment["requires_payment"] = True
        payment["status"] = "price_locked"
        payment["paid"] = False
        payment["price_locked_at"] = now
        job["payment"] = payment
        # Freeze proposal commercial fields
        proposal["price_eur"] = lock["price_eur"]
        proposal["price_locked"] = True
        proposal["payment_enabled"] = True
        proposal["next_step"] = "awaiting_payment"
        job["proposal"] = proposal
        job["status"] = "awaiting_payment"
        job["updated_at"] = now
        engine._write(job)

        if sales is None or revenue is None:
            sales, revenue = build_checkout_services(Path(engine._memory))
        order = sales.create_order(
            {
                "package_id": lock["package_id"],
                "business_name": f"Virtus Office · {lock['action_id']}",
                "description": (
                    f"Office job {job_id}: {lock['action_id']} "
                    f"→ {lock['output_format']} ({lock['filename'] or 'file'})"
                )[:2000],
                "email": (email or job.get("email") or "").strip() or None,
                "customer_id": (customer_id or job.get("customer_id") or "").strip() or None,
                "market_code": "DE",
                "ui_lang": "de",
                "motion_level": "none",
            }
        )
        order_id = str(order["order_id"])
        # Enforce locked float price (never trust client; align Core Order with lock)
        full = sales.get_order(order_id) or order
        full["price_eur"] = float(lock["price_eur"])
        full["price_label"] = f"{lock['price_eur']:.2f} €"
        full["currency"] = "EUR"
        full["product_kind"] = "office"
        full["office_job_id"] = job_id
        full["office_lock_hash"] = lock["lock_hash"]
        full["package_id"] = lock["package_id"]
        sales._save_order(full)

        payment = dict(job.get("payment") or {})
        payment["order_id"] = order_id
        payment["status"] = "awaiting_payment"
        job["payment"] = payment
        job["updated_at"] = _utc_now()
        engine._write(job)

    if sales is None or revenue is None:
        sales, revenue = build_checkout_services(Path(engine._memory))
    try:
        session = revenue.begin_checkout(
            order_id,
            success_url=success_url,
            cancel_url=cancel_url,
        )
    except ValueError as exc:
        code = str(exc)
        if code == "payment_not_configured":
            raise OfficeJobError(
                "payment_not_configured",
                "Checkout nicht konfiguriert (Stripe/Sandbox)",
            ) from exc
        raise OfficeJobError("checkout_failed", code) from exc

    payment = dict(job.get("payment") or {})
    payment["checkout_session_id"] = session.get("session_id")
    payment["checkout_url"] = session.get("checkout_url") or session.get("url")
    payment["status"] = "awaiting_payment"
    job["payment"] = payment
    job["status"] = "awaiting_payment"
    job["updated_at"] = _utc_now()
    engine._write(job)

    view = engine.public_view(job)
    return {
        **view,
        "checkout": {
            "ok": True,
            "order_id": order_id,
            "session_id": session.get("session_id"),
            "checkout_url": payment.get("checkout_url"),
            "provider": session.get("provider"),
            "price_eur": float((payment.get("price_lock") or {}).get("price_eur") or 0),
        },
    }


def on_core_order_paid(order: dict[str, Any], *, memory_dir: Path) -> dict[str, Any]:
    """Webhook / settlement hook — Core Order PAID → Office Job PAYMENT_CONFIRMED."""
    from app.integration.virtus_office.job_engine import OfficeJobEngine, _utc_now

    if not is_office_order(order):
        return {"ok": False, "skipped": True, "reason": "not_office_order"}

    job_id = str(order.get("office_job_id") or "").strip()
    if not job_id:
        logger.warning("office paid order missing office_job_id order=%s", order.get("order_id"))
        return {"ok": False, "error": "office_job_id_missing"}

    engine = OfficeJobEngine(memory_dir)
    job = engine._load(job_id)
    if not job:
        logger.warning("office job missing for paid order=%s job=%s", order.get("order_id"), job_id)
        return {"ok": False, "error": "job_not_found"}

    payment = dict(job.get("payment") or {})
    expected_order = str(payment.get("order_id") or "").strip()
    got_order = str(order.get("order_id") or "").strip()
    if expected_order and got_order and expected_order != got_order:
        logger.warning(
            "office webhook order mismatch job=%s expected=%s got=%s",
            job_id,
            expected_order,
            got_order,
        )
        return {"ok": False, "error": "order_mismatch"}

    lock = payment.get("price_lock") if isinstance(payment.get("price_lock"), dict) else {}
    locked_price = round(float(lock.get("price_eur") or payment.get("price_eur") or 0), 2)
    paid_price = round(float(order.get("price_eur") or 0), 2)
    if locked_price and abs(paid_price - locked_price) > 0.01:
        logger.warning(
            "office paid amount mismatch job=%s locked=%s paid=%s",
            job_id,
            locked_price,
            paid_price,
        )
        return {"ok": False, "error": "amount_mismatch"}

    # Idempotent
    if payment.get("paid") and payment.get("status") == "PAYMENT_CONFIRMED":
        return {"ok": True, "idempotent": True, "job_id": job_id, "order_id": got_order}

    now = _utc_now()
    payment["paid"] = True
    payment["status"] = "PAYMENT_CONFIRMED"
    payment["paid_at"] = now
    payment["order_id"] = got_order or expected_order
    payment["requires_payment"] = True
    payment["payment_provider"] = order.get("payment_provider")
    payment["payment_external_id"] = order.get("payment_external_id")
    job["payment"] = payment
    if job.get("status") in {"proposal_ready", "awaiting_payment", "created"}:
        job["status"] = "paid"
    job["updated_at"] = now
    proposal = dict(job.get("proposal") or {})
    proposal["next_step"] = "execute"
    proposal["continue_hint_de"] = "Zahlung bestätigt — Ausführung freigeschaltet."
    job["proposal"] = proposal
    engine._write(job)
    logger.info(
        "office PAYMENT_CONFIRMED job=%s order=%s amount=%.2f",
        job_id,
        got_order,
        paid_price,
    )
    # Zahlungsbestätigung email (product delivery comes after COMPLETED)
    try:
        from app.integration.virtus_office.digital_product_delivery import (
            notify_payment_confirmed,
        )

        notify_payment_confirmed(job, memory_dir=memory_dir)
        engine._write(job)
    except Exception:
        logger.exception("office_payment_receipt_notify_failed job=%s", job_id)
    return {"ok": True, "job_id": job_id, "order_id": got_order, "status": "PAYMENT_CONFIRMED"}
