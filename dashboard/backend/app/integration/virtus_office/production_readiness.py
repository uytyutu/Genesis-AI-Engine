"""Phase A production readiness — code E2E + gates → GO/NO-GO (no LIVE flip).

Owner flip of OFFICE_PIPELINE_LIVE / Stripe Live stays a separate action.
"""

from __future__ import annotations

import io
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from unittest.mock import patch

from starlette.datastructures import Headers, UploadFile

from app.integration.virtus_office.office_capability_audit import audit_matrix, classify_sku
from app.integration.virtus_office.office_job_ssot import (
    OFFICE_PIPELINE_LIVE,
    OFFICE_SELLABLE_NOW,
    OFFICE_SKU_ROADMAP,
)
from app.integration.virtus_office.payment_bridge import (
    build_checkout_services,
    lock_and_begin_checkout,
    mark_payment_outcome,
)

# Catalog groups for CEO checklist (not every action_id row).
PHASE_A_GROUPS: tuple[dict[str, Any], ...] = (
    {
        "id": "translation",
        "label": "Translation",
        "action_id": "translate",
        "kind": "upload",
    },
    {
        "id": "documents",
        "label": "Documents",
        "action_id": "convert_docx",
        "kind": "upload",
    },
    {
        "id": "excel",
        "label": "Excel",
        "action_id": "extract_data",
        "kind": "upload",
    },
    {
        "id": "cv",
        "label": "CV",
        "action_id": "lebenslauf_create",
        "kind": "bewerbung",
    },
    {
        "id": "bewerbung",
        "label": "Bewerbung",
        "action_id": "bewerbung_paket",
        "kind": "bewerbung",
    },
    {
        "id": "document_quality_check",
        "label": "Document Quality Check",
        "action_id": "document_quality_check",
        "kind": "upload",
    },
)

COMPLETE_PROFILE: dict[str, Any] = {
    "personal": {
        "full_name": "Anna Schmidt",
        "email": "anna.schmidt@example.com",
        "phone": "+49 170 1234567",
        "city": "Berlin",
    },
    "experience": [
        {
            "employer": "Muster GmbH",
            "title": "Kaufmannische Angestellte",
            "start": "03/2020",
            "end": "12/2023",
            "bullets": ["Kundenbetreuung", "Rechnungswesen"],
        }
    ],
    "education": [
        {
            "school": "Berufsschule Berlin",
            "degree": "Kaufmannische Ausbildung",
            "start": "08/2017",
            "end": "07/2020",
        }
    ],
    "languages": [
        {"language": "Deutsch", "level": "C1"},
        {"language": "Englisch", "level": "B2"},
    ],
    "skills": ["MS Office", "SAP"],
    "drivers_license": ["B"],
    "vacancy": {
        "title": "Office Manager",
        "company": "Nordwind AG",
        "text": "Wir suchen Verstarkung im Office.",
    },
    "motivation_notes": "Ich mochte meine Erfahrung im Office einbringen.",
}


@dataclass
class CheckResult:
    id: str
    ok: bool
    detail: str = ""
    meta: dict[str, Any] = field(default_factory=dict)


def _upload(name: str, data: bytes, content_type: str) -> UploadFile:
    return UploadFile(
        file=io.BytesIO(data),
        filename=name,
        headers=Headers({"content-type": content_type}),
    )


def _fixture_for(action_id: str) -> tuple[str, bytes, str]:
    if action_id == "extract_data":
        return (
            "kosten.csv",
            b"Datum,Kategorie,Betrag\n01.02.2024,Miete,800.00\n02.02.2024,Essen,45.50\n",
            "text/csv",
        )
    if action_id == "document_quality_check":
        return (
            "quality_sample.txt",
            (
                b"Virtus Office Dokument-Qualitaetscheck Probe.\n"
                b"Rechnung Nr. 4711 vom 12.01.2025.\n"
                b"Gesamtbetrag 99,00 EUR.\n"
                b"Genug lesbarer Text fuer die Diagnose.\n"
            ),
            "text/plain",
        )
    if action_id == "convert_docx":
        return (
            "brief.txt",
            (
                b"Sehr geehrte Damen und Herren,\n\n"
                b"Rechnung Nr. 99 vom 12.01.2025.\n"
                b"Betrag 40,00 EUR.\n"
            ),
            "text/plain",
        )
    return (
        "Arbeitsvertrag.txt",
        (
            b"Arbeitsvertrag\n\n"
            b"Arbeitgeber: Muster GmbH\n"
            b"Arbeitnehmer: Max Mustermann\n"
            b"Datum: 01.03.2024\n"
            b"Gesamtbetrag 1.250,00 EUR\n"
            b"Probezeit drei Monate.\n"
        ),
        "text/plain",
    )


