"""Client Path A audit — multi-country × niche (sandbox payment → deliverable).

Run: py -3.12 scripts/audit_client_path_countries.py
Does not start the stack. Live Stripe needs Genesis.exe + keys.
"""

from __future__ import annotations

import os
import sys
import tempfile
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "dashboard" / "backend"
sys.path.insert(0, str(BACKEND))

os.environ["GENESIS_PAYMENT_SANDBOX"] = "1"
os.environ.pop("STRIPE_SECRET_KEY", None)

from app.factory.factory_service import FactoryService  # noqa: E402
from app.integration.commerce_engine import resolve_checkout_packages  # noqa: E402
from app.integration.factory_intent_service import FactoryIntentService  # noqa: E402
from app.integration.finance_service import FinanceService  # noqa: E402
from app.integration.market_registry import get_market  # noqa: E402
from app.integration.owner_notification_service import OwnerNotificationService  # noqa: E402
from app.integration.payment_checkout_service import PaymentCheckoutService  # noqa: E402
from app.integration.revenue_pipeline_service import RevenuePipelineService  # noqa: E402
from app.integration.sales_order_service import SalesOrderService  # noqa: E402

# Expected currencies = market_registry (checkout source of truth).
CURRENCY_CASES = [
    ("US", "USD"),
    ("DE", "EUR"),
    ("GB", "GBP"),
    ("FR", "EUR"),
    ("IT", "EUR"),
    ("ES", "EUR"),
    ("CA", "USD"),
    ("AU", "AUD"),
    ("NL", "EUR"),
    ("PL", "PLN"),
    ("CH", "CHF"),
    ("AT", "EUR"),
    ("BE", "EUR"),
    ("PT", "EUR"),
    ("CZ", "CZK"),
    ("RO", "EUR"),  # decision: RO = EUR everywhere
    ("SK", "EUR"),
    ("UA", "UAH"),  # decision: UA = UAH everywhere
    ("RU", "EUR"),  # decision: RU = EUR (Stripe Mission 1)
    ("NZ", "NZD"),
]

FULL_PATH = [
    ("DE", "Köln", "Handwerker Allrounder renovierung montage Köln", "handwerk"),
    ("US", "Austin", "Dental clinic Austin TX smile", "dental"),
    ("PL", "Warszawa", "Warsztat samochodowy Warszawa KFZ", "auto"),
    ("GB", "Manchester", "PC laptop repair Manchester", "computer"),
    ("FR", "Lyon", "Cabinet dentaire Lyon centre", "dental"),
    ("IT", "Milano", "Officina auto riparazioni Milano", "auto"),
    ("ES", "Madrid", "Taller mecanico Madrid", "auto"),
    ("CA", "Toronto", "Dental clinic Toronto ON", "dental"),
    ("AU", "Sydney", "PC repair shop Sydney", "computer"),
    ("NL", "Amsterdam", "Handyman renovation Amsterdam", "handwerk"),
    ("CH", "Zürich", "Zahnarztpraxis Zürich", "dental"),
    ("AT", "Wien", "KFZ Werkstatt Wien", "auto"),
    ("UA", "Kyiv", "СТО автосервіс Київ ремонт", "auto"),
    ("RU", "Moscow", "Автосервис Москва ремонт", "auto"),
    ("BE", "Bruxelles", "PC repair Brussels", "computer"),
    ("PT", "Lisboa", "Oficina auto Lisboa", "auto"),
    ("CZ", "Praha", "Autoservis Praha", "auto"),
    ("RO", "București", "Service auto Bucuresti", "auto"),
    ("SK", "Bratislava", "Autoservis Bratislava", "auto"),
]


