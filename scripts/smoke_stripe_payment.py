"""P-001 Stripe Test Mode smoke — run from repo root.

Phases (stop on first failure):
  1. ENV — keys present, sandbox off when sk_test_ set
  2. API  — GET /api/sales/payment-status (backend must be running)
  3. Checkout — create test order + Stripe Checkout Session URL
  4. Webhook — signed checkout.session.completed → Paid + production

Manual CEO steps (after phase 3 prints checkout URL):
  - Open URL in browser, pay with 4242 4242 4242 4242
  - Or re-run with --order-id ORD... after payment to verify status

Usage:
  py scripts/smoke_stripe_payment.py
  py scripts/smoke_stripe_payment.py --api http://127.0.0.1:8000
  py scripts/smoke_stripe_payment.py --webhook-only --order-id ord-abc123
  py scripts/smoke_stripe_payment.py --verify-order ord-abc123
"""

from __future__ import annotations

import argparse
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


def _ok(msg: str) -> None:
    print(f"  OK  {msg}")


def _fail(msg: str) -> None:
    print(f"  FAIL {msg}")
    raise SystemExit(1)


def _warn(msg: str) -> None:
    print(f"  WARN {msg}")


def _get(url: str) -> tuple[int, dict]:
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            return res.status, json.loads(res.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        try:
            return e.code, json.loads(body)
        except json.JSONDecodeError:
            return e.code, {"detail": body[:300]}


def _post(url: str, payload: dict | None = None, headers: dict | None = None) -> tuple[int, dict]:
    data = None if payload is None else json.dumps(payload).encode()
    hdrs = {"Content-Type": "application/json", "Accept": "application/json"}
    if headers:
        hdrs.update(headers)
    req = urllib.request.Request(url, data=data, headers=hdrs, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            return res.status, json.loads(res.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        try:
            return e.code, json.loads(body)
        except json.JSONDecodeError:
            return e.code, {"detail": body[:300]}


def _stripe_signature(payload: bytes, secret: str) -> str:
    ts = int(time.time())
    signed = f"{ts}.".encode() + payload
    sig = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    return f"t={ts},v1={sig}"


def _env_file_status() -> list[str]:
    backend = BACKEND
    lines: list[str] = []
    for name in (".env", ".env.local"):
        path = backend / name
        if path.is_file():
            stripe_keys = []
            for raw in path.read_text(encoding="utf-8").splitlines():
                line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            if key.startswith("STRIPE_"):
                val = value.strip().strip('"').strip("'")
                if not val:
                    mode = "empty"
                elif val.startswith("sk_live_") or val.startswith("pk_live_"):
                    mode = "live"
                elif val.startswith("sk_test_") or val.startswith("pk_test_"):
                    mode = "test"
                elif val.startswith("whsec_"):
                    mode = "whsec"
                elif key == "STRIPE_PUBLISHABLE_KEY" and val.startswith("pk_live") and not val.startswith("pk_live_"):
                    mode = "fixable_prefix"
                else:
                    mode = "wrong_prefix"
                stripe_keys.append(f"{key}={mode}")
            detail = ", ".join(stripe_keys) if stripe_keys else "no STRIPE_* lines"
            lines.append(f"  found {path.name}: {detail}")
        else:
            lines.append(f"  missing {path.name}")
    return lines


def phase_env() -> None:
    from app.env_loader import load_local_env

    load_local_env()
    sk = os.getenv("STRIPE_SECRET_KEY", "").strip()
    pk = os.getenv("STRIPE_PUBLISHABLE_KEY", "").strip()
    wh = os.getenv("STRIPE_WEBHOOK_SECRET", "").strip()
    sandbox_flag = os.getenv("GENESIS_PAYMENT_SANDBOX", "").strip() == "1"

    print("\n[1/4] ENV")
    for line in _env_file_status():
        print(line)
    if not sk:
        _fail(
            "STRIPE_SECRET_KEY missing — add to dashboard/backend/.env or .env.local "
            "(see dashboard/deploy.env.example)"
        )
    if not sk.startswith("sk_test_"):
        _fail("STRIPE_SECRET_KEY must be sk_test_... for smoke (not live)")
    _ok("STRIPE_SECRET_KEY (test mode)")

    if not pk:
        _warn("STRIPE_PUBLISHABLE_KEY missing — optional for server-side Checkout")
    elif not pk.startswith("pk_test_"):
        _fail("STRIPE_PUBLISHABLE_KEY must be pk_test_...")
    else:
        _ok("STRIPE_PUBLISHABLE_KEY (test mode)")

    if not wh:
        _fail(
            "STRIPE_WEBHOOK_SECRET missing — run: stripe listen --forward-to "
            "localhost:8000/api/webhooks/stripe"
        )
    if not wh.startswith("whsec_"):
        _warn("STRIPE_WEBHOOK_SECRET should start with whsec_")
    else:
        _ok("STRIPE_WEBHOOK_SECRET")

    from app.integration.payment_checkout_service import PaymentCheckoutService

    checkout = PaymentCheckoutService()
    if checkout.provider() != "stripe":
        _fail(f"Expected provider=stripe, got {checkout.provider()!r} (sandbox still active?)")
    if sandbox_flag:
        _warn("GENESIS_PAYMENT_SANDBOX=1 set but ignored because STRIPE_SECRET_KEY wins")
    _ok("Sandbox disabled — Stripe provider active")


def phase_env_live() -> None:
    from app.env_loader import load_local_env

    load_local_env()
    sk = os.getenv("STRIPE_SECRET_KEY", "").strip()
    pk = os.getenv("STRIPE_PUBLISHABLE_KEY", "").strip()
    wh = os.getenv("STRIPE_WEBHOOK_SECRET", "").strip()

    print("\n[Live Keys] ENV")
    for line in _env_file_status():
        print(line)
    if not sk.startswith("sk_live_"):
        _fail("STRIPE_SECRET_KEY must be sk_live_... in .env.local — then restart Genesis")
    _ok("STRIPE_SECRET_KEY (live mode)")
    if not pk.startswith("pk_live_"):
        _fail("STRIPE_PUBLISHABLE_KEY must be pk_live_...")
    _ok("STRIPE_PUBLISHABLE_KEY (live mode)")
    if not wh:
        _fail("STRIPE_WEBHOOK_SECRET missing — add production whsec from Stripe Dashboard")
    _ok("STRIPE_WEBHOOK_SECRET")


def phase_api_live(api: str) -> None:
    print(f"\n[Live Keys] API payment-status ({api})")
    code, body = _get(f"{api.rstrip('/')}/api/sales/payment-status")
    if code != 200:
        _fail(f"payment-status HTTP {code}")
    if not body.get("live_mode"):
        _fail("live_mode=false — restart Genesis after updating .env.local")
    if body.get("stripe_test_mode"):
        _fail("stripe_test_mode=true — backend still on test keys")
    if body.get("provider_label") != "Stripe (live)":
        _fail(f"provider_label={body.get('provider_label')!r} — expected Stripe (live)")
    if not body.get("webhook_configured"):
        _fail("webhook_configured=false")
    _ok("live_mode=true · Stripe (live) · webhook configured")


def phase_api(api: str) -> dict:
    print(f"\n[2/4] API payment-status ({api})")
    code, body = _get(f"{api.rstrip('/')}/api/sales/payment-status")
    if code != 200:
        _fail(f"payment-status HTTP {code}: {body}")
    if not body.get("configured"):
        _fail("payment not configured")
    if body.get("sandbox"):
        _fail("sandbox=true — STRIPE_SECRET_KEY not loaded by running backend")
    if body.get("provider") != "stripe":
        _fail(f"provider={body.get('provider')!r}")
    if not body.get("stripe_test_mode"):
        _fail("stripe_test_mode=false — need sk_test_ on running backend")
    if not body.get("secret_key_configured"):
        _fail("backend does not see STRIPE_SECRET_KEY — restart Genesis after .env")
    if not body.get("webhook_configured"):
        _fail("webhook_configured=false — set STRIPE_WEBHOOK_SECRET and restart")
    _ok(f"{body.get('provider_label')} · webhook configured")
    if not body.get("publishable_key_configured"):
        _warn("publishable_key_configured=false (optional)")
    else:
        _ok("publishable key visible to backend")
    return body


def phase_checkout(api: str) -> str:
    print("\n[3/4] Checkout session")
    code, created = _post(
        f"{api.rstrip('/')}/api/sales/orders",
        {
            "business_name": "Smoke Test GmbH",
            "description": "P-001 Stripe smoke test order",
            "email": "smoke@test.virtus.local",
            "package_id": "basic",
            "city": "Berlin",
        },
    )
    if code != 200 or not created.get("order_id"):
        _fail(f"create order HTTP {code}: {created}")
    order_id = created["order_id"]
    _ok(f"order created {order_id}")

    code, checkout = _post(
        f"{api.rstrip('/')}/api/sales/orders/{order_id}/checkout",
        {
            "success_url": f"http://localhost:3000/order/status/{order_id}",
            "cancel_url": f"http://localhost:3000/order",
        },
    )
    if code != 200:
        _fail(f"checkout HTTP {code}: {checkout}")
    url = str(checkout.get("checkout_url") or "")
    if "checkout.stripe.com" not in url and checkout.get("provider") != "stripe":
        _fail(f"unexpected checkout: {checkout}")
    if "checkout.stripe.com" in url:
        _ok("Stripe Checkout URL (TEST)")
        print(f"\n  -> Open in browser and pay with 4242 4242 4242 4242:\n    {url}\n")
    else:
        _fail(f"not a Stripe URL: {url}")
    return order_id


def phase_webhook(api: str, order_id: str, amount_cents: int = 35000) -> None:
    print(f"\n[4/4] Webhook simulation ({order_id})")
    wh = os.getenv("STRIPE_WEBHOOK_SECRET", "").strip()
    payload = json.dumps(
        {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": f"cs_smoke_{order_id}",
                    "amount_total": amount_cents,
                    "metadata": {"order_id": order_id},
                    "customer_details": {"email": "smoke@test.virtus.local"},
                }
            },
        }
    ).encode()
    sig = _stripe_signature(payload, wh)
    req = urllib.request.Request(
        f"{api.rstrip('/')}/api/webhooks/stripe",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "stripe-signature": sig,
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            code = res.status
            body = json.loads(res.read().decode())
    except urllib.error.HTTPError as e:
        code = e.code
        body = json.loads(e.read().decode(errors="replace") or "{}")

    if code != 200 or not body.get("ok"):
        _fail(f"webhook HTTP {code}: {body}")

    order = body.get("order") or {}
    if order.get("status") not in ("paid", "in_production"):
        _fail(f"order status={order.get('status')!r}")
    if not order.get("paid"):
        _fail("order.paid is false")
    if not body.get("product_id") and not order.get("product_id"):
        _fail("production not started — no product_id")
    _ok("webhook accepted -> Paid -> production started")


def phase_verify_order(api: str, order_id: str) -> None:
    print(f"\n[verify] order status {order_id}")
    code, body = _get(f"{api.rstrip('/')}/api/sales/orders/{order_id}/status")
    if code != 200:
        _fail(f"status HTTP {code}: {body}")
    if not body.get("paid"):
        _fail(f"not paid yet — complete Stripe Checkout first (status={body.get('status')})")
    if body.get("status") not in ("paid", "in_production", "ready", "delivered"):
        _fail(f"unexpected status={body.get('status')!r}")
    _ok(f"status={body.get('status')} · paid=True")
    if body.get("product_id"):
        _ok(f"product_id={body.get('product_id')}")
    code, notes = _get(f"{api.rstrip('/')}/api/owner/notifications")
    if code == 200:
        items = notes.get("notifications") or []
        if any(n.get("order_id") == order_id for n in items):
            _ok("owner notification present")
        else:
            _warn("owner notification not found for this order")


def main() -> None:
    parser = argparse.ArgumentParser(description="P-001 Stripe Test Mode smoke")
    parser.add_argument("--api", default="http://127.0.0.1:8000", help="Backend base URL")
    parser.add_argument("--skip-checkout", action="store_true")
    parser.add_argument("--webhook-only", action="store_true")
    parser.add_argument("--verify-order", metavar="ORDER_ID")
    parser.add_argument("--order-id", metavar="ORDER_ID", help="With --webhook-only")
    parser.add_argument("--env-only", action="store_true")
    parser.add_argument("--check-live", action="store_true", help="P-001 Live Keys gate")
    args = parser.parse_args()

    if args.check_live:
        print("P-001 Live Keys check")
        phase_env_live()
        phase_api_live(args.api)
        print("\nLive Keys PASS — P-001 Live Keys closed; L-001 may open")
        return

    print("P-001 Stripe Test Mode smoke")
    phase_env()
    if args.env_only:
        print("\nSmoke ENV PASS — start backend + stripe listen, then re-run without --env-only")
        return

    if args.verify_order:
        phase_verify_order(args.api, args.verify_order)
        print("\nSmoke VERIFY PASS")
        return

    if args.webhook_only:
        oid = args.order_id
        if not oid:
            _fail("--order-id required with --webhook-only")
        phase_webhook(args.api, oid)
        phase_verify_order(args.api, oid)
        print("\nSmoke WEBHOOK PASS (Simulation — use --verify-order after real card for full smoke)")
        return

    phase_api(args.api)
    order_id = None
    if not args.skip_checkout:
        order_id = phase_checkout(args.api)
        print(
            "After paying with test card, run:\n"
            f"  py scripts/smoke_stripe_payment.py --verify-order {order_id}\n"
            "Or simulate webhook (skips real Stripe payment):\n"
            f"  py scripts/smoke_stripe_payment.py --webhook-only --order-id {order_id}"
        )
        return

    print("\nSmoke API PASS — complete checkout manually, then --verify-order")


if __name__ == "__main__":
    main()