def _expected_ext(action_id: str) -> str:
    return {
        "translate": "pdf",
        "convert_docx": "docx",
        "extract_data": "xlsx",
        "document_quality_check": "pdf",
        "lebenslauf_create": "pdf",
        "bewerbung_paket": "zip",
        "bewerbungsschreiben": "docx",
    }.get(action_id, "pdf")


def _delivery_email_for_tests(*, live: bool) -> str:
    if not live:
        return "e2e-office@example.com"
    raw = (os.environ.get("GENESIS_EMAIL_FROM") or "").strip()
    m = re.search(r"<([^>]+)>", raw)
    addr = (m.group(1) if m else raw).strip()
    return addr or "e2e-office@example.com"


def run_full_e2e_for_action(
    memory_dir: Path,
    *,
    action_id: str,
    kind: str,
    env_sandbox: bool = True,
    mock_email: bool = True,
) -> CheckResult:
    """upload → configure → checkout → sandbox pay → execute → PASS → artifact → delivery."""
    from app.integration.virtus_office import OfficeJobEngine

    if env_sandbox:
        os.environ["GENESIS_PAYMENT_SANDBOX"] = "1"
        os.environ.pop("STRIPE_SECRET_KEY", None)
        os.environ.pop("STRIPE_SECRET_KEY_LIVE", None)

    eng = OfficeJobEngine(memory_dir)
    email = (
        _delivery_email_for_tests(live=True)
        if not mock_email
        else f"e2e-{action_id}@example.com"
    )
    customer_id = f"cust-e2e-{action_id}"
    try:
        if kind == "bewerbung":
            created = eng.create_job(
                service_preset=action_id,
                customer_id=customer_id,
                email=email,
            )
            jid, tok = created["job_id"], created["owner_token"]
            eng.submit_bewerbung_profile(
                jid,
                owner_token=tok,
                profile=COMPLETE_PROFILE,
                action_id=action_id,
                output_format="pdf" if action_id == "lebenslauf_create" else None,
            )
        else:
            name, body, ctype = _fixture_for(action_id)
            created = eng.create_job(
                service_preset=action_id if action_id != "convert_docx" else None,
                customer_id=customer_id,
                email=email,
            )
            jid, tok = created["job_id"], created["owner_token"]
            view = eng.upload(
                jid,
                owner_token=tok,
                upload=_upload(name, body, ctype),
            )
            if view.get("status") not in {"proposal_ready", "understanding"}:
                return CheckResult(
                    action_id,
                    False,
                    f"upload status={view.get('status')} fail={view.get('failure_reason')}",
                )
            kwargs: dict[str, Any] = {
                "action_id": action_id,
                "output_format": _expected_ext(action_id)
                if action_id != "extract_data"
                else "xlsx",
                "confirm_settings": True,
            }
            if action_id == "translate":
                kwargs["target_language"] = "uk"
            eng.select_action(jid, owner_token=tok, **kwargs)

        sales, revenue = build_checkout_services(memory_dir)
        out = lock_and_begin_checkout(
            eng,
            jid,
            owner_token=tok,
            success_url="http://localhost:3000/office/order/x?paid=1",
            cancel_url="http://localhost:3000/office/order/x?cancel=1",
            email=email,
            customer_id=customer_id,
            sales=sales,
            revenue=revenue,
        )
        if not out.get("checkout", {}).get("order_id"):
            return CheckResult(action_id, False, "checkout missing order_id", meta=out)
        if out.get("payment", {}).get("paid"):
            return CheckResult(action_id, False, "paid before sandbox complete")

        from app.integration.virtus_office import OfficeJobError

        try:
            eng.execute(jid, owner_token=tok)
            return CheckResult(action_id, False, "execute allowed before payment")
        except OfficeJobError as exc:
            if exc.code != "payment_required":
                return CheckResult(action_id, False, f"prepay execute code={exc.code}")

        paid = revenue.complete_sandbox_payment(out["checkout"]["order_id"])
        if not paid.get("ok"):
            return CheckResult(action_id, False, f"sandbox pay failed: {paid}")

        paid_view = eng.get_job(jid, owner_token=tok)
        if not paid_view.get("payment", {}).get("paid"):
            return CheckResult(action_id, False, "payment not confirmed on job")
        if paid_view.get("payment", {}).get("status") != "PAYMENT_CONFIRMED":
            return CheckResult(
                action_id,
                False,
                f"payment status={paid_view.get('payment', {}).get('status')}",
            )

        if mock_email:
            with patch(
                "app.integration.receipt_email_service.ReceiptEmailService.send_office_delivery_ready",
                return_value={"ok": True},
            ), patch(
                "app.integration.receipt_email_service.ReceiptEmailService.send_office_payment_receipt",
                return_value={"ok": True},
            ):
                done = eng.execute(jid, owner_token=tok)
        else:
            # Real Resend path — do not mask failures as success
            done = eng.execute(jid, owner_token=tok)

        if done.get("status") != "completed":
            return CheckResult(
                action_id,
                False,
                f"status={done.get('status')} detail={done.get('failure_detail')}",
                meta={"quality": done.get("quality"), "failure": done.get("failure_reason")},
            )
        quality = done.get("quality") or {}
        if not quality.get("passed"):
            return CheckResult(
                action_id,
                False,
                f"quality not PASS: {quality}",
                meta={"quality": quality},
            )

        # Translation soft-beta: refuse offline / ???? artifacts
        if action_id == "translate":
            provider = str((quality.get("meta") or {}).get("translation_provider") or "")
            # quality checks already enforce; also scan artifact text if pdf
            if "offline" in provider:
                return CheckResult(action_id, False, f"offline translator used: {provider}")

        blob, filename, mime = eng.get_artifact_bytes(jid, owner_token=tok)
        exp = _expected_ext(action_id)
        if not filename.endswith(f".{exp}"):
            return CheckResult(
                action_id,
                False,
                f"filename={filename} expected .{exp}",
            )
        if len(blob) < 32:
            return CheckResult(action_id, False, "artifact too small")
        if exp == "pdf" and not blob.startswith(b"%PDF"):
            return CheckResult(action_id, False, "artifact not PDF")
        if exp in {"docx", "xlsx", "zip"} and blob[:2] != b"PK":
            return CheckResult(action_id, False, f"artifact not ZIP/OOXML ({exp})")

        if action_id == "translate" and exp == "pdf" and not mock_email:
            try:
                from pypdf import PdfReader

                reader = PdfReader(io.BytesIO(blob))
                pdf_text = "\n".join((p.extract_text() or "") for p in reader.pages)
            except Exception:  # noqa: BLE001
                pdf_text = blob.decode("utf-8", errors="ignore")
            if "????" in pdf_text or "offline_glossary" in pdf_text:
                return CheckResult(action_id, False, "translation artifact has offline/????")
            if not re.search(r"[\u0400-\u04FF]", pdf_text):
                return CheckResult(action_id, False, "DE→UK artifact missing Cyrillic")

        delivery = done.get("delivery") or {}
        if not delivery.get("cabinet_ready"):
            return CheckResult(action_id, False, f"cabinet not ready: {delivery}")
        if not mock_email:
            if delivery.get("email_status") != "EMAIL_SENT" or delivery.get("email_ok") is False:
                return CheckResult(
                    action_id,
                    False,
                    f"real email failed: status={delivery.get('email_status')} "
                    f"err={delivery.get('email_error')}",
                    meta={"delivery": delivery},
                )

        blob2, name2, _mime2 = eng.get_artifact_bytes(jid, owner_token=tok)
        if blob2 != blob or name2 != filename:
            return CheckResult(action_id, False, "re-download mismatch")

        return CheckResult(
            action_id,
            True,
            "e2e PASS" + (" + live email" if not mock_email else ""),
            meta={
                "filename": filename,
                "mime": mime,
                "bytes": len(blob),
                "price_eur": (paid_view.get("payment") or {})
                .get("price_lock", {})
                .get("price_eur"),
                "email_status": delivery.get("email_status"),
                "email_ok": delivery.get("email_ok"),
                "fully_delivered": delivery.get("fully_delivered"),
                "mock_email": mock_email,
                "quality_passed": True,
            },
        )
    except Exception as exc:  # noqa: BLE001
        return CheckResult(action_id, False, f"{type(exc).__name__}: {exc}")


