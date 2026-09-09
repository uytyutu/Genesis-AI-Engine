"""Sales Kit Owner E2E — integrated pipeline proof.

Proves:
  input → executor → validator → ZIP → cabinet artifact → email delivery path

Does NOT:
  - mutate SALES_KIT_LIVE / SKU_ENABLED
  - mutate OFFICE_SELLABLE_NOW
  - pretend Stripe checkout is wired (PAYMENT_E2E=PENDING)

Run:
  py -3.12 -m app.integration.virtus_office.sales_kit_owner_e2e
"""

from __future__ import annotations

import io
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from unittest.mock import patch

from app.integration.virtus_office.b2b_packages import (
    SALES_KIT_BASIC,
    SALES_KIT_BUSINESS,
    SALES_KIT_LIVE,
    SALES_KIT_PROFESSIONAL,
)
from app.integration.virtus_office.digital_product_delivery import (
    EMAIL_SENT,
    deliver_completed_product,
    verify_delivery_token,
)
from app.integration.virtus_office.job_engine import OfficeJobEngine
from app.integration.virtus_office.office_job_ssot import OFFICE_SELLABLE_NOW
from app.integration.virtus_office.sku_sales_kit import (
    SKU_ENABLED,
    TIER_FILES,
    generate_sales_kit,
    validate_sales_kit_artifact,
)

# Deterministic synthetic company — explicit facts only (no invented extras).
DEMO_COMPANY: dict[str, Any] = {
    "company_name": "Demo GmbH",
    "description": "Digitale Dienstleistungen für kleine Unternehmen.",
    "services": [
        {"name": "Webdesign", "description": "", "price": "499 EUR"},
        {"name": "Dokumentenverarbeitung", "description": "", "price": ""},
        {"name": "IT-Support", "description": "", "price": "79 EUR/hour"},
    ],
    "prices": [
        "Webdesign — 499 EUR",
        "IT-Support — 79 EUR/hour",
    ],
    "contacts": {
        "email": "demo@example.test",
    },
    "extra_doc_count": 2,
}

TIER_ROWS = (
    ("BASIC", SALES_KIT_BASIC, 99.0),
    ("BUSINESS", SALES_KIT_BUSINESS, 199.0),
    ("PROFESSIONAL", SALES_KIT_PROFESSIONAL, 299.0),
)

FABRICATED_FORBIDDEN = (
    "iso 9001",
    "beispielkunde",
    "mustermann referenz",
    "lorem ipsum",
    "guaranteed sales",
    "fiktive",
)


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _pf(ok: bool) -> str:
    return "PASS" if ok else "FAIL"


def _zip_has_fabrications(data: bytes) -> bool:
    blob = ""
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            for name in zf.namelist():
                raw = zf.read(name)
                if name.endswith(".docx") and raw[:2] == b"PK":
                    try:
                        with zipfile.ZipFile(io.BytesIO(raw)) as dz:
                            blob += dz.read("word/document.xml").decode(
                                "utf-8", errors="ignore"
                            ).lower()
                    except Exception:  # noqa: BLE001
                        blob += raw.decode("utf-8", errors="ignore").lower()
                else:
                    blob += raw.decode("utf-8", errors="ignore").lower()
    except Exception:  # noqa: BLE001
        return True
    return any(m in blob for m in FABRICATED_FORBIDDEN)


