# -*- coding: utf-8 -*-
"""Bake NEW Premium LORENNE Website + Shop etalon into one client's product dirs.

Does not create a second account. Soft-marks superseded duplicates.
Creates CONTROL_POINT_ORIGINAL on first bake.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parents[1]
sys.path.insert(0, str(BACKEND))

ETALON_WEB = Path(
    os.environ.get(
        "LORENNE_ETALON_WEB",
        str(
            ROOT
            / "dashboard"
            / "frontend"
            / "public"
            / "package-previews"
            / "premium"
            / "lorenne"
        ),
    )
)
ETALON_SHOP = Path(
    os.environ.get(
        "LORENNE_ETALON_SHOP",
        str(
            ROOT
            / "dashboard"
            / "frontend"
            / "public"
            / "package-previews"
            / "premium"
            / "lorenne-shop"
        ),
    )
)

EMAIL = os.environ.get("LORENNE_EMAIL", "Bulhakovasvitlana94@gmail.com").strip()


def _copy_tree(src: Path, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        target = dest / item.name
        if item.is_dir():
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(item, target)
        else:
            shutil.copy2(item, target)


def main() -> int:
    from app.factory.factory_service import FactoryService
    from app.factory.store_factory.service import StoreFactoryService
    from app.integration.customer_identity.store import CustomerIdentityStore
    from app.integration.sales_order_service import SalesOrderService
    from app.integration.store_admin.catalog_service import StoreCatalogService
    from app.integration.store_admin.shop_live_sync import sync_catalog_to_storefront
    from app.integration.website_admin.cinematic_control import (
        ensure_control_point_original,
    )

    if not ETALON_WEB.is_dir() or not (ETALON_WEB / "index.html").is_file():
        raise SystemExit(f"etalon_web_missing:{ETALON_WEB}")
    if not (ETALON_WEB / "assets" / "seq").is_dir():
        raise SystemExit("etalon_web_seq_missing")
    if not ETALON_SHOP.is_dir() or not (ETALON_SHOP / "index.html").is_file():
        raise SystemExit(f"etalon_shop_missing:{ETALON_SHOP}")

    memory_env = (os.environ.get("GENESIS_MEMORY_DIR") or "").strip()
    memory = Path(memory_env) if memory_env else (BACKEND / "app" / "memory")
    memory.mkdir(parents=True, exist_ok=True)

    store = CustomerIdentityStore(memory)
    customer_id = str(store.find_customer_by_email(EMAIL) or "").strip()
    if not customer_id:
        raise SystemExit("lorenne_customer_missing — run provision_lorenne_client first")

    card = store.load_card(customer_id)
    if card is not None:
        card.gift_account = True
        card.gift_unlimited = True
        card.unlimited = True
        card.workspace_mode = "gift_unlimited"
        card.primary_niche = "gift_boxes"
        card.company_display_name = card.company_display_name or "LORENNE"
        store.save_card(card)

    from app.integration.factory_intent_service import FactoryIntentService

    factory = FactoryService(memory_dir=memory)
    intent = FactoryIntentService(memory_dir=memory, factory=factory)
    sales = SalesOrderService(memory, intent)

    summaries = sales.list_orders_for_customer(
        customer_id=customer_id, email=EMAIL, limit=100
    )
    orders = []
    for s in summaries:
        oid = str(s.get("order_id") or "")
        full = sales.get_order(oid) if oid else None
        if full:
            orders.append(full)

    report: dict = {"email": EMAIL, "customer_id": customer_id}

    web_orders = [
        o
        for o in orders
        if str(o.get("product_kind") or "").lower() != "shop"
        and str(o.get("package_id") or "").lower() != "ecommerce_shop"
    ]
    shop_orders = [
        o
        for o in orders
        if str(o.get("product_kind") or "").lower() == "shop"
        or str(o.get("package_id") or "").lower() == "ecommerce_shop"
    ]

    # Ensure one Website + one Shop exist (same account — no second client)
    if not web_orders or not shop_orders:
        os.environ.setdefault("GENESIS_ALLOW_DEMO_PAYMENT", "1")
        from app.integration.finance_service import FinanceService
        from app.integration.owner_notification_service import OwnerNotificationService
        from app.integration.payment_checkout_service import PaymentCheckoutService
        from app.integration.revenue_pipeline_service import RevenuePipelineService

        finance = FinanceService(memory)
        notify = OwnerNotificationService(memory)
        checkout = PaymentCheckoutService(memory)
        revenue = RevenuePipelineService(sales, finance, checkout, notify)

        if not web_orders:
            web = sales.create_order(
                {
                    "business_name": "LORENNE",
                    "description": "LORENNE — Premium Geschenkboxen",
                    "email": EMAIL,
                    "package_id": "premium",
                    "city": "Berlin",
                    "niche": "gift_boxes",
                    "market_code": "DE",
                    "ui_lang": "de",
                    "customer_id": customer_id,
                    "cinematic_enabled": True,
                    "demo": True,
                    "brand_style": "cinematic",
                }
            )
            revenue.complete_demo_payment(str(web["order_id"]))
            full = sales.get_order(str(web["order_id"]))
            if full:
                web_orders.append(full)
                report["created_website_order"] = web.get("order_id")

        if not shop_orders:
            shop = sales.create_order(
                {
                    "business_name": "LORENNE",
                    "description": "LORENNE Online-Shop — Gift Boxes",
                    "email": EMAIL,
                    "package_id": "ecommerce_shop",
                    "city": "Berlin",
                    "market_code": "DE",
                    "ui_lang": "de",
                    "customer_id": customer_id,
                    "demo": True,
                    "cinematic_enabled": True,
                    "shop_brief": {
                        "company_name": "LORENNE",
                        "store_name": "LORENNE",
                        "what_is_sold": "Premium Geschenkboxen",
                        "category": "gifts",
                        "style": "premium",
                        "market_code": "DE",
                    },
                }
            )
            revenue.complete_demo_payment(str(shop["order_id"]))
            full = sales.get_order(str(shop["order_id"]))
            if full:
                shop_orders.append(full)
                report["created_shop_order"] = shop.get("order_id")

    report["web_orders"] = len(web_orders)
    report["shop_orders"] = len(shop_orders)

    # Keep newest as primary; supersede older
    def _sort_key(o: dict) -> str:
        return str(o.get("updated_at") or o.get("created_at") or o.get("order_id") or "")

    web_orders_sorted = sorted(web_orders, key=_sort_key, reverse=True)
    shop_orders_sorted = sorted(shop_orders, key=_sort_key, reverse=True)

    primary_web = web_orders_sorted[0] if web_orders_sorted else None
    primary_shop = shop_orders_sorted[0] if shop_orders_sorted else None

    for o in web_orders_sorted[1:]:
        oid = str(o.get("order_id") or "")
        o["status"] = "superseded"
        o["deliver_allowed"] = False
        o["quality_state"] = "ARCHIVED"
        o["archived_reason"] = "lorenne_premium_etalon_bake"
        sales._save_order(o)  # noqa: SLF001
        report.setdefault("superseded_web", []).append(oid)

    for o in shop_orders_sorted[1:]:
        oid = str(o.get("order_id") or "")
        o["status"] = "superseded"
        o["deliver_allowed"] = False
        o["quality_state"] = "ARCHIVED"
        o["archived_reason"] = "lorenne_premium_etalon_bake"
        sales._save_order(o)  # noqa: SLF001
        report.setdefault("superseded_shop", []).append(oid)

    if primary_web:
        pid = str(primary_web.get("product_id") or "").strip()
        if not pid:
            # allocate sandbox id
            pid = f"lorenne-web-{primary_web['order_id']}"
            primary_web["product_id"] = pid
        dest = factory._sandbox / pid  # noqa: SLF001
        _copy_tree(ETALON_WEB, dest)
        meta = {
            "business_name": "LORENNE",
            "niche": "gift_boxes",
            "package_id": "premium",
            "cinematic": True,
            "quality_state": "READY",
            "etalon": "package-previews/premium/lorenne",
        }
        (dest / "meta.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        ensure_control_point_original(dest)
        primary_web["package_id"] = "premium"
        primary_web["quality_state"] = "READY"
        primary_web["deliver_allowed"] = True
        primary_web["status"] = primary_web.get("status") or "paid"
        primary_web["product_id"] = pid
        primary_web["cinematic_enabled"] = True
        sales._save_order(primary_web)  # noqa: SLF001
        report["website_order_id"] = primary_web.get("order_id")
        report["website_product_id"] = pid
        report["website_dir"] = str(dest)

    if primary_shop:
        pid = str(primary_shop.get("product_id") or "").strip()
        if not pid:
            pid = f"lorenne-shop-{primary_shop['order_id']}"
            primary_shop["product_id"] = pid
        store_factory = StoreFactoryService(memory)
        dest = store_factory.product_dir(pid)
        _copy_tree(ETALON_SHOP, dest)
        ensure_control_point_original(dest)

        # Seed catalog from etalon product names if empty
        catalog = StoreCatalogService(memory)
        existing = catalog._load(str(primary_shop["order_id"]))  # noqa: SLF001
        if not existing:
            # parse catalog.json if present
            cat_path = ETALON_SHOP / "catalog.json"
            seeded = []
            if cat_path.is_file():
                try:
                    raw = json.loads(cat_path.read_text(encoding="utf-8"))
                    items = raw.get("products") if isinstance(raw, dict) else raw
                    if isinstance(items, list):
                        for i, row in enumerate(items, start=1):
                            if not isinstance(row, dict):
                                continue
                            seeded.append(
                                {
                                    "id": f"prd-lorenne-{i:02d}",
                                    "title": row.get("name") or row.get("title") or f"Box {i}",
                                    "price": float(row.get("price") or 0),
                                    "category": row.get("cat") or row.get("category") or "Shop",
                                    "status": "active",
                                    "description": row.get("description") or "",
                                    "images": [
                                        {
                                            "id": f"img-{i}",
                                            "storefront_path": f"assets/products/p{i:02d}.jpg",
                                        }
                                    ],
                                }
                            )
                except (OSError, json.JSONDecodeError, TypeError, ValueError):
                    seeded = []
            if seeded:
                catalog._save(str(primary_shop["order_id"]), seeded)  # noqa: SLF001
                existing = seeded

        if existing:
            sync_catalog_to_storefront(dest, existing)

        primary_shop["quality_state"] = "READY"
        primary_shop["deliver_allowed"] = True
        primary_shop["product_id"] = pid
        sales._save_order(primary_shop)  # noqa: SLF001
        report["shop_order_id"] = primary_shop.get("order_id")
        report["shop_product_id"] = pid
        report["shop_dir"] = str(dest)

    report["ok"] = bool(primary_web and primary_shop)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