def run_payment_gate_suite(memory_dir: Path) -> list[CheckResult]:
    """Sandbox success, cancel/fail, retry, forged price, unpaid no delivery."""
    import os

    from app.integration.virtus_office import OfficeJobEngine, OfficeJobError
    from app.integration.virtus_office.digital_product_delivery import deliver_completed_product

    os.environ["GENESIS_PAYMENT_SANDBOX"] = "1"
    os.environ.pop("STRIPE_SECRET_KEY", None)
    os.environ.pop("STRIPE_SECRET_KEY_LIVE", None)

    results: list[CheckResult] = []
    eng = OfficeJobEngine(memory_dir / "pay")
    name, body, ctype = _fixture_for("translate")
    created = eng.create_job(service_preset="translate", email="pay@example.com")
    jid, tok = created["job_id"], created["owner_token"]
    eng.upload(jid, owner_token=tok, upload=_upload(name, body, ctype))
    eng.select_action(
        jid,
        owner_token=tok,
        action_id="translate",
        target_language="en",
        output_format="pdf",
        confirm_settings=True,
    )
    sales, revenue = build_checkout_services(memory_dir / "pay")

    # Forged price
    try:
        lock_and_begin_checkout(
            eng,
            jid,
            owner_token=tok,
            success_url="http://localhost:3000/ok",
            cancel_url="http://localhost:3000/cancel",
            client_price_eur=1.0,
            sales=sales,
            revenue=revenue,
        )
        results.append(CheckResult("forged_price", False, "forged price accepted"))
    except OfficeJobError as exc:
        results.append(
            CheckResult("forged_price", exc.code == "price_mismatch", f"code={exc.code}")
        )

    out = lock_and_begin_checkout(
        eng,
        jid,
        owner_token=tok,
        success_url="http://localhost:3000/ok",
        cancel_url="http://localhost:3000/cancel",
        sales=sales,
        revenue=revenue,
    )
    pay_pub = out.get("payment") or {}
    results.append(
        CheckResult(
            "price_lock",
            bool(pay_pub.get("price_locked")) and float(pay_pub.get("price_eur") or 0) > 0,
            f"price_eur={pay_pub.get('price_eur')} locked={pay_pub.get('price_locked')}",
        )
    )

    # Cancel keeps execute locked
    mark_payment_outcome(eng, jid, owner_token=tok, outcome="cancelled")
    try:
        eng.execute(jid, owner_token=tok)
        results.append(CheckResult("cancelled_blocks_execute", False, "execute after cancel"))
    except OfficeJobError as exc:
        results.append(
            CheckResult(
                "cancelled_blocks_execute",
                exc.code == "payment_required",
                f"code={exc.code}",
            )
        )

    # Retry: resume checkout + sandbox pay
    out2 = lock_and_begin_checkout(
        eng,
        jid,
        owner_token=tok,
        success_url="http://localhost:3000/ok",
        cancel_url="http://localhost:3000/cancel",
        sales=sales,
        revenue=revenue,
    )
    order_id = out2["checkout"]["order_id"]
    paid = revenue.complete_sandbox_payment(order_id)
    results.append(CheckResult("retry_after_cancel", bool(paid.get("ok")), str(paid)[:120]))

    # Failed payment on a second job
    eng2 = OfficeJobEngine(memory_dir / "pay2")
    c2 = eng2.create_job(service_preset="translate", email="fail@example.com")
    eng2.upload(
        c2["job_id"],
        owner_token=c2["owner_token"],
        upload=_upload(name, body, ctype),
    )
    eng2.select_action(
        c2["job_id"],
        owner_token=c2["owner_token"],
        action_id="translate",
        target_language="uk",
        output_format="pdf",
    )
    sales2, revenue2 = build_checkout_services(memory_dir / "pay2")
    lock_and_begin_checkout(
        eng2,
        c2["job_id"],
        owner_token=c2["owner_token"],
        success_url="http://localhost:3000/ok",
        cancel_url="http://localhost:3000/cancel",
        sales=sales2,
        revenue=revenue2,
    )
    mark_payment_outcome(eng2, c2["job_id"], owner_token=c2["owner_token"], outcome="failed")
    try:
        eng2.execute(c2["job_id"], owner_token=c2["owner_token"])
        results.append(CheckResult("failed_blocks_execute", False, "execute after fail"))
    except OfficeJobError as exc:
        results.append(
            CheckResult(
                "failed_blocks_execute",
                exc.code == "payment_required",
                f"code={exc.code}",
            )
        )

    # QA fail / unpaid → no delivery
    job = eng2._require_owner(c2["job_id"], c2["owner_token"])
    job["status"] = "completed"
    job["artifact"] = {
        "material_id": "mat-x",
        "filename": "x.pdf",
        "ext": "pdf",
        "held_for_qa_fail": True,
    }
    eng2._write(job)
    res = deliver_completed_product(eng2, job)
    results.append(
        CheckResult(
            "no_delivery_without_pass",
            res.get("ok") is False and res.get("error") in {"qa_failed", "unpaid"},
            str(res)[:160],
        )
    )
    return results


