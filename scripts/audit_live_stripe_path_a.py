"""Live Path A probe — stack must be running. Does NOT fake webhooks or mark unpaid as paid.

Creates real Stripe Checkout Sessions and verifies currency/amount via Stripe retrieve.
No card charge unless a human pays the URL.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "dashboard" / "backend"
sys.path.insert(0, str(BACKEND))

API = os.getenv("GENESIS_API", "http://127.0.0.1:8000")

# Sample of Mission 1 markets — currency must match country.
CASES = [
    ("DE", "Berlin", "Handwerker renovierung Berlin", "EUR"),
    ("US", "Austin", "Dental clinic Austin", "USD"),
    ("UA", "Kyiv", "СТО автосервіс Київ", "UAH"),
    ("PL", "Warszawa", "Warsztat samochodowy Warszawa", "PLN"),
    ("PT", "Lisboa", "Oficina auto Lisboa", "EUR"),
    ("RU", "Moscow", "Автосервис Москва", "EUR"),
    ("GB", "London", "PC repair London", "GBP"),
    ("RO", "București", "Service auto Bucuresti", "EUR"),
]


def _req(method: str, path: str, payload: dict | None = None) -> tuple[int, dict]:
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{API.rstrip('/')}{path}",
        data=data,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as res:
            return res.status, json.loads(res.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        try:
            return e.code, json.loads(body)
        except json.JSONDecodeError:
            return e.code, {"detail": body[:400]}


def _stripe_get_session(session_id: str) -> dict | None:
    from app.env_loader import load_local_env

    load_local_env()
    secret = os.getenv("STRIPE_SECRET_KEY", "").strip()
    if not secret or not session_id:
        return None
    import httpx

    with httpx.Client(timeout=30.0) as client:
        res = client.get(
            f"https://api.stripe.com/v1/checkout/sessions/{session_id}",
            auth=(secret, ""),
        )
    if res.status_code >= 400:
        return {"error": res.text[:200], "status": res.status_code}
    return res.json()


def main() -> int:
    print("=== LIVE STACK / STRIPE (no forged payment) ===")
    code, pay = _req("GET", "/api/sales/payment-status")
    if code != 200:
        print(f"FAIL payment-status HTTP {code}")
        return 1
    print(
        f"  provider={pay.get('provider')} live={pay.get('live_mode')} "
        f"label={pay.get('provider_label')} webhook={pay.get('webhook_configured')}"
    )
    if pay.get("provider") != "stripe" or not pay.get("live_mode"):
        print("FAIL: need Stripe live on running backend")
        return 1
    if not pay.get("webhook_configured"):
        print("WARN: webhook_configured=false — paid → production may stall until webhook works")

    code, st = _req("GET", "/api/status")
    print(f"  api status={code} commit={(st.get('git_commit') if code == 200 else '?')}")

    results = []
    for market, city, desc, expect_cur in CASES:
        row: dict = {"market": market, "expect": expect_cur}
        # Packages surface (client-visible price)
        qs = urllib.parse.urlencode({"market": market, "city": city})
        code, pkgs = _req("GET", f"/api/sales/packages?{qs}")
        if code != 200:
            row["stop"] = "packages_http"
            row["detail"] = str(pkgs)[:120]
            results.append(row)
            continue
        row["pkg_currency"] = pkgs.get("currency")
        row["pkg_symbol"] = pkgs.get("symbol")
        row["pkg_market"] = pkgs.get("market_code")
        basic = next((p for p in pkgs.get("packages") or [] if p.get("id") == "basic"), None)
        if not basic:
            row["stop"] = "no_basic_package"
            results.append(row)
            continue
        row["price_label"] = basic.get("price_label") or f"{basic.get('price_eur')} {pkgs.get('symbol')}"
        row["amount"] = basic.get("price_eur")

        if str(pkgs.get("currency") or "").upper() != expect_cur:
            row["stop"] = "packages_currency"
            row["detail"] = f"got={pkgs.get('currency')}"
            results.append(row)
            continue
        if pkgs.get("market_code") != market:
            row["stop"] = "packages_market"
            row["detail"] = f"got={pkgs.get('market_code')}"
            results.append(row)
            continue

        # Order
        code, created = _req(
            "POST",
            "/api/sales/orders",
            {
                "business_name": f"Live Probe {market}",
                "description": desc,
                "email": f"live-probe-{market.lower()}@virtus.local",
                "city": city,
                "package_id": "basic",
                "market_code": market,
            },
        )
        if code != 200 or not created.get("order_id"):
            row["stop"] = "order_create"
            row["detail"] = str(created)[:160]
            results.append(row)
            continue
        oid = created["order_id"]
        row["order_id"] = oid
        row["order_currency"] = created.get("currency")
        row["order_market"] = created.get("market_code")
        row["order_price"] = created.get("price_eur")
        row["order_label"] = created.get("price_label")

        if str(created.get("currency") or "").upper() != expect_cur:
            row["stop"] = "order_currency"
            results.append(row)
            continue
        if created.get("market_code") != market:
            row["stop"] = "order_market"
            results.append(row)
            continue

        # Checkout session (real Stripe — unpaid)
        code, checkout = _req(
            "POST",
            f"/api/sales/orders/{oid}/checkout",
            {
                "success_url": f"http://localhost:3000/order/status/{oid}",
                "cancel_url": "http://localhost:3000/order",
            },
        )
        if code != 200:
            row["stop"] = "checkout_http"
            row["detail"] = str(checkout)[:200]
            results.append(row)
            continue
        url = str(checkout.get("checkout_url") or "")
        sid = str(checkout.get("session_id") or "")
        row["session_id"] = sid
        row["checkout_url"] = url[:70] + ("…" if len(url) > 70 else "")
        if "checkout.stripe.com" not in url:
            row["stop"] = "not_stripe_url"
            row["detail"] = url[:120]
            results.append(row)
            continue

        session = _stripe_get_session(sid)
        if not session or session.get("error"):
            row["stop"] = "stripe_retrieve"
            row["detail"] = str(session)[:160]
            results.append(row)
            continue

        scurrency = str(session.get("currency") or "").upper()
        amount_total = int(session.get("amount_total") or 0)
        expected_minor = int(round(float(created["price_eur"]) * 100))
        row["stripe_currency"] = scurrency
        row["stripe_amount_total"] = amount_total
        row["payment_status"] = session.get("payment_status")
        meta_oid = (session.get("metadata") or {}).get("order_id")
        row["stripe_meta_order"] = meta_oid

        if scurrency != expect_cur:
            row["stop"] = "stripe_currency_mismatch"
        elif amount_total != expected_minor:
            row["stop"] = "stripe_amount_mismatch"
            row["detail"] = f"stripe={amount_total} expected_minor={expected_minor}"
        elif meta_oid != oid:
            row["stop"] = "stripe_metadata_order"
        elif session.get("payment_status") == "paid":
            # Should be unpaid — we did not charge
            row["stop"] = "unexpected_already_paid"
        else:
            row["pass"] = True
            row["note"] = "session_ok_unpaid_awaiting_real_card"
        results.append(row)

    print("\n=== RESULTS ===")
    fails = []
    for r in results:
        mark = "PASS" if r.get("pass") else f"STOP:{r.get('stop')}"
        print(
            f"  {r['market']}: {mark} "
            f"label={r.get('order_label') or r.get('price_label')} "
            f"order={r.get('order_currency')}/{r.get('order_price')} "
            f"stripe={r.get('stripe_currency')}/{r.get('stripe_amount_total')} "
            f"pay_status={r.get('payment_status')} "
            f"{r.get('detail', '')}"
        )
        if r.get("checkout_url") and r.get("pass"):
            print(f"    checkout: {r.get('checkout_url')}")
        if not r.get("pass"):
            fails.append(r)

    print("\n=== SUMMARY ===")
    print(f"  Live checkout probes: {len(results) - len(fails)}/{len(results)} PASS")
    print(
        "  Policy: no forged webhook · no mark-paid without Stripe payment_status=paid"
    )
    print(
        "  Next human step: open one checkout URL, pay for real, confirm "
        "/order/status shows in_production + HTML deliverable"
    )
    if fails:
        print("  Stops:")
        for r in fails:
            print(f"    - {r['market']}: {r.get('stop')} {r.get('detail')}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
