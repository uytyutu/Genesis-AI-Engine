"""CEO Stripe live smoke — €1 Checkout Session.

Requires Railway/backend:
  GENESIS_STRIPE_SMOKE=1
  STRIPE_SECRET_KEY=sk_live_...

Usage (from repo root):
  py scripts/smoke_stripe_1eur.py
  py scripts/smoke_stripe_1eur.py --api https://renewed-reprieve-production.up.railway.app

Opens nothing — prints checkout.stripe.com URL. Pay €1 with a real card, then
check /order/status/{id} and Money Monitor.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request


def _post(url: str, body: dict) -> tuple[int, dict]:
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as res:
            raw = res.read().decode("utf-8")
            return res.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            payload = {"detail": raw[:400]}
        return exc.code, payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Stripe €1 live smoke checkout")
    parser.add_argument(
        "--api",
        default="https://renewed-reprieve-production.up.railway.app",
        help="Backend API base (no trailing slash)",
    )
    parser.add_argument(
        "--site",
        default="https://beta.genesis-ai-engine.com",
        help="Storefront origin for success/cancel URLs",
    )
    args = parser.parse_args()
    api = args.api.rstrip("/")
    site = args.site.rstrip("/")

    code, order = _post(
        f"{api}/api/sales/orders",
        {
            "business_name": "Stripe Smoke €1",
            "description": "CEO Path A smoke — 1 EUR live Stripe verification",
            "email": "ceo.patha.test@genesis-ai-engine.com",
            "package_id": "smoke",
            "city": "Berlin",
            "market_code": "DE",
            "phone": "+491711112233",
        },
    )
    if code >= 400:
        print(f"FAIL create order HTTP {code}: {order}")
        if code == 400 and "smoke" in str(order).lower():
            print("Hint: set GENESIS_STRIPE_SMOKE=1 on Railway and redeploy.")
        return 1

    order_id = order.get("order_id") or (order.get("order") or {}).get("order_id")
    price = order.get("price_eur") or (order.get("order") or {}).get("price_eur")
    currency = order.get("currency") or (order.get("order") or {}).get("currency")
    if not order_id:
        print(f"FAIL no order_id: {order}")
        return 1
    if float(price or 0) != 1.0 or str(currency or "").upper() != "EUR":
        print(f"FAIL expected 1 EUR, got price={price} currency={currency}")
        return 1

    print(f"OK  order {order_id} · {price} {currency}")

    code, checkout = _post(
        f"{api}/api/sales/orders/{order_id}/checkout",
        {
            "success_url": f"{site}/order/status/{order_id}?paid=1",
            "cancel_url": f"{site}/order/status/{order_id}",
        },
    )
    if code >= 400:
        print(f"FAIL checkout HTTP {code}: {checkout}")
        return 1

    url = str(checkout.get("checkout_url") or "")
    if not url.startswith("https://checkout.stripe.com/"):
        print(f"FAIL unexpected checkout_url: {url[:120]}")
        return 1

    print("OK  Stripe Checkout (live €1)")
    print()
    print(url)
    print()
    print(f"After pay → {site}/order/status/{order_id}?paid=1")
    return 0


if __name__ == "__main__":
    sys.exit(main())