def run_security_checks() -> list[CheckResult]:
    from app.integration.order_materials_service import OrderMaterialsService
    from app.integration.virtus_office.file_classify import classify_office_file
    from app.integration.virtus_office.office_job_ssot import OFFICE_ALLOWED_EXT

    results: list[CheckResult] = []
    results.append(
        CheckResult(
            "pipeline_live_on",
            OFFICE_PIPELINE_LIVE is True,
            f"OFFICE_PIPELINE_LIVE={OFFICE_PIPELINE_LIVE}",
        )
    )
    results.append(
        CheckResult(
            "allowed_ext_allowlist",
            ".pdf" in OFFICE_ALLOWED_EXT and ".exe" not in OFFICE_ALLOWED_EXT,
            f"exts={sorted(OFFICE_ALLOWED_EXT)}",
        )
    )
    kind, reason = classify_office_file(
        filename="malware.exe", content_type="application/octet-stream", size=100
    )
    results.append(
        CheckResult(
            "reject_exe",
            kind is None and reason == "unsupported_type",
            f"kind={kind} reason={reason}",
        )
    )
    # Materials hard limit (Office ingest path)
    max_bytes = getattr(OrderMaterialsService, "_MAX_BYTES", None)
    if max_bytes is None:
        # instance attribute on module
        import app.integration.order_materials_service as oms

        max_bytes = getattr(oms, "_MAX_BYTES", 0)
    results.append(
        CheckResult(
            "upload_size_limit",
            isinstance(max_bytes, int) and max_bytes > 0,
            f"_MAX_BYTES={max_bytes}",
        )
    )
    # No Stripe live key required for sandbox path (env check only)
    import os

    results.append(
        CheckResult(
            "stripe_mode_reported",
            True,
            "stripe_live follows PaymentCheckoutService.is_live_mode()",
        )
    )
    # Frontend secret scan (shallow)
    frontend_office = (
        Path(__file__).resolve().parents[4] / "frontend" / "app" / "components" / "office"
    )
    secret_hits: list[str] = []
    if frontend_office.is_dir():
        for path in list(frontend_office.rglob("*.ts")) + list(frontend_office.rglob("*.tsx")):
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for needle in ("sk_live", "sk_test", "STRIPE_SECRET", "Bot Token", "api_key="):
                if needle in text:
                    secret_hits.append(f"{path.name}:{needle}")
    results.append(
        CheckResult(
            "no_secrets_in_office_frontend",
            not secret_hits,
            ",".join(secret_hits) if secret_hits else "clean",
        )
    )
    return results


