"""Final Conversion Audit — 5 buyer scenarios against live Path A API."""

from __future__ import annotations

import io
import json
import sys
import zipfile
from pathlib import Path
from urllib import error, request

API = "http://127.0.0.1:8000"
BASE = Path(__file__).resolve().parents[1] / "dashboard" / "backend"


def req(method: str, path: str, *, data=None, files=None):
    url = API + path
    if files:
        boundary = "----BoundaryAudit7"
        body = b""
        for name, (filename, content, ctype) in files.items():
            body += f"--{boundary}\r\n".encode()
            body += (
                f'Content-Disposition: form-data; name="{name}"; '
                f'filename="{filename}"\r\n'
            ).encode()
            body += f"Content-Type: {ctype}\r\n\r\n".encode()
            body += content + b"\r\n"
        body += f"--{boundary}--\r\n".encode()
        headers = {"Content-Type": f"multipart/form-data; boundary={boundary}"}
        http_req = request.Request(url, data=body, headers=headers, method=method)
    else:
        headers = {"Content-Type": "application/json"}
        raw = None if data is None else json.dumps(data).encode()
        http_req = request.Request(url, data=raw, headers=headers, method=method)
    try:
        with request.urlopen(http_req, timeout=90) as resp:
            return resp.status, json.loads(resp.read().decode() or "{}")
    except error.HTTPError as e:
        raw_body = e.read().decode(errors="replace")
        try:
            payload = json.loads(raw_body) if raw_body else {"detail": str(e)}
        except json.JSONDecodeError:
            payload = {"detail": raw_body or str(e)}
        return e.code, payload
    except Exception as e:  # noqa: BLE001
        return 0, {"detail": str(e)}


def upload(filename: str, content: bytes, ctype: str):
    return req(
        "POST",
        "/api/sales/order-materials?session_id=conversion-audit",
        files={"file": (filename, content, ctype)},
    )


def make_png() -> bytes:
    return (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00"
        b"\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
    )


def make_pdf() -> bytes:
    return b"""%PDF-1.4
1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj
2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1 >>endobj
3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 144] /Contents 4 0 R /Resources<< /Font<< /F1 5 0 R >> >> >>endobj
4 0 obj<< /Length 68 >>stream
BT /F1 12 Tf 20 100 Td (Kontakt hello@audit.de Tel +49 221 555) Tj ET
endstream
endobj
5 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000266 00000 n 
0000000385 00000 n 
trailer<< /Size 6 /Root 1 0 R >>
startxref
462
%%EOF
"""


def make_xlsx_like() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("[Content_Types].xml", "<Types></Types>")
        z.writestr("xl/workbook.xml", "<workbook/>")
    return buf.getvalue()


def checks_honest(checks: list) -> tuple[bool, str]:
    for c in checks or []:
        if c.get("found") is False:
            return False, f"false check leaked: {c}"
        label = (c.get("label_de") or "").lower()
        if "vollständig analysiert" in label or "alle dateien analysiert" in label:
            return False, f"overclaim: {label}"
    return True, "ok"


def checkout_reachable(order_id: str) -> tuple[bool, str]:
    status, body = req(
        "POST",
        f"/api/sales/orders/{order_id}/checkout",
        data={
            "success_url": "http://127.0.0.1:3000/order?paid=1",
            "cancel_url": "http://127.0.0.1:3000/order?cancel=1",
        },
    )
    if status == 200 and (body.get("checkout_url") or body.get("url")):
        return True, body.get("checkout_url") or body.get("url") or ""
    if status == 200 and body.get("ok"):
        return True, json.dumps(body)[:160]
    return False, f"checkout HTTP {status}: {body}"


def get_order_from_memory(order_id: str) -> dict | None:
    candidates = [
        BASE / "app" / "memory" / "sales_orders.json",
        BASE / "memory" / "sales_orders.json",
    ]
    for p in candidates:
        if not p.is_file():
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        orders = data if isinstance(data, list) else data.get("orders") or []
        for o in orders:
            if o.get("order_id") == order_id:
                return o
    return None


