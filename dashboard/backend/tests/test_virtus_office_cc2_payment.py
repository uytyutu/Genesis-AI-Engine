"""CC-2 security matrix — Office Price Lock → Core Order → Checkout → Paid → Execute."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pytest
from starlette.datastructures import Headers, UploadFile

from app.integration.virtus_office import OFFICE_PIPELINE_LIVE, OfficeJobEngine, OfficeJobError
from app.integration.virtus_office.payment_bridge import (
    build_checkout_services,
    lock_and_begin_checkout,
    mark_payment_outcome,
    on_core_order_paid,
)


def _upload(name: str, data: bytes, content_type: str) -> UploadFile:
    return UploadFile(
        file=BytesIO(data),
        filename=name,
        headers=Headers({"content-type": content_type}),
    )


def _proposal_job(eng: OfficeJobEngine):
    text = (
        "Arbeitsvertrag\n\n"
        "Arbeitgeber: Muster GmbH\n"
        "Arbeitnehmer: Max Mustermann\n"
        "Datum: 01.03.2024\n"
        "Gesamtbetrag 1.250,00 €\n"
    ).encode("utf-8")
    created = eng.create_job(service_preset="translate")
    view = eng.upload(
        created["job_id"],
        owner_token=created["owner_token"],
        upload=_upload("Arbeitsvertrag.txt", text, "text/plain"),
    )
    assert view["status"] == "proposal_ready"
    configured = eng.select_action(
        created["job_id"],
        owner_token=created["owner_token"],
        action_id="translate",
        target_language="uk",
        output_format="pdf",
    )
    return created, configured


@pytest.fixture
def sandbox_payment(monkeypatch):
    monkeypatch.setenv("GENESIS_PAYMENT_SANDBOX", "1")
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    monkeypatch.delenv("STRIPE_SECRET_KEY_LIVE", raising=False)
    yield


def test_pipeline_is_live():
    assert OFFICE_PIPELINE_LIVE is True


def test_happy_path_lock_checkout_paid_execute(tmp_path: Path, sandbox_payment):
    eng = OfficeJobEngine(tmp_path)
    created, _ = _proposal_job(eng)
    jid, tok = created["job_id"], created["owner_token"]
    sales, revenue = build_checkout_services(tmp_path)

    out = lock_and_begin_checkout(
        eng,
        jid,
        owner_token=tok,
        success_url="http://localhost:3000/office?paid=1",
        cancel_url="http://localhost:3000/office?cancel=1",
        sales=sales,
        revenue=revenue,
    )
    assert out["status"] == "awaiting_payment"
    assert out["payment"]["requires_payment"] is True
    assert out["payment"]["price_locked"] is True
    assert out["payment"]["paid"] is False
    assert out["payment"]["execute_unlocked"] is False
    assert out["checkout"]["order_id"]
    assert out["checkout"]["checkout_url"]
    order_id = out["checkout"]["order_id"]

    with pytest.raises(OfficeJobError) as blocked:
        eng.execute(jid, owner_token=tok)
    assert blocked.value.code == "payment_required"

    paid = revenue.complete_sandbox_payment(order_id)
    assert paid["ok"] is True

    view = eng.get_job(jid, owner_token=tok)
    assert view["payment"]["paid"] is True
    assert view["payment"]["status"] == "PAYMENT_CONFIRMED"
    assert view["payment"]["execute_unlocked"] is True
    assert view["status"] == "paid"

    done = eng.execute(jid, owner_token=tok)
    assert done["status"] == "completed", done.get("failure_detail")


def test_forged_price_rejected(tmp_path: Path, sandbox_payment):
    eng = OfficeJobEngine(tmp_path)
    created, _ = _proposal_job(eng)
    sales, revenue = build_checkout_services(tmp_path)
    with pytest.raises(OfficeJobError) as exc:
        lock_and_begin_checkout(
            eng,
            created["job_id"],
            owner_token=created["owner_token"],
            success_url="http://localhost:3000/ok",
            cancel_url="http://localhost:3000/cancel",
            client_price_eur=1.0,
            sales=sales,
            revenue=revenue,
        )
    assert exc.value.code == "price_mismatch"


def test_modified_parameters_after_lock_rejected(tmp_path: Path, sandbox_payment):
    eng = OfficeJobEngine(tmp_path)
    created, _ = _proposal_job(eng)
    jid, tok = created["job_id"], created["owner_token"]
    sales, revenue = build_checkout_services(tmp_path)
    lock_and_begin_checkout(
        eng,
        jid,
        owner_token=tok,
        success_url="http://localhost:3000/ok",
        cancel_url="http://localhost:3000/cancel",
        sales=sales,
        revenue=revenue,
    )
    with pytest.raises(OfficeJobError) as exc:
        eng.select_action(
            jid,
            owner_token=tok,
            action_id="translate",
            target_language="en",
            output_format="docx",
        )
    assert exc.value.code == "price_locked"


def test_wrong_owner_forbidden(tmp_path: Path, sandbox_payment):
    eng = OfficeJobEngine(tmp_path)
    created, _ = _proposal_job(eng)
    sales, revenue = build_checkout_services(tmp_path)
    with pytest.raises(OfficeJobError) as exc:
        lock_and_begin_checkout(
            eng,
            created["job_id"],
            owner_token="not-the-owner-token",
            success_url="http://localhost:3000/ok",
            cancel_url="http://localhost:3000/cancel",
            sales=sales,
            revenue=revenue,
        )
    assert exc.value.code == "forbidden"


def test_execute_before_payment_locked(tmp_path: Path, sandbox_payment):
    eng = OfficeJobEngine(tmp_path)
    created, _ = _proposal_job(eng)
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
    with pytest.raises(OfficeJobError) as exc:
        eng.execute(created["job_id"], owner_token=created["owner_token"])
    assert exc.value.code == "payment_required"


def test_duplicate_webhook_idempotent(tmp_path: Path, sandbox_payment):
    eng = OfficeJobEngine(tmp_path)
    created, _ = _proposal_job(eng)
    jid, tok = created["job_id"], created["owner_token"]
    sales, revenue = build_checkout_services(tmp_path)
    out = lock_and_begin_checkout(
        eng,
        jid,
        owner_token=tok,
        success_url="http://localhost:3000/ok",
        cancel_url="http://localhost:3000/cancel",
        sales=sales,
        revenue=revenue,
    )
    order_id = out["checkout"]["order_id"]
    first = revenue.complete_sandbox_payment(order_id)
    second = revenue.complete_sandbox_payment(order_id)
    assert first["ok"] is True
    assert second.get("already_processed") or second["ok"] is True
    view = eng.get_job(jid, owner_token=tok)
    assert view["payment"]["status"] == "PAYMENT_CONFIRMED"
    assert view["payment"]["paid"] is True


def test_failed_and_cancelled_keep_execute_locked(tmp_path: Path, sandbox_payment):
    eng = OfficeJobEngine(tmp_path)
    created, _ = _proposal_job(eng)
    jid, tok = created["job_id"], created["owner_token"]
    sales, revenue = build_checkout_services(tmp_path)
    lock_and_begin_checkout(
        eng,
        jid,
        owner_token=tok,
        success_url="http://localhost:3000/ok",
        cancel_url="http://localhost:3000/cancel",
        sales=sales,
        revenue=revenue,
    )
    mark_payment_outcome(eng, jid, owner_token=tok, outcome="failed")
    with pytest.raises(OfficeJobError) as failed:
        eng.execute(jid, owner_token=tok)
    assert failed.value.code == "payment_required"

    # Re-lock path: status still awaiting — mark cancelled
    mark_payment_outcome(eng, jid, owner_token=tok, outcome="cancelled")
    view = eng.get_job(jid, owner_token=tok)
    assert view["payment"]["status"] == "cancelled"
    assert view["payment"]["paid"] is False
    with pytest.raises(OfficeJobError) as cancelled:
        eng.execute(jid, owner_token=tok)
    assert cancelled.value.code == "payment_required"


def test_webhook_wrong_order_does_not_unlock(tmp_path: Path, sandbox_payment):
    eng = OfficeJobEngine(tmp_path)
    created, _ = _proposal_job(eng)
    jid, tok = created["job_id"], created["owner_token"]
    sales, revenue = build_checkout_services(tmp_path)
    out = lock_and_begin_checkout(
        eng,
        jid,
        owner_token=tok,
        success_url="http://localhost:3000/ok",
        cancel_url="http://localhost:3000/cancel",
        sales=sales,
        revenue=revenue,
    )
    real_order = out["checkout"]["order_id"]
    # Foreign order pretending to be office payment for this job
    foreign = {
        "order_id": "ord-foreign999",
        "office_job_id": jid,
        "product_kind": "office",
        "package_id": "office_translate",
        "price_eur": 7.90,
        "payment_provider": "stripe",
        "payment_external_id": "sess_fake",
    }
    result = on_core_order_paid(foreign, memory_dir=tmp_path)
    assert result.get("ok") is False
    assert result.get("error") == "order_mismatch"
    view = eng.get_job(jid, owner_token=tok)
    assert view["payment"]["paid"] is False
    assert view["payment"]["order_id"] == real_order


def test_repayment_already_paid(tmp_path: Path, sandbox_payment):
    eng = OfficeJobEngine(tmp_path)
    created, _ = _proposal_job(eng)
    jid, tok = created["job_id"], created["owner_token"]
    sales, revenue = build_checkout_services(tmp_path)
    out = lock_and_begin_checkout(
        eng,
        jid,
        owner_token=tok,
        success_url="http://localhost:3000/ok",
        cancel_url="http://localhost:3000/cancel",
        sales=sales,
        revenue=revenue,
    )
    revenue.complete_sandbox_payment(out["checkout"]["order_id"])
    again = lock_and_begin_checkout(
        eng,
        jid,
        owner_token=tok,
        success_url="http://localhost:3000/ok",
        cancel_url="http://localhost:3000/cancel",
        sales=sales,
        revenue=revenue,
    )
    assert again["checkout"].get("already_paid") is True


def test_stage3_unpaid_execute_blocked_without_lock(tmp_path: Path):
    """CRA #1: no free final artifact — execute requires payment even without price lock."""
    eng = OfficeJobEngine(tmp_path)
    created, _ = _proposal_job(eng)
    assert eng.get_job(created["job_id"], owner_token=created["owner_token"])[
        "payment"
    ]["execute_unlocked"] is False
    with pytest.raises(OfficeJobError) as exc:
        eng.execute(created["job_id"], owner_token=created["owner_token"])
    assert exc.value.code == "payment_required"
