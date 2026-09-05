"""CC-4 — Digital Product Delivery + delivery token security."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from starlette.datastructures import Headers, UploadFile

from app.integration.virtus_office import OFFICE_PIPELINE_LIVE, OfficeJobEngine, OfficeJobError
from app.integration.virtus_office.digital_product_delivery import (
    EMAIL_FAILED,
    EMAIL_SENT,
    deliver_completed_product,
    verify_delivery_token,
)
from app.integration.virtus_office.payment_bridge import (
    build_checkout_services,
    lock_and_begin_checkout,
)
from app.integration.virtus_office.post_pay import download_formats


def _upload(name: str, data: bytes, content_type: str) -> UploadFile:
    return UploadFile(
        file=BytesIO(data),
        filename=name,
        headers=Headers({"content-type": content_type}),
    )


def _paid_completed(eng: OfficeJobEngine, tmp_path: Path, monkeypatch):
    monkeypatch.setenv("GENESIS_PAYMENT_SANDBOX", "1")
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    monkeypatch.delenv("STRIPE_SECRET_KEY_LIVE", raising=False)
    text = (
        b"Arbeitsvertrag\nArbeitgeber: Muster GmbH\n"
        b"Arbeitnehmer: Max Mustermann\nDatum: 01.03.2024\n"
    )
    created = eng.create_job(
        service_preset="translate",
        customer_id="cust-cc4",
        email="buyer@example.com",
    )
    eng.upload(
        created["job_id"],
        owner_token=created["owner_token"],
        upload=_upload("a.txt", text, "text/plain"),
    )
    eng.select_action(
        created["job_id"],
        owner_token=created["owner_token"],
        action_id="translate",
        target_language="uk",
        output_format="pdf",
    )
    sales, revenue = build_checkout_services(tmp_path)
    out = lock_and_begin_checkout(
        eng,
        created["job_id"],
        owner_token=created["owner_token"],
        success_url="http://localhost:3000/office/order/x?paid=1",
        cancel_url="http://localhost:3000/office/order/x?cancel=1",
        email="buyer@example.com",
        customer_id="cust-cc4",
        sales=sales,
        revenue=revenue,
    )
    revenue.complete_sandbox_payment(out["checkout"]["order_id"])
    with patch(
        "app.integration.receipt_email_service.ReceiptEmailService.send_office_delivery_ready",
        return_value={"ok": True},
    ), patch(
        "app.integration.receipt_email_service.ReceiptEmailService.send_office_payment_receipt",
        return_value={"ok": True},
    ):
        done = eng.execute(created["job_id"], owner_token=created["owner_token"])
    return created, done


def test_pipeline_is_live():
    assert OFFICE_PIPELINE_LIVE is True


def test_paid_completed_triggers_delivery(tmp_path: Path, monkeypatch):
    eng = OfficeJobEngine(tmp_path)
    created, done = _paid_completed(eng, tmp_path, monkeypatch)
    assert done["status"] == "completed"
    assert done["delivery"]["cabinet_ready"] is True
    assert done["delivery"]["email_status"] == EMAIL_SENT
    assert done["delivery"]["receipt_path"]
    assert any(f["available"] for f in done["download_formats"] if f["format"] == "pdf")


def test_unpaid_no_delivery(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("GENESIS_PAYMENT_SANDBOX", "1")
    eng = OfficeJobEngine(tmp_path)
    created = eng.create_job(email="x@example.com")
    eng.upload(
        created["job_id"],
        owner_token=created["owner_token"],
        upload=_upload("a.txt", b"Hallo Vertrag 2024\n", "text/plain"),
    )
    eng.select_action(
        created["job_id"],
        owner_token=created["owner_token"],
        action_id="translate",
        target_language="en",
        output_format="pdf",
    )
    sales, revenue = build_checkout_services(tmp_path)
    lock_and_begin_checkout(
        eng,
        created["job_id"],
        owner_token=created["owner_token"],
        success_url="http://localhost:3000/ok",
        cancel_url="http://localhost:3000/cancel",
        sales=sales,
        revenue=revenue,
    )
    job = eng._require_owner(created["job_id"], created["owner_token"])
    res = deliver_completed_product(eng, job)
    assert res.get("ok") is False
    assert res.get("error") in {"not_completed", "unpaid"}


def test_qa_fail_no_delivery(tmp_path: Path):
    eng = OfficeJobEngine(tmp_path)
    created = eng.create_job(email="x@example.com")
    job = eng._require_owner(created["job_id"], created["owner_token"])
    # Safety net: even if status were completed, held_for_qa_fail blocks delivery
    job["status"] = "completed"
    job["payment"] = {"paid": True, "requires_payment": True, "order_id": "ord-1"}
    job["artifact"] = {
        "material_id": "mat-x",
        "filename": "x.pdf",
        "ext": "pdf",
        "held_for_qa_fail": True,
    }
    eng._write(job)
    res = deliver_completed_product(eng, job)
    assert res.get("ok") is False
    assert res.get("error") == "qa_failed"


def test_delivery_token_scoped(tmp_path: Path, monkeypatch):
    eng = OfficeJobEngine(tmp_path)
    created, done = _paid_completed(eng, tmp_path, monkeypatch)
    job = eng._load(created["job_id"])
    assert job is not None
    # Re-deliver to capture token from return
    with patch(
        "app.integration.receipt_email_service.ReceiptEmailService.send_office_delivery_ready",
        return_value={"ok": True},
    ):
        again = deliver_completed_product(eng, job, force_retry=True)
    token = again.get("download_token")
    assert token
    job2 = eng._load(created["job_id"])
    assert verify_delivery_token(job2, token) is True
    assert verify_delivery_token(job2, "wrong-token-value-xxxxx") is False

    data, _fn, _mime = eng.get_artifact_with_delivery_token(
        created["job_id"], delivery_token=token, fmt="pdf"
    )
    assert data.startswith(b"%PDF")

    with pytest.raises(OfficeJobError) as exc:
        eng.get_artifact_with_delivery_token(
            created["job_id"], delivery_token="forged-token-abcdef", fmt="pdf"
        )
    assert exc.value.code == "forbidden"


def test_duplicate_delivery_idempotent(tmp_path: Path, monkeypatch):
    eng = OfficeJobEngine(tmp_path)
    created, _ = _paid_completed(eng, tmp_path, monkeypatch)
    job = eng._load(created["job_id"])
    with patch(
        "app.integration.receipt_email_service.ReceiptEmailService.send_office_delivery_ready",
        return_value={"ok": True},
    ) as send:
        first = deliver_completed_product(eng, job)
        second = deliver_completed_product(eng, job)
    assert first.get("email_status") == EMAIL_SENT or first.get("idempotent")
    assert second.get("idempotent") is True
    # Second call without force_retry should not send again
    assert send.call_count <= 1


def test_email_failure_keeps_completed(tmp_path: Path, monkeypatch):
    eng = OfficeJobEngine(tmp_path)
    created, done = _paid_completed(eng, tmp_path, monkeypatch)
    assert done["status"] == "completed"
    job = eng._load(created["job_id"])
    with patch(
        "app.integration.receipt_email_service.ReceiptEmailService.send_office_delivery_ready",
        side_effect=RuntimeError("smtp down"),
    ):
        res = deliver_completed_product(eng, job, force_retry=True)
    assert res.get("email_status") == EMAIL_FAILED
    fresh = eng.get_job(created["job_id"], owner_token=created["owner_token"])
    assert fresh["status"] == "completed"
    assert fresh["artifact_download"]


def test_zip_format_in_download_buttons():
    job = {
        "job_id": "ojob-1",
        "artifact": {"ext": "zip", "filename": "paket.zip"},
    }
    formats = download_formats(job, download_ready=True)
    zip_row = next(f for f in formats if f["format"] == "zip")
    assert zip_row["available"] is True
    assert next(f for f in formats if f["format"] == "pdf")["available"] is False