def main() -> int:
    results: list[tuple[str, bool, list[str]]] = []

    print("payment-status check…")
    st, pay = req("GET", "/api/sales/payment-status")
    print("payment", st, pay.get("configured"), pay.get("provider"))
    if st != 200 or not pay.get("configured"):
        print("FATAL: payment not configured — Bezahlen path blocked")
        return 2

    scenarios = [
        {
            "name": "A_nothing",
            "payload": {
                "business_name": "Idee Café",
                "description": "Neue Café-Idee in Köln, noch ohne Online-Präsenz",
                "email": "audit-a@example.de",
                "package_id": "basic",
                "domain_status": "none",
                "city": "Köln",
            },
            "files": [],
        },
        {
            "name": "B_domain_only",
            "payload": {
                "business_name": "Domain Only GmbH",
                "description": "Handwerk, Domain vorhanden",
                "email": "audit-b@example.de",
                "package_id": "basic",
                "domain_status": "have_domain",
                "existing_domain": "domain-only-audit.de",
                "city": "Düsseldorf",
            },
            "files": [],
        },
        {
            "name": "C_site_instagram",
            "payload": {
                "business_name": "Site Insta Shop",
                "description": "Mode-Boutique mit bestehender Website",
                "email": "audit-c@example.de",
                "package_id": "business",
                "domain_status": "have_domain",
                "existing_domain": "example.com",
                "company_website": "https://example.com",
                "instagram": "https://instagram.com/audit_demo",
                "city": "Berlin",
            },
            "files": [],
        },
        {
            "name": "D_pdf_logo",
            "payload": {
                "business_name": "PDF Logo Praxis",
                "description": "Zahnarztpraxis mit Flyer und Logo",
                "email": "audit-d@example.de",
                "package_id": "basic",
                "domain_status": "need_help",
                "needs_logo": True,
                "city": "München",
            },
            "files": [
                ("logo.png", make_png(), "image/png"),
                ("flyer.pdf", make_pdf(), "application/pdf"),
            ],
        },
        {
            "name": "E_full_pack",
            "payload": {
                "business_name": "Full Pack Autohaus",
                "description": "Autohaus mit Website, Preislisten und Fotos",
                "email": "audit-e@example.de",
                "package_id": "premium",
                "domain_status": "have_domain",
                "existing_domain": "example.org",
                "company_website": "https://example.org",
                "google_business": "https://maps.google.com/?cid=audit",
                "city": "Hamburg",
            },
            "files": [
                ("logo.png", make_png(), "image/png"),
                ("info.pdf", make_pdf(), "application/pdf"),
                (
                    "preisliste.xlsx",
                    make_xlsx_like(),
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                ),
                ("foto.jpg", make_png(), "image/jpeg"),
            ],
        },
    ]

    for sc in scenarios:
        name = sc["name"]
        fails: list[str] = []
        material_ids: list[str] = []

        for fname, content, ctype in sc["files"]:
            ust, ubody = upload(fname, content, ctype)
            if ust != 200 or not ubody.get("id"):
                fails.append(f"upload {fname}: HTTP {ust} {ubody}")
            else:
                material_ids.append(ubody["id"])
                if not ubody.get("status_de"):
                    fails.append(f"upload {fname}: missing status_de")

        payload = dict(sc["payload"])
        payload["material_ids"] = material_ids

        insight_body = {
            "company_website": payload.get("company_website"),
            "domain_status": payload.get("domain_status"),
            "existing_domain": payload.get("existing_domain"),
            "instagram": payload.get("instagram"),
            "google_business": payload.get("google_business"),
            "material_ids": material_ids,
        }
        ist, ibody = req("POST", "/api/sales/order-insights-preview", data=insight_body)
        if ist != 200:
            fails.append(f"insights-preview: HTTP {ist} {ibody}")
        else:
            checks = ibody.get("checks") or []
            okc, why = checks_honest(checks)
            if not okc:
                fails.append(f"insights honesty: {why}")
            labels = " | ".join(c.get("label_de") or "" for c in checks)
            if name == "A_nothing":
                if "Domain später" not in labels and "Hilfe bei Domain" not in labels:
                    fails.append(f"A expected domain note, got: {labels[:200]}")
            if name == "B_domain_only":
                if "Domain vorhanden" not in labels:
                    fails.append(f"B expected Domain vorhanden, got: {labels[:200]}")
                if any(x in labels.lower() for x in ["kaufen", "jetzt bestellen domain"]):
                    fails.append("B forced domain purchase language")
            if name == "C_site_instagram":
                if "Instagram" not in labels:
                    fails.append(f"C Instagram missing in insights: {labels[:200]}")
                if (
                    "Website" not in labels
                    and "gescannt" not in labels.lower()
                    and "gespeichert" not in labels.lower()
                ):
                    fails.append(f"C no website finding: {labels[:200]}")
            if name == "D_pdf_logo":
                if not material_ids:
                    fails.append("D no materials uploaded")
                if not any(
                    k in labels.lower() for k in ["bild", "logo", "pdf", "datei", "e-mail"]
                ):
                    fails.append(f"D expected material findings: {labels[:200]}")
            if name == "E_full_pack":
                if len(material_ids) < 4:
                    fails.append(f"E expected 4 uploads, got {len(material_ids)}")
                if "Google Business" not in labels:
                    fails.append(f"E Google Business missing: {labels[:200]}")

        cst, cbody = req("POST", "/api/sales/orders", data=payload)
        if cst != 200 or not cbody.get("order_id"):
            fails.append(f"create order: HTTP {cst} {cbody}")
            results.append((name, False, fails))
            print(f"\n=== {name} === FAIL")
            for f in fails:
                print(" -", f)
            continue

        order_id = cbody["order_id"]
        bi = cbody.get("buyer_insights") or {}
        okc, why = checks_honest(bi.get("checks") or [])
        if not okc:
            fails.append(f"order insights honesty: {why}")

        order = get_order_from_memory(order_id)
        if not order:
            fails.append("order not found in sales_orders.json workspace")
        else:
            ws = order.get("project_workspace") or {}
            mats = (order.get("materials") or {}).get("files") or ws.get("materials") or []
            if material_ids and len(mats) < len(material_ids):
                fails.append(
                    f"workspace materials {len(mats)} < uploaded {len(material_ids)}"
                )
            if (
                order.get("domain_status") == "have_domain"
                and order.get("needs_domain")
                and name == "B_domain_only"
            ):
                fails.append("B needs_domain true despite have_domain")
            if name == "B_domain_only" and order.get("existing_domain") != "domain-only-audit.de":
                fails.append("B existing_domain not stored")
            if name == "C_site_instagram":
                social = order.get("social_links") or {}
                if not social.get("instagram"):
                    fails.append("C instagram not in social_links")

        ok_pay, pay_detail = checkout_reachable(order_id)
        if not ok_pay:
            fails.append(f"Bezahlen/checkout: {pay_detail}")

        results.append((name, len(fails) == 0, fails))
        print(f"\n=== {name} === {'PASS' if not fails else 'FAIL'}")
        if fails:
            for f in fails:
                print(" -", f)
        else:
            n_checks = len((cbody.get("buyer_insights") or {}).get("checks") or [])
            print(
                f" order={order_id} materials={len(material_ids)} checks={n_checks}"
            )

    print("\n======= SUMMARY =======")
    all_pass = True
    for name, ok, fails in results:
        print(f"{name}: {'PASS' if ok else 'FAIL'}")
        if not ok:
            all_pass = False
            for f in fails:
                print(f"  FAIL detail: {f}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