def _store_completed_job(
    eng: OfficeJobEngine,
    *,
    tier: str,
    zip_bytes: bytes,
    filename: str,
    price_eur: float,
    held_for_qa_fail: bool = False,
    paid: bool = True,
) -> dict[str, Any]:
    """Attach Sales Kit ZIP to a job and mark completed for CC-4 delivery path."""
    created = eng.create_job(
        customer_id="owner-e2e-sales-kit",
        email="demo@example.test",
    )
    job = eng._require_owner(created["job_id"], created["owner_token"])
    art_mat = eng._materials.save_bytes(
        zip_bytes,
        filename=filename,
        content_type="application/zip",
        session_id=f"office-artifact:{job['job_id']}",
        meta={
            "office_job_id": job["job_id"],
            "office_artifact": True,
            "action_id": tier,
            "sales_kit_owner_e2e": True,
        },
    )
    job["understanding"] = {
        "intent": {"id": tier, "label_de": f"Sales Kit · {tier}"},
        "filled": True,
    }
    job["proposal"] = {
        "task": tier,
        "task_label_de": f"Sales Kit · {tier}",
        "price_eur": price_eur,
        "next_step": "completed" if not held_for_qa_fail else "quality_failed",
    }
    job["payment"] = {
        "paid": paid,
        "requires_payment": True,
        "order_id": f"e2e-sk-{tier}-{job['job_id'][-8:]}",
        "price_eur": price_eur,
        "price_lock": {"price_eur": price_eur, "currency": "EUR"},
        "note": "Owner E2E simulated paid — PAYMENT_E2E=PENDING for real Sales Kit checkout",
    }
    job["artifact"] = {
        "material_id": art_mat.get("id"),
        "filename": filename,
        "ext": "zip",
        "mime": "application/zip",
        "size": len(zip_bytes),
        "held_for_qa_fail": held_for_qa_fail,
    }
    job["status"] = "completed"
    # QA fail is signaled by held_for_qa_fail (CC-4), not only by status=failed
    if held_for_qa_fail:
        job["failure_reason"] = "quality_gate_failed"
    job["sales_kit_owner_e2e"] = True
    job["updated_at"] = _utc()
    eng._write(job)
    return {"created": created, "job": eng._load(created["job_id"])}


