"""Live HTTP Demo Company smoke — Nordlicht Möbel GmbH."""
from __future__ import annotations

import json
import urllib.request

API = "http://127.0.0.1:8000"


def post(path: str, body: dict) -> dict:
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        API + path,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode())


def get_bytes(path: str) -> tuple[int, bytes]:
    with urllib.request.urlopen(API + path, timeout=60) as r:
        return r.status, r.read()


def main() -> None:
    report: dict = {}
    web = post(
        "/api/sales/orders",
        {
            "business_name": "Nordlicht Möbel GmbH",
            "description": "Tischlerei und Möbelhaus in Hamburg — Handwerk Premium",
            "email": "info@nordlicht-moebel.de",
            "package_id": "business",
            "city": "Hamburg",
            "niche": "handwerk",
            "market_code": "DE",
            "ui_lang": "de",
            "demo": True,
        },
    )
    report["website_order_id"] = web["order_id"]
    report["website_price"] = web.get("price_eur")
    pay = post(f"/api/sales/orders/{web['order_id']}/pay-demo", {})
    report["website_paid"] = pay.get("ok")
    report["website_payment_mode"] = pay.get("payment_mode")
    report["website_demo"] = pay.get("demo")
    st = json.loads(get_bytes(f"/api/sales/orders/{web['order_id']}/status")[1].decode())
    report["website_status"] = st.get("status")
    report["website_product_id"] = st.get("product_id")
    report["website_payment_mode_status"] = st.get("payment_mode")

    shop = post(
        "/api/sales/orders",
        {
            "business_name": "Nordlicht Möbel GmbH",
            "description": "Online-Shop für Möbel",
            "email": "info@nordlicht-moebel.de",
            "package_id": "ecommerce_shop",
            "city": "Hamburg",
            "market_code": "DE",
            "ui_lang": "de",
            "customer_id": "cust-nordlicht-live",
            "shop_brief": {
                "company_name": "Nordlicht Möbel GmbH",
                "store_name": "Nordlicht Möbel",
                "what_is_sold": "Hochwertige Möbel und Einrichtung aus Hamburg",
                "category": "home",
                "catalog_size": "50",
                "languages": ["de"],
                "currency": "EUR",
                "payments": ["stripe", "invoice"],
                "shipping": ["dhl", "pickup"],
                "pages": [
                    "home",
                    "catalog",
                    "pdp",
                    "about",
                    "contact",
                    "legal",
                    "returns",
                    "cart",
                ],
                "style": "premium",
                "market_code": "DE",
            },
        },
    )
    report["shop_order_id"] = shop["order_id"]
    shop_pay = post(f"/api/sales/orders/{shop['order_id']}/pay-demo", {})
    report["shop_paid"] = shop_pay.get("ok")
    report["shop_payment_mode"] = shop_pay.get("payment_mode")
    sst = json.loads(get_bytes(f"/api/sales/orders/{shop['order_id']}/status")[1].decode())
    report["shop_status"] = sst.get("status")
    report["shop_product_id"] = sst.get("product_id")
    report["shop_pipeline"] = sst.get("shop_pipeline")
    oid = shop["order_id"]
    for page in ("checkout.html", "cart.html", "account.html"):
        try:
            code, body = get_bytes(f"/api/client/stores/{oid}/live/{page}")
            report[page] = code
            if page == "cart.html":
                report["cart_links_checkout"] = b"checkout.html" in body
        except Exception as exc:  # noqa: BLE001
            report[page] = f"fail:{exc}"
    try:
        _code, body = get_bytes("/api/owner/global-analytics")
        ga = json.loads(body.decode())
        report["global_analytics"] = ga.get("title")
        report["has_revenue"] = bool(ga.get("revenue"))
        report["has_funnel"] = bool(ga.get("funnel"))
    except Exception as exc:  # noqa: BLE001
        report["global_analytics"] = f"fail:{exc}"
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
