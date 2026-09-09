"""Sales Kit sandbox Payment E2E — real GENESIS_PAYMENT_SANDBOX checkout path.

Controlled via:
  GENESIS_OFFICE_SALES_KIT_SANDBOX_E2E=1

Does NOT mock payment success — uses RevenuePipelineService.complete_sandbox_payment.
Email may still be mocked (ReceiptEmailService) like other Office CC-4 tests.
"""

from __future__ import annotations

import io
import json
import os
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from unittest.mock import patch

from app.integration.virtus_office.b2b_packages import (
    B2B_PRICE_EUR,
    SALES_KIT_BASIC,
    SALES_KIT_BUSINESS,
    SALES_KIT_LIVE,
    SALES_KIT_PROFESSIONAL,
    SALES_KIT_SKUS,
)
from app.integration.virtus_office.job_engine import OfficeJobEngine, OfficeJobError
from app.integration.virtus_office.office_job_ssot import OFFICE_SELLABLE_NOW
from app.integration.virtus_office.payment_bridge import (
    build_checkout_services,
    lock_and_begin_checkout,
    mark_payment_outcome,
)
from app.integration.virtus_office.sku_sales_kit import SKU_ENABLED, TIER_FILES
from app.integration.virtus_office.understanding import _price_for

DEMO_COMPANY: dict[str, Any] = {
    "company_name": "Demo GmbH",
    "description": "Digitale Dienstleistungen für kleine Unternehmen.",
    "services": [
        {"name": "Webdesign", "price": "499 EUR"},
        {"name": "Dokumentenverarbeitung"},
        {"name": "IT-Support", "price": "79 EUR/hour"},
    ],
    "prices": [
        "Webdesign — 499 EUR",
        "IT-Support — 79 EUR/hour",
    ],
    "contacts": {"email": "demo@example.test"},
    "extra_doc_count": 2,
}

TIERS = (
    ("BASIC", SALES_KIT_BASIC, 99.0),
    ("BUSINESS", SALES_KIT_BUSINESS, 199.0),
    ("PROFESSIONAL", SALES_KIT_PROFESSIONAL, 299.0),
)


def _pf(ok: bool) -> str:
    return "PASS" if ok else "FAIL"


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _enable_sandbox_env() -> None:
    os.environ["GENESIS_PAYMENT_SANDBOX"] = "1"
    os.environ["GENESIS_OFFICE_SALES_KIT_SANDBOX_E2E"] = "1"
    os.environ.pop("STRIPE_SECRET_KEY", None)
    os.environ.pop("STRIPE_SECRET_KEY_LIVE", None)