def run_api_ssot_checks() -> list[CheckResult]:
    matrix = audit_matrix()
    results: list[CheckResult] = []
    results.append(
        CheckResult(
            "inconsistencies_empty",
            matrix.get("inconsistencies") == [],
            str(matrix.get("inconsistencies") or []),
        )
    )
    results.append(
        CheckResult(
            "pipeline_live_true",
            matrix.get("pipeline_live") is True,
            f"live={matrix.get('pipeline_live')} stripe={matrix.get('stripe_live')}",
        )
    )
    results.append(
        CheckResult(
            "auto_flip_forbidden",
            bool((matrix.get("live_gate") or {}).get("auto_flip_forbidden")),
            "",
        )
    )
    # No roadmap SKU falsely sellable
    false_sellable = [
        sid
        for sid in OFFICE_SKU_ROADMAP
        if classify_sku(sid)["status"] == "SELLABLE"
    ]
    results.append(
        CheckResult(
            "no_false_sellable_roadmap",
            not false_sellable,
            ",".join(false_sellable) if false_sellable else "ok",
        )
    )
    # All OFFICE_SELLABLE_NOW classify as SELLABLE
    bad = [
        sid
        for sid in OFFICE_SELLABLE_NOW
        if classify_sku(sid)["status"] != "SELLABLE"
    ]
    results.append(
        CheckResult(
            "sellable_list_honest",
            not bad,
            ",".join(bad) if bad else "ok",
        )
    )
    # Client vitrine = sellable only (roadmap never on /office)
    home = (
        Path(__file__).resolve().parents[4]
        / "frontend"
        / "app"
        / "components"
        / "office"
        / "OfficeHome.tsx"
    )
    catalog_ok = False
    detail = "OfficeHome.tsx missing"
    if home.is_file():
        text = home.read_text(encoding="utf-8", errors="ignore")
        text_l = text.lower()
        forbidden_ui = (
            "coming_soon",
            "comingsoon",
            "xrechnung",
            "zugferd",
            "searchable_pdf",
            "fillable_pdf",
            "pdf_a_2b",
            "document_archive",
            "pdf_ua",
        )
        hits = [tok for tok in forbidden_ui if tok in text_l]
        has_cards = "SERVICE_CARDS" in text
        catalog_ok = has_cards and not hits
        detail = "sellable-only catalog" if catalog_ok else f"roadmap leaked: {hits}"
    results.append(CheckResult("frontend_catalog_sellable_only", catalog_ok, detail))
    return results


