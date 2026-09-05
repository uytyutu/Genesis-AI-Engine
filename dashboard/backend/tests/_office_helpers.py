"""Shared helpers for Virtus Office tests."""

from __future__ import annotations

from app.integration.virtus_office import OfficeJobEngine


def mark_office_paid(eng: OfficeJobEngine, job_id: str, owner_token: str) -> None:
    """Simulate PAYMENT_CONFIRMED so execute/download tests can run generation/QA."""
    job = eng._require_owner(job_id, owner_token)
    payment = dict(job.get("payment") or {})
    payment.update(
        {
            "paid": True,
            "requires_payment": True,
            "status": "PAYMENT_CONFIRMED",
            "order_id": payment.get("order_id") or "test-ord-paid",
        }
    )
    job["payment"] = payment
    if job.get("status") in {"proposal_ready", "awaiting_payment", "created"}:
        job["status"] = "paid"
    eng._write(job)