def run_tier_payment_e2e(
    eng: OfficeJobEngine,
    *,
    tier_label: str,
    tier: str,
    expected_price: float,
    memory_dir: Path,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "tier": tier,
        "checkout": "FAIL",
        "sandbox_payment": "FAIL",
        "paid_job": "FAIL",
        "execute": "FAIL",
        "validate": "FAIL",
        "cabinet": "FAIL",
        "delivery": "FAIL",
        "details": {},
    }

    # Price integrity vs canonical sources
    matrix = float(_price_for(tier))
    b2b = float(B2B_PRICE_EUR[tier])
    if abs(matrix - expected_price) > 0.01 or abs(b2b - expected_price) > 0.01:
        row["details"]["price_drift"] = {"matrix": matrix, "b2b": b2b, "expected": expected_price}
        return row

    created = eng.create_job(
        customer_id=f"cust-sk-pay-{tier}",
        email="demo@example.test",
    )
    jid, tok = created["job_id"], created["owner_token"]
    eng.configure_sales_kit_sandbox_e2e(
        jid, owner_token=tok, tier=tier, company=DEMO_COMPANY
    )

    sales, revenue = build_checkout_services(memory_dir)
    try:
        out = lock_and_begin_checkout(
            eng,
            jid,
            owner_token=tok,
            success_url="http://localhost:3000/office/order/x?paid=1",
            cancel_url="http://localhost:3000/office/order/x?cancel=1",
            email="demo@example.test",
            customer_id=f"cust-sk-pay-{tier}",
            sales=sales,
            revenue=revenue,
        )
    except OfficeJobError as exc:
        if exc.code == "payment_not_configured":
            row["details"]["blocked"] = "payment_not_configured"
            row["details"]["reason"] = str(exc.message)
            return row
        row["details"]["checkout_error"] = {"code": exc.code, "message": exc.message}
        return row

    checkout = dict(out.get("checkout") or {})
    order_id = str(checkout.get("order_id") or "")
    session_id = checkout.get("session_id")
    provider = checkout.get("provider")
    locked_price = float(checkout.get("price_eur") or 0)
    if not order_id or not session_id:
        row["details"]["checkout"] = checkout
        return row
    if abs(locked_price - expected_price) > 0.01:
        row["details"]["checkout_price"] = locked_price
        return row
    if out.get("payment", {}).get("paid"):
        row["details"]["paid_before_sandbox"] = True
        return row
    row["checkout"] = "PASS"
    row["details"]["order_id"] = order_id
    row["details"]["session_id"] = session_id
    row["details"]["provider"] = provider

    # Real sandbox payment — not a fake paid flag
    paid = revenue.complete_sandbox_payment(order_id)
    if not paid.get("ok") and paid.get("status") not in {"PAYMENT_CONFIRMED", "paid", "completed"}:
        # complete_sandbox_payment return shapes vary — check job
        pass
    view = eng.public_view(eng._require_owner(jid, tok))
    if not view.get("payment", {}).get("paid"):
        # Try on_core_order path via reload
        job = eng._load(jid)
        row["details"]["sandbox_raw"] = {
            "paid_return": {k: paid.get(k) for k in list(paid)[:12]} if isinstance(paid, dict) else str(paid),
            "payment": (job or {}).get("payment"),
        }
        return row
    row["sandbox_payment"] = "PASS"
    row["paid_job"] = "PASS"

    with patch(
        "app.integration.receipt_email_service.ReceiptEmailService.send_office_delivery_ready",
        return_value={"ok": True},
    ), patch(
        "app.integration.receipt_email_service.ReceiptEmailService.send_office_payment_receipt",
        return_value={"ok": True},
    ):
        done = eng.execute(jid, owner_token=tok)

    if done.get("status") != "completed":
        row["details"]["execute_view"] = {
            "status": done.get("status"),
            "failure_reason": done.get("failure_reason"),
            "failure_detail": done.get("failure_detail"),
            "quality": done.get("quality"),
        }
        return row
    row["execute"] = "PASS"

    # Validator already ran inside execute; confirm artifact ZIP
    job = eng._load(jid)
    assert job is not None
    art = dict(job.get("artifact") or {})
    if art.get("held_for_qa_fail") or not art.get("material_id"):
        row["details"]["artifact"] = art
        return row
    data, fn, mime = eng.get_artifact_bytes(jid, owner_token=tok, fmt="zip")
    if data[:2] != b"PK":
        row["details"]["artifact_type"] = mime
        return row
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        names = set(zf.namelist())
    expected_files = {f"VIRTUS_SALES_KIT/{n}" for n in TIER_FILES[tier]}
    if not expected_files.issubset(names):
        row["details"]["missing_files"] = sorted(expected_files - names)
        return row
    row["validate"] = "PASS"

    d = dict(done.get("delivery") or {})
    cabinet_ok = bool(d.get("cabinet_ready"))
    email_ok = str(d.get("email_status") or "") == "EMAIL_SENT"
    row["cabinet"] = _pf(cabinet_ok)
    row["delivery"] = _pf(cabinet_ok and email_ok and bool(fn))
    row["details"]["email_note"] = "ReceiptEmailService mocked — payment path is real sandbox"
    row["details"]["filename"] = fn
    return row