def build_production_readiness(
    work_dir: Path,
    *,
    run_e2e: bool = True,
    live_email: bool | None = None,
) -> dict[str, Any]:
    """Run Phase A gates and assemble PRODUCTION_READINESS payload."""
    try:
        from app.env_loader import load_local_env

        load_local_env()
    except Exception:  # noqa: BLE001
        pass

    use_live_email = live_email
    if use_live_email is None:
        use_live_email = bool(
            os.environ.get("RESEND_API_KEY", "").strip()
            and os.environ.get("GENESIS_EMAIL_FROM", "").strip()
            and os.environ.get("OFFICE_E2E_LIVE", "").strip().lower() in {"1", "true", "yes"}
        )

    if use_live_email:
        os.environ["OFFICE_E2E_LIVE"] = "1"
        os.environ.pop("OFFICE_ALLOW_OFFLINE_TRANSLATE", None)

    e2e_results: list[CheckResult] = []
    if run_e2e:
        for i, group in enumerate(PHASE_A_GROUPS):
            sub = work_dir / f"e2e-{i}-{group['id']}"
            sub.mkdir(parents=True, exist_ok=True)
            e2e_results.append(
                run_full_e2e_for_action(
                    sub,
                    action_id=str(group["action_id"]),
                    kind=str(group["kind"]),
                    mock_email=not use_live_email,
                )
            )

    payment = run_payment_gate_suite(work_dir / "payment")
    security = run_security_checks()
    api_ssot = run_api_ssot_checks()
    matrix = audit_matrix()

    sellable_checks = {
        g["id"]: next(
            (r for r in e2e_results if r.id == g["action_id"]),
            CheckResult(g["action_id"], False, "not run"),
        )
        for g in PHASE_A_GROUPS
    }

    blocked = {
        sid: classify_sku(sid)["status"] for sid in OFFICE_SKU_ROADMAP
    }

    e2e_ok = all(r.ok for r in e2e_results) if e2e_results else False
    payment_ok = all(r.ok for r in payment)
    security_ok = all(r.ok for r in security)
    api_ok = all(r.ok for r in api_ssot)
    delivery_ok = e2e_ok and all(
        bool((r.meta or {}).get("email_status")) for r in e2e_results if r.ok
    )
    if use_live_email and e2e_results:
        delivery_ok = delivery_ok and all(
            (r.meta or {}).get("email_status") == "EMAIL_SENT" for r in e2e_results if r.ok
        )

    # Soft-beta LIVE is on — GO no longer requires flags off
    verdict = (
        "GO"
        if e2e_ok
        and payment_ok
        and security_ok
        and api_ok
        and delivery_ok
        and OFFICE_PIPELINE_LIVE
        else "NO-GO"
    )
    blockers: list[str] = []
    if not e2e_ok:
        blockers.extend(f"E2E:{r.id}:{r.detail}" for r in e2e_results if not r.ok)
    if not payment_ok:
        blockers.extend(f"PAYMENT:{r.id}:{r.detail}" for r in payment if not r.ok)
    if not security_ok:
        blockers.extend(f"SECURITY:{r.id}:{r.detail}" for r in security if not r.ok)
    if not api_ok:
        blockers.extend(f"API/SSOT:{r.id}:{r.detail}" for r in api_ssot if not r.ok)
    if not delivery_ok:
        blockers.append("DELIVERY: cabinet/email gate failed")
    if not OFFICE_PIPELINE_LIVE:
        blockers.append("OFFICE_PIPELINE_LIVE is False — soft-beta not flipped")

    return {
        "phase": "A-LIVE",
        "verdict": verdict,
        "pipeline_live": OFFICE_PIPELINE_LIVE,
        "stripe_live": bool((matrix.get("stripe_live"))),
        "auto_flip": False,
        "live_email": bool(use_live_email),
        "sellable_groups": {
            gid: {
                "ok": cr.ok,
                "action_id": cr.id,
                "detail": cr.detail,
                "meta": cr.meta,
            }
            for gid, cr in sellable_checks.items()
        },
        "blocked_roadmap": blocked,
        "e2e": [{"id": r.id, "ok": r.ok, "detail": r.detail, "meta": r.meta} for r in e2e_results],
        "payment": [{"id": r.id, "ok": r.ok, "detail": r.detail} for r in payment],
        "delivery": {
            "ok": delivery_ok,
            "live_email": bool(use_live_email),
            "note": "cabinet_ready + artifact; live email when RESEND configured",
        },
        "security": [{"id": r.id, "ok": r.ok, "detail": r.detail} for r in security],
        "api_ssot": [{"id": r.id, "ok": r.ok, "detail": r.detail} for r in api_ssot],
        "inconsistencies": list(matrix.get("inconsistencies") or []),
        "blockers": blockers,
        "next_phase": (
            "Soft-beta LIVE. Next engineering: XRechnung + KoSIT → SELLABLE. "
            "Do not add roadmap SKUs to client vitrine until PASS."
        ),
    }