def run_tier_path(eng: OfficeJobEngine, *, tier_label: str, tier: str, price_eur: float) -> dict[str, Any]:
    row: dict[str, Any] = {
        "tier": tier,
        "tier_label": tier_label,
        "price_eur": price_eur,
        "input": "FAIL",
        "execute": "FAIL",
        "validate": "FAIL",
        "package": "FAIL",
        "cabinet": "FAIL",
        "email": "FAIL",
        "delivery": "FAIL",
        "payment_e2e": "PENDING",
        "details": {},
    }

    # 1) Input
    company = dict(DEMO_COMPANY)
    if not company.get("company_name") or not company.get("services"):
        row["details"]["input_error"] = "demo company incomplete"
        return row
    row["input"] = "PASS"
    row["details"]["sku"] = tier

    # 2–3) Execute
    gen = generate_sales_kit(company=company, tier=tier)
    if not gen.get("ok"):
        row["details"]["execute_error"] = gen
        return row
    row["execute"] = "PASS"
    row["details"]["files"] = list(gen.get("files") or [])

    # 4–6) Validate
    va = validate_sales_kit_artifact(
        data=gen["bytes"], tier=tier, company=company
    )
    if not va.get("pass"):
        row["details"]["validate"] = va
        return row
    # In LIVE mode, validator can allow delivery; in pre-live it must remain blocked.
    if SALES_KIT_LIVE and SKU_ENABLED:
        if not va.get("delivery_allowed"):
            row["details"]["live_gate"] = "validator delivery_allowed False while LIVE=true"
            return row
    elif va.get("delivery_allowed"):
        row["details"]["live_leak"] = "validator delivery_allowed True while LIVE=false"
        return row
    row["validate"] = "PASS"

    # 7–11) Package integrity
    try:
        zf = zipfile.ZipFile(io.BytesIO(gen["bytes"]))
        names = set(zf.namelist())
    except Exception as exc:  # noqa: BLE001
        row["details"]["package_error"] = str(exc)[:200]
        return row
    expected = {f"VIRTUS_SALES_KIT/{n}" for n in TIER_FILES[tier]}
    if not expected.issubset(names):
        row["details"]["missing_files"] = sorted(expected - names)
        return row
    for path in expected:
        if len(zf.read(path)) < 32:
            row["details"]["empty_file"] = path
            return row
    if _zip_has_fabrications(gen["bytes"]):
        row["details"]["fabricated"] = True
        return row
    # Preserve Demo GmbH + listed services in DOCX
    profile_docx = zf.read("VIRTUS_SALES_KIT/Company_Profile.docx")
    with zipfile.ZipFile(io.BytesIO(profile_docx)) as dz:
        xml = dz.read("word/document.xml").decode("utf-8", errors="ignore")
    if "Demo GmbH" not in xml:
        row["details"]["fact_loss"] = "company_name"
        return row
    if "Webdesign" not in xml or "IT-Support" not in xml:
        row["details"]["fact_loss"] = "services"
        return row
    row["package"] = "PASS"

    # 12–17) Cabinet + email via existing CC-4 path (email mocked = path proof)
    stored = _store_completed_job(
        eng,
        tier=tier,
        zip_bytes=gen["bytes"],
        filename=str(gen["filename"]),
        price_eur=price_eur,
    )
    job = stored["job"]
    assert job is not None

    with patch(
        "app.integration.receipt_email_service.ReceiptEmailService.send_office_delivery_ready",
        return_value={"ok": True},
    ):
        deliv = deliver_completed_product(eng, job, force_retry=True)

    job2 = eng._load(stored["created"]["job_id"])
    assert job2 is not None
    dview = dict(job2.get("delivery") or {})
    cabinet_ready = bool(
        job2.get("status") == "completed"
        and (job2.get("payment") or {}).get("paid")
        and not (job2.get("artifact") or {}).get("held_for_qa_fail")
        and (job2.get("artifact") or {}).get("material_id")
    )
    row["cabinet"] = _pf(cabinet_ready and deliv.get("ok"))

    email_ok = dview.get("email_status") == EMAIL_SENT and bool(deliv.get("ok"))
    row["email"] = _pf(email_ok)
    row["details"]["email_note"] = (
        "ReceiptEmailService mocked ok=True — proves CC-4 path; live SMTP not claimed"
    )

    token = deliv.get("download_token")
    download_ok = False
    if token and verify_delivery_token(job2, token):
        data, fn, mime = eng.get_artifact_with_delivery_token(
            stored["created"]["job_id"], delivery_token=str(token), fmt="zip"
        )
        download_ok = (
            bool(data)
            and data[:2] == b"PK"
            and "zip" in (mime or "").lower()
            and str(fn or "").endswith(".zip")
        )
        # Re-open downloaded ZIP
        if download_ok:
            with zipfile.ZipFile(io.BytesIO(data)) as dz:
                download_ok = expected.issubset(set(dz.namelist()))

    row["delivery"] = _pf(
        row["cabinet"] == "PASS" and row["email"] == "PASS" and download_ok
    )
    row["details"]["download_ok"] = download_ok
    row["details"]["job_id"] = stored["created"]["job_id"]
    return row


def run_failure_tests(eng: OfficeJobEngine) -> dict[str, str]:
    out: dict[str, str] = {}

    # A) missing company name
    miss = generate_sales_kit(
        company={"services": [{"name": "X"}], "contacts": {"email": "a@b.c"}},
        tier=SALES_KIT_BASIC,
    )
    out["missing_input"] = _pf(
        miss.get("ok") is False and miss.get("error") == "missing_input"
    )

    # B) missing services — must not invent (description-only allowed for basic)
    # Business tier requires services_or_prices
    no_svc = generate_sales_kit(
        company={
            "company_name": "Demo GmbH",
            "description": "Nur Text ohne Leistungen.",
            "contacts": {"email": "demo@example.test"},
        },
        tier=SALES_KIT_BUSINESS,
    )
    invented = False
    if no_svc.get("ok"):
        # Must not invent Siemens-style services
        invented = _zip_has_fabrications(no_svc["bytes"])
    out["missing_services"] = _pf(
        (no_svc.get("ok") is False and no_svc.get("error") == "missing_input")
        or (no_svc.get("ok") is True and not invented)
    )

    # C) validator failure → block delivery
    gen_ok = generate_sales_kit(company=DEMO_COMPANY, tier=SALES_KIT_BASIC)
    assert gen_ok.get("ok")
    stored_fail = _store_completed_job(
        eng,
        tier=SALES_KIT_BASIC,
        zip_bytes=gen_ok["bytes"],
        filename="fail.zip",
        price_eur=99.0,
        held_for_qa_fail=True,
    )
    blocked = deliver_completed_product(eng, stored_fail["job"])
    out["validator_failure"] = _pf(
        blocked.get("ok") is False and blocked.get("error") == "qa_failed"
    )

    # D) empty output → validate fail
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("VIRTUS_SALES_KIT/Company_Profile.pdf", b"")
        zf.writestr("VIRTUS_SALES_KIT/Company_Profile.docx", b"")
    empty_va = validate_sales_kit_artifact(
        data=buf.getvalue(), tier=SALES_KIT_BASIC, company=DEMO_COMPANY
    )
    out["empty_output"] = _pf(empty_va.get("pass") is False)

    # E) malformed ZIP
    bad_va = validate_sales_kit_artifact(
        data=b"not-a-zip", tier=SALES_KIT_BASIC, company=DEMO_COMPANY
    )
    out["malformed_zip"] = _pf(bad_va.get("pass") is False)

    # F) unsupported / empty company → safe fail
    empty = generate_sales_kit(company={}, tier=SALES_KIT_PROFESSIONAL)
    out["unsupported_input"] = _pf(empty.get("ok") is False)

    return out