def run_failure_tests(memory_dir: Path) -> dict[str, str]:
    _enable_sandbox_env()
    eng = OfficeJobEngine(memory_dir / "fail")
    out: dict[str, str] = {}

    # wrong SKU via public select_action (not sellable / not available)
    created = eng.create_job(email="x@example.com")
    try:
        eng.select_action(
            created["job_id"],
            owner_token=created["owner_token"],
            action_id="sales_kit_business",
        )
        out["wrong_sku"] = "FAIL"
    except OfficeJobError as exc:
        out["wrong_sku"] = _pf(
            exc.code
            in {
                "action_not_available",
                "not_ready",
                "invalid_action",
                "invalid_state",
            }
        )

    # wrong tier
    try:
        eng.configure_sales_kit_sandbox_e2e(
            created["job_id"],
            owner_token=created["owner_token"],
            tier="sales_kit_nope",
            company=DEMO_COMPANY,
        )
        out["wrong_tier"] = "FAIL"
    except OfficeJobError as exc:
        out["wrong_tier"] = _pf(exc.code in {"invalid_tier", "invalid_action"})

    # price mismatch — forged client price
    created2 = eng.create_job(email="y@example.com")
    eng.configure_sales_kit_sandbox_e2e(
        created2["job_id"],
        owner_token=created2["owner_token"],
        tier=SALES_KIT_BASIC,
        company=DEMO_COMPANY,
    )
    sales, revenue = build_checkout_services(memory_dir / "fail")
    try:
        lock_and_begin_checkout(
            eng,
            created2["job_id"],
            owner_token=created2["owner_token"],
            success_url="http://localhost:3000/ok",
            cancel_url="http://localhost:3000/cancel",
            client_price_eur=1.0,
            sales=sales,
            revenue=revenue,
        )
        out["price_mismatch"] = "FAIL"
    except OfficeJobError as exc:
        out["price_mismatch"] = _pf(exc.code == "price_mismatch")

    # public purchase gate behavior depends on LIVE state
    eng_pub = OfficeJobEngine(memory_dir / "public")
    created3 = eng_pub.create_job(email="public@example.com")
    # Manually forge a proposal_ready sales kit job WITHOUT sandbox marker
    job = eng_pub._require_owner(created3["job_id"], created3["owner_token"])
    job["understanding"] = {
        "filled": True,
        "intent": {
            "id": SALES_KIT_BUSINESS,
            "output_format": "zip",
            "price_eur": 199.0,
            "label_de": "Sales Kit Business",
        },
    }
    job["proposal"] = {
        "filled": True,
        "task": SALES_KIT_BUSINESS,
        "price_eur": 199.0,
        "next_step": "awaiting_payment",
        "payment_enabled": True,
        "result_format": "zip",
    }
    job["sales_kit_company"] = DEMO_COMPANY
    job["sales_kit_sandbox_e2e"] = False
    job["status"] = "proposal_ready"
    eng_pub._write(job)
    sales2, revenue2 = build_checkout_services(memory_dir / "public")
    try:
        lock_and_begin_checkout(
            eng_pub,
            created3["job_id"],
            owner_token=created3["owner_token"],
            success_url="http://localhost:3000/ok",
            cancel_url="http://localhost:3000/cancel",
            sales=sales2,
            revenue=revenue2,
        )
        out["public_purchase_gate"] = _pf(SALES_KIT_LIVE is True)
    except OfficeJobError as exc:
        out["public_purchase_gate"] = _pf(
            (SALES_KIT_LIVE is False and exc.code == "product_not_live")
            or (SALES_KIT_LIVE is True and exc.code != "product_not_live")
        )

    # payment failure → no execute
    created4 = eng.create_job(email="failpay@example.com")
    eng.configure_sales_kit_sandbox_e2e(
        created4["job_id"],
        owner_token=created4["owner_token"],
        tier=SALES_KIT_BASIC,
        company=DEMO_COMPANY,
    )
    sales3, revenue3 = build_checkout_services(memory_dir / "fail")
    lock_and_begin_checkout(
        eng,
        created4["job_id"],
        owner_token=created4["owner_token"],
        success_url="http://localhost:3000/ok",
        cancel_url="http://localhost:3000/cancel",
        sales=sales3,
        revenue=revenue3,
    )
    mark_payment_outcome(
        eng, created4["job_id"], owner_token=created4["owner_token"], outcome="failed"
    )
    try:
        eng.execute(created4["job_id"], owner_token=created4["owner_token"])
        out["payment_failure"] = "FAIL"
    except OfficeJobError as exc:
        out["payment_failure"] = _pf(exc.code == "payment_required")

    # unpaid → no delivery (execute blocked already; also unpaid deliver)
    out["unpaid_delivery"] = out["payment_failure"]  # same gate; reinforce
    job4 = eng._load(created4["job_id"])
    from app.integration.virtus_office.digital_product_delivery import deliver_completed_product

    if job4:
        job4["status"] = "completed"
        job4["artifact"] = {"material_id": "x", "held_for_qa_fail": False}
        # payment still unpaid
        res = deliver_completed_product(eng, job4)
        out["unpaid_delivery"] = _pf(res.get("ok") is False and res.get("error") == "unpaid")

    return out


