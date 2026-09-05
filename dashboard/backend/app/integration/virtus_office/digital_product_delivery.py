"""CC-4 — Digital Product Delivery (cabinet + secure email).

Universal for Office products (Bewerbung, translate, templates, …).
Does NOT write trading / affiliate / Virtus Money ledgers.

Flow after COMPLETED + paid:
  ARTIFACT_READY → DELIVERY record → EMAIL (secure link) → Cabinet download

Email failure never deletes the artifact; order stays COMPLETED.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger("virtus.office.delivery")

EMAIL_PENDING = "EMAIL_PENDING"
EMAIL_SENT = "EMAIL_SENT"
EMAIL_FAILED = "EMAIL_FAILED"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _public_url(path: str) -> str:
    from app.integration.public_site_url import configured_public_base

    base = configured_public_base()
    p = path if path.startswith("/") else f"/{path}"
    return f"{base}{p}"


def delivery_public_view(job: dict[str, Any]) -> dict[str, Any]:
    d = dict(job.get("delivery") or {})
    payment = dict(job.get("payment") or {})
    order_id = payment.get("order_id")
    email_status = str(d.get("email_status") or "none")
    cabinet_ready = bool(
        job.get("status") == "completed"
        and payment.get("paid")
        and not (job.get("artifact") or {}).get("held_for_qa_fail")
    )
    email_ok = email_status == EMAIL_SENT
    return {
        "delivery_id": d.get("delivery_id"),
        "email_status": email_status,
        "email_ok": email_ok,
        "email_error": d.get("email_error"),
        "email_sent_at": d.get("email_sent_at"),
        "email_attempts": int(d.get("email_attempts") or 0),
        "cabinet_ready": cabinet_ready,
        # Honest: cabinet download ≠ email success
        "fully_delivered": cabinet_ready and email_ok,
        "receipt_path": f"/order/status/{order_id}" if order_id else None,
        "order_page_path": f"/office/order/{job.get('job_id')}",
        "product_label": d.get("product_label")
        or (job.get("proposal") or {}).get("task_label_de")
        or (job.get("proposal") or {}).get("task"),
    }


def verify_delivery_token(job: dict[str, Any], token: str | None) -> bool:
    if not token:
        return False
    expected = str((job.get("delivery") or {}).get("download_token_hash") or "")
    if not expected:
        return False
    got = _hash_token(token.strip())
    return hmac.compare_digest(expected, got)


def _product_label(job: dict[str, Any]) -> str:
    proposal = dict(job.get("proposal") or {})
    task = str(proposal.get("task_label_de") or proposal.get("task") or "").strip()
    if task:
        return task
    intent = dict((job.get("understanding") or {}).get("intent") or {})
    aid = str(intent.get("id") or job.get("service_preset") or "Virtus Office")
    labels = {
        "lebenslauf_create": "Lebenslauf erstellen",
        "lebenslauf_improve": "Lebenslauf verbessern",
        "bewerbungsschreiben": "Bewerbungsschreiben",
        "bewerbung_paket": "Bewerbung-Paket",
        "translate": "Übersetzung",
        "convert_docx": "Word-Dokument",
        "extract_data": "Datenexport",
    }
    return labels.get(aid, f"Virtus Office · {aid}")


def _file_list(job: dict[str, Any]) -> list[str]:
    artifact = dict(job.get("artifact") or {})
    name = str(artifact.get("filename") or "").strip()
    if name:
        return [name]
    ext = str(artifact.get("ext") or "").strip()
    if ext:
        return [f"Ergebnis.{ext}"]
    return []


def notify_payment_confirmed(job: dict[str, Any], *, memory_dir: Path) -> dict[str, Any]:
    """Zahlungsbestätigung after PAYMENT_CONFIRMED — no product files yet."""
    payment = dict(job.get("payment") or {})
    if not payment.get("paid"):
        return {"ok": False, "error": "not_paid"}
    email = str(job.get("email") or "").strip()
    if not email and isinstance(job.get("bewerbung_profile"), dict):
        pers = (job["bewerbung_profile"].get("personal") or {})
        email = str(pers.get("email") or "").strip()
    if not email:
        return {"ok": False, "error": "no_email", "skipped": True}

    order_id = str(payment.get("order_id") or "")
    job_id = str(job.get("job_id") or "")
    order_url = _public_url(f"/office/order/{job_id}")
    receipt_url = _public_url(f"/order/status/{order_id}") if order_id else order_url
    product = _product_label(job)
    price = payment.get("price_eur") or (payment.get("price_lock") or {}).get("price_eur")
    price_s = f"{float(price):.2f} €" if price is not None else ""

    # Idempotency for payment receipt mail
    delivery = dict(job.get("delivery") or {})
    if delivery.get("payment_email_sent"):
        return {"ok": True, "idempotent": True, "kind": "payment_receipt"}

    try:
        from app.integration.receipt_email_service import ReceiptEmailService

        mailer = ReceiptEmailService(memory_dir)
        result = mailer.send_office_payment_receipt(
            to=email,
            order_id=order_id or job_id,
            product=product,
            price_label=price_s,
            order_url=order_url,
            receipt_url=receipt_url,
            customer_name=_customer_name(job),
        )
        if result.get("ok"):
            delivery["payment_email_sent"] = True
            delivery["payment_email_at"] = _utc_now()
            job["delivery"] = delivery
        return {"ok": bool(result.get("ok")), "kind": "payment_receipt", "email": result}
    except Exception as exc:  # noqa: BLE001
        logger.exception("office_payment_receipt_failed job=%s", job_id)
        return {"ok": False, "error": str(exc)[:200]}


def deliver_completed_product(
    engine: Any,
    job: dict[str, Any],
    *,
    force_retry: bool = False,
) -> dict[str, Any]:
    """After COMPLETED + paid + QA pass → cabinet already ready; email secure link."""
    job_id = str(job.get("job_id") or "")
    payment = dict(job.get("payment") or {})
    artifact = dict(job.get("artifact") or {})

    if job.get("status") != "completed":
        return {"ok": False, "error": "not_completed"}
    if payment.get("requires_payment") or payment.get("price_lock"):
        if not payment.get("paid"):
            return {"ok": False, "error": "unpaid"}
    if artifact.get("held_for_qa_fail"):
        return {"ok": False, "error": "qa_failed"}
    if not artifact.get("material_id"):
        return {"ok": False, "error": "artifact_missing"}

    delivery = dict(job.get("delivery") or {})
    if delivery.get("email_status") == EMAIL_SENT and not force_retry:
        return {
            "ok": True,
            "idempotent": True,
            "delivery_id": delivery.get("delivery_id"),
            "email_status": EMAIL_SENT,
        }

    order_id = str(payment.get("order_id") or "")
    delivery_id = str(delivery.get("delivery_id") or f"odel-{secrets.token_hex(8)}")
    idem = f"office-delivery:{order_id or job_id}:{job_id}"
    if (
        not force_retry
        and delivery.get("idempotency_key") == idem
        and delivery.get("email_status") == EMAIL_SENT
    ):
        return {
            "ok": True,
            "idempotent": True,
            "delivery_id": delivery_id,
            "email_status": EMAIL_SENT,
        }

    plain_token = secrets.token_urlsafe(32)
    delivery.update(
        {
            "delivery_id": delivery_id,
            "idempotency_key": idem,
            "product_label": _product_label(job),
            "download_token_hash": _hash_token(plain_token),
            "email_status": EMAIL_PENDING,
            "email_attempts": int(delivery.get("email_attempts") or 0) + 1,
            "updated_at": _utc_now(),
            "files": _file_list(job),
        }
    )
    job["delivery"] = delivery
    engine._write(job)

    email = str(job.get("email") or "").strip()
    if not email and isinstance(job.get("bewerbung_profile"), dict):
        pers = (job["bewerbung_profile"].get("personal") or {})
        email = str(pers.get("email") or "").strip()
    if not email:
        delivery["email_status"] = EMAIL_FAILED
        delivery["email_error"] = "no_email"
        job["delivery"] = delivery
        engine._write(job)
        return {
            "ok": True,
            "cabinet_only": True,
            "email_status": EMAIL_FAILED,
            "delivery_id": delivery_id,
            "download_token": plain_token,  # for tests / claim; not logged
        }

    order_url = _public_url(f"/office/order/{job_id}?dt={plain_token}")
    receipt_url = (
        _public_url(f"/order/status/{order_id}") if order_id else order_url
    )
    try:
        from app.integration.receipt_email_service import ReceiptEmailService

        mailer = ReceiptEmailService(Path(engine._memory))
        result = mailer.send_office_delivery_ready(
            to=email,
            order_id=order_id or job_id,
            product=_product_label(job),
            files=_file_list(job),
            download_url=order_url,
            receipt_url=receipt_url,
            customer_name=_customer_name(job),
        )
        if result.get("ok"):
            delivery["email_status"] = EMAIL_SENT
            delivery["email_sent_at"] = _utc_now()
            delivery["email_error"] = None
        else:
            delivery["email_status"] = EMAIL_FAILED
            delivery["email_error"] = str(result.get("error") or result.get("reason") or "send_failed")[:200]
        job["delivery"] = delivery
        engine._write(job)
        email_ok = delivery["email_status"] == EMAIL_SENT
        return {
            "ok": True,  # cabinet artifact path succeeded; email is separate
            "email_ok": email_ok,
            "delivery_id": delivery_id,
            "email_status": delivery["email_status"],
            "email": result,
            "download_token": plain_token,
            "fully_delivered": email_ok,
        }
    except Exception as exc:  # noqa: BLE001
        logger.exception("office_delivery_email_failed job=%s", job_id)
        delivery["email_status"] = EMAIL_FAILED
        delivery["email_error"] = str(exc)[:200]
        job["delivery"] = delivery
        engine._write(job)
        return {
            "ok": True,
            "cabinet_only": True,
            "email_status": EMAIL_FAILED,
            "delivery_id": delivery_id,
            "error": str(exc)[:200],
            "download_token": plain_token,
        }


def _customer_name(job: dict[str, Any]) -> str:
    profile = job.get("bewerbung_profile") if isinstance(job.get("bewerbung_profile"), dict) else {}
    pers = profile.get("personal") if isinstance(profile.get("personal"), dict) else {}
    name = str(pers.get("full_name") or "").strip()
    if name:
        return name
    return "Kunde"


def claim_delivery_access(engine: Any, job_id: str, *, delivery_token: str) -> dict[str, Any]:
    """Validate scoped delivery token — returns public view if OK (no owner_token leak)."""
    from app.integration.virtus_office.job_engine import OfficeJobError

    job = engine._load(job_id)
    if not job:
        raise OfficeJobError("not_found", "Job nicht gefunden")
    if not verify_delivery_token(job, delivery_token):
        raise OfficeJobError("forbidden", "Ungültiger Delivery-Token")
    view = engine.public_view(job)
    view["delivery_token_valid"] = True
    return view
