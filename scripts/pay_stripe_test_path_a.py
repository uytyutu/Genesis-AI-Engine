"""Pay Path A across markets in Stripe TEST mode via signed test webhook.

Flow: order → Checkout Session (sk_test_) → signed checkout.session.completed
→ confirm production. No live charges. No forged live payments.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "dashboard" / "backend"
sys.path.insert(0, str(BACKEND))

API = os.getenv("GENESIS_API", "http://127.0.0.1:8000")

CASES = [
    ("DE", "Berlin", "Handwerker Berlin renovierung", "EUR"),
    ("US", "Austin", "Dental clinic Austin", "USD"),
    ("UA", "Kyiv", "Auto service Kyiv", "UAH"),
    ("PL", "Warszawa", "Warsztat samochodowy Warszawa", "PLN"),
    ("PT", "Lisboa", "Oficina auto Lisboa", "EUR"),
    ("RU", "Moscow", "Autoservice Moscow", "EUR"),
    ("GB", "London", "PC repair London", "GBP"),
    ("RO", "Bucuresti", "Service auto Bucuresti", "EUR"),
]


def _req(method: str, path: str, payload: dict | None = None, headers: dict | None = None) -> tuple[int, dict]:
    data = None if payload is None else json.dumps(payload).encode()
    hdrs = {"Content-Type": "application/json", "Accept": "application/json"}
    if headers:
        hdrs.update(headers)
    req = urllib.request.Request(
        f"{API.rstrip('/')}{path}",
        data=data,
        headers=hdrs,
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as res:
            return res.status, json.loads(res.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        try:
            return e.code, json.loads(body)
        except json.JSONDecodeError:
            return e.code, {"detail": body[:400]}


def _stripe_signature(payload: bytes, secret: str) -> str:
    ts = int(time.time())
    signed = f"{ts}.".encode() + payload
    sig = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    return f"t={ts},v1={sig}"


def _pay_via_test_webhook(
    *,
    order_id: str,
    session_id: str,
    amount: float,
    currency: str,
    email: str,
) -> tuple[int, dict]:
    from app.env_loader import load_local_env

    load_local_env()
    wh = os.getenv("STRIPE_WEBHOOK_SECRET", "").strip()
    if not wh:
        return 0, {"detail": "STRIPE_WEBHOOK_SECRET missing"}
    amount_cents = int(round(float(amount) * 100))
    payload = json.dumps(
        {
            "id": f"evt_test_{order_id}",
            "object": "event",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": session_id,
                    "object": "checkout.session",
                    "amount_total": amount_cents,
                    "currency": currency.lower(),
                    "payment_status": "paid",
                    "status": "complete",
                    "metadata": {"order_id": order_id},
                    "customer_details": {"email": email},
                }
            },
        }
    ).encode()
    sig = _stripe_signature(payload, wh)
    return _post_raw("/api/webhooks/stripe", payload, {"stripe-signature": sig})


def _post_raw(path: str, body: bytes, headers: dict) -> tuple[int, dict]:
    hdrs = {"Content-Type": "application/json", "Accept": "application/json", **headers}
    req = urllib.request.Request(
        f"{API.rstrip('/')}{path}",
        data=body,
        headers=hdrs,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as res:
            return res.status, json.loads(res.read().decode())
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors="replace")
        try:
            return e.code, json.loads(raw)
        except json.JSONDecodeError:
            return e.code, {"detail": raw[:400]}


def main() -> int:
    code, pay = _req("GET", "/api/sales/payment-status")
    print("payment-status", pay)
    if code != 200 or pay.get("provider") != "stripe":
        print("FAIL: stripe not configured")
        return 1
    if pay.get("live_mode"):
        print("FAIL: still LIVE — py -3.12 scripts/switch_stripe_mode.py test && restart Genesis")
        return 1

    results = []
    for market, city, desc, expect_cur in CASES:
        row: dict = {"market": market}
        email = f"test-pay-{market.lower()}@virtus.local"
        code, created = _req(
            "POST",
            "/api/sales/orders",
            {
                "business_name": f"Test Pay {market}",
                "description": desc,
                "email": email,
                "city": city,
                "package_id": "basic",
                "market_code": market,
            },
        )
        if code != 200:
            row["stop"] = "order"
            row["detail"] = str(created)[:160]
            results.append(row)
            continue
        oid = created["order_id"]
        row["order_id"] = oid
        row["price_label"] = created.get("price_label")
        row["currency"] = created.get("currency")
        row["amount"] = created.get("price_eur")
        if str(created.get("currency") or "").upper() != expect_cur:
            row["stop"] = "currency"
            results.append(row)
            continue

        code, checkout = _req(
            "POST",
            f"/api/sales/orders/{oid}/checkout",
            {
                "success_url": f"http://localhost:3000/order/status/{oid}",
                "cancel_url": "http://localhost:3000/order",
            },
        )
        if code != 200:
            row["stop"] = "checkout"
            row["detail"] = str(checkout)[:160]
            results.append(row)
            continue
        sid = str(checkout.get("session_id") or "")
        row["session_id"] = sid
        if "cs_test_" not in sid and not sid.startswith("cs_test"):
            # accept cs_test_... 
            if not sid.startswith("cs_"):
                row["stop"] = "bad_session"
                results.append(row)
                continue

        wh_code, wh_body = _pay_via_test_webhook(
            order_id=oid,
            session_id=sid,
            amount=float(created["price_eur"]),
            currency=str(created.get("currency") or expect_cur),
            email=email,
        )
        row["webhook_http"] = wh_code
        if wh_code != 200 or not wh_body.get("ok"):
            row["stop"] = "webhook"
            row["detail"] = str(wh_body)[:220]
            results.append(row)
            continue

        code2, status = _req("GET", f"/api/sales/orders/{oid}/status")
        st = status if code2 == 200 else {}
        row["final_status"] = st.get("status")
        row["final_paid"] = st.get("paid")
        row["product_id"] = st.get("product_id")
        if st.get("paid") and st.get("status") in (
            "paid",
            "in_production",
            "ready",
            "delivered",
        ):
            row["pass"] = True
        else:
            row["stop"] = "no_deliverable_state"
            row["detail"] = str(st)[:200]
        results.append(row)

    print("\n=== RESULTS ===")
    fails = []
    for r in results:
        mark = "PASS" if r.get("pass") else f"STOP:{r.get('stop')}"
        print(
            f"  {r['market']}: {mark} {r.get('price_label')} "
            f"status={r.get('final_status')} paid={r.get('final_paid')} "
            f"product={r.get('product_id')} {r.get('detail', '')}"
        )
        if not r.get("pass"):
            fails.append(r)
    print(f"\nSUMMARY {len(results) - len(fails)}/{len(results)} PASS")
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(main())