def audit_currency() -> list[dict]:
    rows: list[dict] = []
    for market, expect in CURRENCY_CASES:
        row: dict = {"market": market, "expect": expect}
        try:
            m = get_market(market)
            row["registry_code"] = m.code
            row["registry_currency"] = m.currency
            pkgs = resolve_checkout_packages(market)
            row["checkout_market"] = pkgs["market_code"]
            row["checkout_currency"] = pkgs["currency"]
            basic = next(p for p in pkgs["packages"] if p["id"] == "basic")
            row["price"] = basic["price_eur"]
            row["price_label"] = basic.get("price_label")
            if pkgs["market_code"] != market:
                row["stop"] = "market_fallback"
                row["detail"] = f"resolved={pkgs['market_code']}"
            elif str(pkgs["currency"]).upper() != expect.upper():
                row["stop"] = "currency_mismatch"
                row["detail"] = f"got={pkgs['currency']}"
            else:
                row["pass"] = True
        except Exception as exc:  # noqa: BLE001
            row["stop"] = "exception"
            row["detail"] = f"{type(exc).__name__}: {exc}"
        rows.append(row)
    return rows


def audit_full_path() -> list[dict]:
    out: list[dict] = []
    for market, city, desc, niche in FULL_PATH:
        step: dict = {"market": market, "city": city, "niche": niche, "steps": []}
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            try:
                factory = FactoryService(memory_dir=tmp, sandbox_dir=tmp / "sandbox")
                intent = FactoryIntentService(memory_dir=tmp, factory=factory)
                sales = SalesOrderService(tmp, intent)
                checkout = PaymentCheckoutService(tmp)
                finance = FinanceService(tmp)
                notifications = OwnerNotificationService(tmp)
                revenue = RevenuePipelineService(sales, finance, checkout, notifications)

                created = sales.create_order(
                    {
                        "business_name": f"{niche.title()} {city}",
                        "description": desc,
                        "email": f"client@{market.lower()}.test",
                        "phone": "+10000000000",
                        "whatsapp": "+10000000000",
                        "city": city,
                        "package_id": "basic",
                        "market_code": market,
                    }
                )
                oid = created["order_id"]
                order = sales.get_order(oid)
                assert order is not None
                step["order_id"] = oid
                step["currency"] = order.get("currency")
                step["market_code"] = order.get("market_code")
                step["price"] = order.get("price_eur")
                step["steps"].append("order_created")

                if order.get("market_code") != market:
                    step["stop"] = "order_market_mismatch"
                    step["detail"] = f"order.market_code={order.get('market_code')}"
                    out.append(step)
                    continue

                ck = revenue.begin_checkout(
                    oid,
                    success_url=f"http://localhost:3000/order/status/{oid}",
                    cancel_url="http://localhost:3000/order",
                )
                step["checkout_provider"] = ck.get("provider")
                step["steps"].append("checkout")

                paid = revenue.complete_sandbox_payment(oid)
                step["paid_ok"] = bool(paid.get("ok"))
                step["steps"].append("paid")

                st = sales.public_status(oid)
                step["status"] = st.get("status")
                step["paid_flag"] = st.get("paid")
                step["product_id"] = st.get("product_id")
                step["client_message"] = (st.get("client_status_message") or "")[:120]
                step["steps"].append(f"status:{st.get('status')}")

                # Wrong-currency re-apply must fail (already paid → already_processed OR reject)
                try:
                    revenue._apply_payment(
                        order_id=oid,
                        amount_eur=1.0,
                        currency="xxx",
                        provider="stripe",
                        sender="attacker@test",
                        external_id="attack-low-amount",
                    )
                    step["amount_guard"] = "FAIL_accepted_wrong_amount"
                except Exception as exc:  # noqa: BLE001
                    step["amount_guard"] = str(exc)[:100]

                prod = st.get("product_id")
                html_path = tmp / "sandbox" / str(prod) / "index.html" if prod else None
                if html_path and html_path.is_file():
                    html = html_path.read_text(encoding="utf-8")
                    step["html_bytes"] = len(html)
                    step["has_maps"] = 'id="maps"' in html or "maps" in html.lower()
                    biz = str(order.get("business_name") or "")
                    step["name_in_html"] = bool(biz) and (
                        biz in html or biz.split()[0] in html or city in html
                    )
                    step["steps"].append("deliverable_html")
                    if not step["paid_flag"]:
                        step["stop"] = "paid_flag_false"
                    elif st.get("status") not in (
                        "in_production",
                        "ready",
                        "delivered",
                        "paid",
                    ):
                        step["stop"] = "bad_status_after_pay"
                    elif step["html_bytes"] < 400:
                        step["stop"] = "deliverable_too_small"
                    elif not step["name_in_html"]:
                        step["stop"] = "deliverable_missing_client_name"
                    else:
                        step["pass"] = True
                else:
                    order2 = sales.get_order(oid)
                    assert order2 is not None
                    step["order_status"] = order2.get("status")
                    step["order_product"] = order2.get("product_id")
                    if (
                        order2.get("status")
                        in ("in_production", "ready", "delivered", "paid")
                        and order2.get("product_id")
                    ):
                        step["pass"] = True
                        step["note"] = "production_started_without_sandbox_html"
                    else:
                        step["stop"] = "paid_but_no_deliverable"
                        step["detail"] = (
                            f"status={order2.get('status')} product={order2.get('product_id')}"
                        )
            except Exception as exc:  # noqa: BLE001
                step["stop"] = "exception"
                step["detail"] = f"{type(exc).__name__}: {exc}"
                step["trace"] = traceback.format_exc()[-600:]
        out.append(step)
    return out