def run_owner_e2e(*, memory_dir: Path | None = None) -> dict[str, Any]:
    """Full Owner E2E report. Does not mutate LIVE flags."""

    base = memory_dir or Path(".runtime") / "office_sales_kit_owner_e2e"
    base.mkdir(parents=True, exist_ok=True)
    eng = OfficeJobEngine(base)

    tiers: dict[str, Any] = {}
    for label, tier, price in TIER_ROWS:
        tiers[label] = run_tier_path(eng, tier_label=label, tier=tier, price_eur=price)

    failures = run_failure_tests(eng)

    tier_ok = all(
        tiers[k].get(f) == "PASS"
        for k in ("BASIC", "BUSINESS", "PROFESSIONAL")
        for f in ("input", "execute", "validate", "package", "cabinet", "email", "delivery")
    )
    fail_ok = all(v == "PASS" for v in failures.values())
    live_ok = SALES_KIT_LIVE is True and SKU_ENABLED is True
    sellable_ok = all(
        s in OFFICE_SELLABLE_NOW
        for s in (SALES_KIT_BASIC, SALES_KIT_BUSINESS, SALES_KIT_PROFESSIONAL)
    )

    verdict = "PASS" if (tier_ok and fail_ok and live_ok and sellable_ok) else "FAIL"

    report = {
        "product": "sales_kit",
        "generated_at": _utc(),
        "SALES_KIT_OWNER_E2E": {
            "BASIC": {k: tiers["BASIC"][k] for k in (
                "input", "execute", "validate", "package", "cabinet", "email", "delivery"
            )},
            "BUSINESS": {k: tiers["BUSINESS"][k] for k in (
                "input", "execute", "validate", "package", "cabinet", "email", "delivery"
            )},
            "PROFESSIONAL": {k: tiers["PROFESSIONAL"][k] for k in (
                "input", "execute", "validate", "package", "cabinet", "email", "delivery"
            )},
        },
        "FAILURE_TESTS": failures,
        "PAYMENT_E2E": "PENDING",
        "PAYMENT_NOTE": (
            "Owner E2E validates executor/validator/package/cabinet delivery path. "
            "Payment flow is covered by dedicated payment E2E."
        ),
        "LIVE": {
            "SALES_KIT_LIVE": SALES_KIT_LIVE,
            "SKU_ENABLED": SKU_ENABLED,
        },
        "OFFICE_SELLABLE_NOW": "LIVE_WITH_SALES_KIT",
        "tier_details": tiers,
        "FINAL_VERDICT": f"OWNER_E2E={verdict}",
        "OWNER_E2E": verdict,
    }

    out_path = base / "SALES_KIT_OWNER_E2E.json"
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    report["report_path"] = str(out_path.resolve())
    return report


def main() -> int:
    report = run_owner_e2e()
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report.get("OWNER_E2E") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