def run_payment_e2e(*, memory_dir: Path | None = None) -> dict[str, Any]:
    _enable_sandbox_env()
    base = memory_dir or Path(".runtime") / "office_sales_kit_payment_e2e"
    base.mkdir(parents=True, exist_ok=True)
    eng = OfficeJobEngine(base / "jobs")

    tiers: dict[str, Any] = {}
    blocked_reason = None
    for label, tier, price in TIERS:
        tiers[label] = run_tier_payment_e2e(
            eng,
            tier_label=label,
            tier=tier,
            expected_price=price,
            memory_dir=base / "jobs",
        )
        if tiers[label]["details"].get("blocked") == "payment_not_configured":
            blocked_reason = tiers[label]["details"].get("reason")

    if blocked_reason:
        report = {
            "product": "sales_kit",
            "generated_at": _utc(),
            "PAYMENT_E2E": "BLOCKED",
            "REASON": blocked_reason,
            "LIVE": {"SALES_KIT_LIVE": SALES_KIT_LIVE, "SKU_ENABLED": SKU_ENABLED},
            "OFFICE_SELLABLE_NOW": (
                "LIVE_WITH_SALES_KIT"
                if all(s in OFFICE_SELLABLE_NOW for s in SALES_KIT_SKUS)
                else "UNCHANGED"
            ),
            "tier_details": tiers,
            "FINAL_VERDICT": "PAYMENT_E2E=BLOCKED",
        }
        path = base / "SALES_KIT_PAYMENT_E2E.json"
        path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        report["report_path"] = str(path.resolve())
        return report

    failures = run_failure_tests(base / "failures")

    keys = ("checkout", "sandbox_payment", "paid_job", "execute", "validate", "cabinet", "delivery")
    tier_ok = all(tiers[t][k] == "PASS" for t in ("BASIC", "BUSINESS", "PROFESSIONAL") for k in keys)
    fail_ok = all(v == "PASS" for v in failures.values())
    price_ok = all(
        abs(float(B2B_PRICE_EUR[tier]) - price) < 0.01
        and abs(float(_price_for(tier)) - price) < 0.01
        for _, tier, price in TIERS
    )
    live_ok = SALES_KIT_LIVE is True and SKU_ENABLED is True
    sellable_ok = all(s in OFFICE_SELLABLE_NOW for s in SALES_KIT_SKUS)

    verdict = "PASS" if (tier_ok and fail_ok and price_ok and live_ok and sellable_ok) else "FAIL"

    report = {
        "product": "sales_kit",
        "generated_at": _utc(),
        "SALES_KIT_PAYMENT_E2E": {
            label: {k: tiers[label][k] for k in keys}
            for label, _, _ in TIERS
        },
        "PRICE_INTEGRITY": _pf(price_ok),
        "PUBLIC_LIVE_GATE": failures.get("public_purchase_gate", "FAIL"),
        "FAILURE_TESTS": failures,
        "LIVE": {
            "SALES_KIT_LIVE": SALES_KIT_LIVE,
            "SKU_ENABLED": SKU_ENABLED,
        },
        "OFFICE_SELLABLE_NOW": (
            "LIVE_WITH_SALES_KIT" if sellable_ok else "UNCHANGED"
        ),
        "tier_details": tiers,
        "PAYMENT_E2E": verdict,
        "FINAL_VERDICT": f"PAYMENT_E2E={verdict}",
    }
    path = base / "SALES_KIT_PAYMENT_E2E.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    report["report_path"] = str(path.resolve())
    return report


def main() -> int:
    report = run_payment_e2e()
    print(json.dumps(report, indent=2, ensure_ascii=False))
    code = report.get("PAYMENT_E2E")
    if code == "PASS":
        return 0
    if code == "BLOCKED":
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
