"""CC-3 — post-pay progress, secure artifact, cabinet isolation."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pytest
from starlette.datastructures import Headers, UploadFile

from app.integration.virtus_office import OFFICE_PIPELINE_LIVE, OfficeJobEngine, OfficeJobError
from app.integration.virtus_office.payment_bridge import (
    build_checkout_services,
    lock_and_begin_checkout,
)
from app.integration.virtus_office.post_pay import progress_steps


def _upload(name: str, data: bytes, content_type: str) -> UploadFile:
    return UploadFile(
        file=BytesIO(data),
        filename=name,
        headers=Headers({"content-type": content_type}),
    )


def _paid_job(eng: OfficeJobEngine, tmp_path: Path, monkeypatch):
    monkeypatch.setenv("GENESIS_PAYMENT_SANDBOX", "1")
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    monkeypatch.delenv("STRIPE_SECRET_KEY_LIVE", raising=False)
    text = b"Rechnung Nr. 12\nBetrag 99,00 EUR\nDatum 01.02.2025\n"
    created = eng.create_job(service_preset="translate", customer_id="cust-cc3", email="a@example.com")
    eng.upload(
        created["job_id"],
        owner_token=created["owner_token"],
        upload=_upload("rechnung.txt", text, "text/plain"),
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
        customer_id="cust-cc3",
        email="a@example.com",
        sales=sales,
        revenue=revenue,
    )
    revenue.complete_sandbox_payment(out["checkout"]["order_id"])
    return created


def test_pipeline_is_live():
    assert OFFICE_PIPELINE_LIVE is True


def test_paid_auto_execute_and_download(tmp_path: Path, monkeypatch):
    eng = OfficeJobEngine(tmp_path)
    created = _paid_job(eng, tmp_path, monkeypatch)
    jid, tok = created["job_id"], created["owner_token"]
    view = eng.get_job(jid, owner_token=tok)
    assert view["payment"]["paid"] is True
    assert view["status"] == "paid"
    steps = progress_steps(eng._load(jid))
    assert steps[0]["state"] == "done"

    done = eng.execute(jid, owner_token=tok)
    assert done["status"] == "completed", done.get("failure_detail")
    assert done["artifact_download"]
    assert any(f["available"] for f in done["download_formats"])

    data, filename, mime = eng.get_artifact_bytes(jid, owner_token=tok, fmt="pdf")
    assert data.startswith(b"%PDF")
    assert filename.endswith(".pdf")
    assert "pdf" in mime or mime.startswith("application/")


def test_unpaid_artifact_blocked(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("GENESIS_PAYMENT_SANDBOX", "1")
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    eng = OfficeJobEngine(tmp_path)
    created = eng.create_job()
    eng.upload(
        created["job_id"],
        owner_token=created["owner_token"],
        upload=_upload("a.txt", b"Hallo Welt Vertrag 12.01.2024\n", "text/plain"),
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
    with pytest.raises(OfficeJobError) as exc:
        eng.execute(created["job_id"], owner_token=created["owner_token"])
    assert exc.value.code == "payment_required"


def test_wrong_customer_forbidden(tmp_path: Path, monkeypatch):
    eng = OfficeJobEngine(tmp_path)
    created = _paid_job(eng, tmp_path, monkeypatch)
    jid = created["job_id"]
    eng.execute(jid, owner_token=created["owner_token"])
    with pytest.raises(OfficeJobError) as exc:
        eng.get_for_customer(jid, customer_id="other-user", email="other@example.com")
    assert exc.value.code == "forbidden"
    with pytest.raises(OfficeJobError) as art:
        eng.get_artifact_for_customer(
            jid, customer_id="other-user", email="other@example.com", fmt="pdf"
        )
    assert art.value.code == "forbidden"


def test_owner_can_list_and_reopen(tmp_path: Path, monkeypatch):
    eng = OfficeJobEngine(tmp_path)
    created = _paid_job(eng, tmp_path, monkeypatch)
    eng.execute(created["job_id"], owner_token=created["owner_token"])
    rows = eng.list_for_customer(customer_id="cust-cc3", email="a@example.com")
    assert any(r["job_id"] == created["job_id"] for r in rows)
    again = eng.get_for_customer(
        created["job_id"], customer_id="cust-cc3", email="a@example.com"
    )
    assert again["status"] == "completed"
    assert again["artifact_download"]


def test_wrong_format_rejected(tmp_path: Path, monkeypatch):
    eng = OfficeJobEngine(tmp_path)
    created = _paid_job(eng, tmp_path, monkeypatch)
    eng.execute(created["job_id"], owner_token=created["owner_token"])
    with pytest.raises(OfficeJobError) as exc:
        eng.get_artifact_bytes(
            created["job_id"], owner_token=created["owner_token"], fmt="xlsx"
        )
    assert exc.value.code == "format_unavailable"


def test_qa_fail_holds_artifact(tmp_path: Path):
    """Simulate held_for_qa_fail — download must stay blocked."""
    eng = OfficeJobEngine(tmp_path)
    created = eng.create_job(customer_id="cust-qa")
    jid, tok = created["job_id"], created["owner_token"]
    job = eng._require_owner(jid, tok)
    job["status"] = "failed"
    job["failure_reason"] = "quality_gate_failed"
    job["payment"] = {"paid": True, "requires_payment": True, "status": "PAYMENT_CONFIRMED"}
    job["artifact"] = {
        "material_id": "mat-fake",
        "filename": "x.pdf",
        "ext": "pdf",
        "mime": "application/pdf",
        "size": 10,
        "held_for_qa_fail": True,
    }
    eng._write(job)
    with pytest.raises(OfficeJobError) as exc:
        eng.get_artifact_bytes(jid, owner_token=tok)
    assert exc.value.code == "quality_gate_failed"