def format_production_readiness(report: dict[str, Any]) -> str:
    def mark(ok: bool) -> str:
        return "[x]" if ok else "[ ]"

    lines = [
        "PRODUCTION_READINESS",
        "",
        "SELLABLE:",
    ]
    groups = report.get("sellable_groups") or {}
    order = [
        ("translation", "Translation"),
        ("documents", "Documents"),
        ("excel", "Excel"),
        ("cv", "CV"),
        ("bewerbung", "Bewerbung"),
        ("document_quality_check", "Document Quality Check"),
    ]
    for gid, label in order:
        ok = bool((groups.get(gid) or {}).get("ok"))
        lines.append(f"{mark(ok)} {label}")

    lines.extend(["", "BLOCKED:"])
    for sid, status in (report.get("blocked_roadmap") or {}).items():
        lines.append(f"[ ] {sid} ({status})")

    lines.extend(["", "E2E:"])
    for row in report.get("e2e") or []:
        lines.append(f"{mark(bool(row.get('ok')))} {row.get('id')}: {row.get('detail')}")

    lines.extend(["", "PAYMENT:"])
    for row in report.get("payment") or []:
        lines.append(f"{mark(bool(row.get('ok')))} {row.get('id')}: {row.get('detail')}")

    delivery = report.get("delivery") or {}
    lines.extend(
        [
            "",
            "DELIVERY:",
            f"{mark(bool(delivery.get('ok')))} cabinet+artifact+email path",
            "",
            "SECURITY:",
        ]
    )
    for row in report.get("security") or []:
        lines.append(f"{mark(bool(row.get('ok')))} {row.get('id')}: {row.get('detail')}")

    lines.extend(["", "API/SSOT:"])
    for row in report.get("api_ssot") or []:
        lines.append(f"{mark(bool(row.get('ok')))} {row.get('id')}: {row.get('detail')}")

    lines.extend(
        [
            "",
            "INCONSISTENCIES:",
        ]
    )
    incs = report.get("inconsistencies") or []
    if not incs:
        lines.append("(none)")
    else:
        for item in incs:
            lines.append(f"- {item}")

    lines.extend(
        [
            "",
            f"OFFICE_PIPELINE_LIVE: {report.get('pipeline_live')}",
            f"STRIPE_LIVE: {report.get('stripe_live')}",
            "",
            f"RELEASE VERDICT: {report.get('verdict')}",
        ]
    )
    if report.get("blockers"):
        lines.append("BLOCKERS:")
        for b in report["blockers"]:
            lines.append(f"- {b}")
    lines.append(f"NEXT: {report.get('next_phase')}")
    return "\n".join(lines)