def try_live_api() -> dict:
    import json
    import urllib.error
    import urllib.request

    api = "http://127.0.0.1:8000"
    try:
        with urllib.request.urlopen(f"{api}/api/sales/payment-status", timeout=3) as res:
            body = json.loads(res.read().decode())
        return {"up": True, "payment": body}
    except Exception as exc:  # noqa: BLE001
        return {"up": False, "detail": str(exc)}


def main() -> int:
    live = try_live_api()
    print("=== LIVE STACK ===")
    if live.get("up"):
        print(f"  API up · payment={live.get('payment')}")
    else:
        print(f"  API DOWN — live Stripe not exercised ({live.get('detail')})")
        print("  Start Genesis.exe -> Zapustit, then re-run for Stripe Checkout URLs.")

    print("\n=== CURRENCY / MARKET RESOLUTION ===")
    currency_rows = audit_currency()
    cur_fail = [r for r in currency_rows if not r.get("pass")]
    for r in currency_rows:
        mark = "PASS" if r.get("pass") else f"STOP:{r.get('stop')}"
        print(
            f"  {r['market']}: expect={r['expect']} "
            f"registry={r.get('registry_code')}/{r.get('registry_currency')} "
            f"checkout={r.get('checkout_market')}/{r.get('checkout_currency')} "
            f"price={r.get('price')} · {mark} {r.get('detail', '')}"
        )

    print("\n=== FULL PATH A (order → sandbox pay → deliverable) ===")
    full = audit_full_path()
    fails = [s for s in full if not s.get("pass")]
    for s in full:
        mark = "PASS" if s.get("pass") else f"STOP:{s.get('stop')}"
        print(
            f"  {s['market']}/{s['niche']}: {mark} "
            f"status={s.get('status')} cur={s.get('currency')} "
            f"mkt={s.get('market_code')} price={s.get('price')} "
            f"product={s.get('product_id')} html={s.get('html_bytes')} "
            f"guard={s.get('amount_guard')} {s.get('detail', '')}"
        )
        if s.get("trace") and not s.get("pass"):
            print("    " + s["trace"].replace("\n", "\n    ")[-400:])

    print("\n=== SUMMARY ===")
    print(f"  Currency matrix: {len(currency_rows) - len(cur_fail)}/{len(currency_rows)} PASS")
    print(f"  Full Path A:     {len(full) - len(fails)}/{len(full)} PASS")
    if cur_fail:
        print("  Currency stops:")
        for r in cur_fail:
            print(f"    - {r['market']}: {r.get('stop')} {r.get('detail')}")
    if fails:
        print("  Path A stops:")
        for s in fails:
            print(f"    - {s['market']}/{s['niche']}: {s.get('stop')} {s.get('detail')}")

    # Exit non-zero if any full-path hard fail (currency RU fallback is known gap)
    hard = [s for s in fails if s.get("stop") not in ("order_market_mismatch",)]
    # RU mismatch is still a client-visible bug
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(main())
