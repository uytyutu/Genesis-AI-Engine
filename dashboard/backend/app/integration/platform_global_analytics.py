"""Mission Control — Global Analytics + Integrations Analytics (platform owner).

Aggregates anonymized/store-level commerce connection stats across store_admin memory.
Privacy: no buyer PII; only merchant connection status counts.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _scan_commerce_files(memory_dir: Path) -> list[dict[str, Any]]:
    root = Path(memory_dir) / "store_admin"
    if not root.is_dir():
        return []
    rows: list[dict[str, Any]] = []
    for path in root.glob("*/commerce_settings.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                rows.append(data)
        except (OSError, json.JSONDecodeError):
            continue
    return rows


def _count_connected(rows: list[dict[str, Any]], bucket: str, provider_id: str) -> int:
    n = 0
    for row in rows:
        block = row.get(bucket)
        if not isinstance(block, dict):
            continue
        # nested map
        if provider_id in block and isinstance(block[provider_id], dict):
            if block[provider_id].get("status") == "connected":
                n += 1
            continue
        # single card
        if block.get("id") == provider_id and block.get("status") == "connected":
            n += 1
    return n


def _store_commerce_incomplete(row: dict[str, Any]) -> bool:
    payments = row.get("payments") if isinstance(row.get("payments"), dict) else {}
    shipping = row.get("shipping") if isinstance(row.get("shipping"), dict) else {}
    any_pay = any(
        isinstance(p, dict) and p.get("status") == "connected" for p in payments.values()
    )
    any_ship = any(
        isinstance(p, dict) and p.get("status") == "connected" for p in shipping.values()
    )
    taxes = row.get("taxes") if isinstance(row.get("taxes"), dict) else {}
    taxes_ok = taxes.get("status") == "connected"
    return not (any_pay and any_ship and taxes_ok)


def build_integrations_analytics(memory_dir: Path) -> dict[str, Any]:
    rows = _scan_commerce_files(memory_dir)
    stores = len(rows)
    providers = [
        ("payments", "stripe", "Stripe"),
        ("payments", "paypal", "PayPal"),
        ("payments", "klarna", "Klarna"),
        ("payments", "sepa", "SEPA"),
        ("shipping", "dhl", "DHL"),
        ("shipping", "dpd", "DPD"),
        ("shipping", "gls", "GLS"),
        ("shipping", "ups", "UPS"),
        ("shipping", "hermes", "Hermes"),
        ("shipping", "fedex", "FedEx"),
        ("shipping", "pickup", "Pickup"),
        ("email", "gmail", "Gmail"),
        ("email", "outlook", "Outlook"),
        ("email", "microsoft365", "Microsoft 365"),
        ("email", "smtp", "SMTP"),
        ("notifications", "telegram", "Telegram"),
    ]
    counts = []
    for bucket, pid, label in providers:
        counts.append(
            {
                "id": pid,
                "category": bucket,
                "label": label,
                "connected_stores": _count_connected(rows, bucket, pid),
            }
        )
    counts.sort(key=lambda x: (-int(x["connected_stores"]), x["label"]))
    incomplete = sum(1 for r in rows if _store_commerce_incomplete(r))
    return {
        "ok": True,
        "title": "Integrations Analytics",
        "stores_scanned": stores,
        "providers": counts,
        "most_popular": counts[0] if counts and counts[0]["connected_stores"] else None,
        "commerce_incomplete_stores": incomplete,
        "privacy": "Aggregated merchant connection status only — no buyer PII.",
        "updated_at": _now(),
    }


def build_global_analytics(
    memory_dir: Path,
    *,
    finance: dict[str, Any] | None = None,
    factory: dict[str, Any] | None = None,
    company: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Company dashboard shell — real where available, honest placeholders elsewhere."""
    from app.integration.launch_readiness import (
        build_business_kpis,
        build_first_value_time,
        build_launch_readiness,
        build_sales_focus,
        build_time_to_launch,
    )

    fin = finance or {}
    fac = factory or {}
    co = company or {}
    integ = build_integrations_analytics(memory_dir)

    sections = [
        {
            "id": "finance",
            "label": "Финансы",
            "status": "live",
            "metrics": [
                {"id": "revenue_today", "label": "Выручка сегодня", "value": fin.get("revenue_today_eur"), "unit": "€"},
                {"id": "mrr", "label": "Подписки (MRR)", "value": fin.get("mrr_eur") or fin.get("subscription_mrr_eur"), "unit": "€"},
                {"id": "one_time", "label": "Разовые продажи", "value": fin.get("one_time_revenue_eur"), "unit": "€"},
                {"id": "avg_order", "label": "Средний чек", "value": fin.get("avg_order_eur"), "unit": "€"},
                {"id": "ltv", "label": "LTV", "value": fin.get("ltv_eur"), "unit": "€"},
            ],
        },
        {
            "id": "products",
            "label": "Продукты",
            "status": "live",
            "metrics": [
                {"id": "websites", "label": "Websites", "value": fac.get("websites_total") or fac.get("sites_created")},
                {"id": "ai_stores", "label": "AI Stores", "value": fac.get("stores_total") or integ.get("stores_scanned")},
                {"id": "digital_employees", "label": "AI Digital Employees", "value": None, "coming": "R4"},
                {"id": "automation", "label": "Automation", "value": None, "coming": "R4"},
                {"id": "crm", "label": "CRM", "value": None, "coming": "R4"},
                {"id": "analytics", "label": "Analytics modules", "value": None, "coming": "R3.4"},
            ],
        },
        {
            "id": "clients",
            "label": "Клиенты",
            "status": "partial",
            "metrics": [
                {"id": "total", "label": "Всего клиентов", "value": co.get("total_clients") or fin.get("clients")},
                {"id": "new", "label": "Новые регистрации", "value": co.get("new_clients")},
                {"id": "active", "label": "Активные пользователи", "value": co.get("active_users")},
                {"id": "site_owners", "label": "Владельцы сайтов", "value": fac.get("website_owners")},
                {"id": "store_owners", "label": "Владельцы магазинов", "value": integ.get("stores_scanned")},
            ],
        },
        {
            "id": "vector",
            "label": "Vector Analytics",
            "status": "shell",
            "coming": "expand",
            "metrics": [
                {"id": "dialogs", "label": "Диалоги", "value": None},
                {"id": "tasks_helped", "label": "Задачи с помощью Vector", "value": None},
                {"id": "top_tips", "label": "Популярные подсказки", "value": None},
                {"id": "dropoffs", "label": "Где останавливаются", "value": None},
            ],
        },
        {
            "id": "website_factory",
            "label": "Website Factory",
            "status": "partial",
            "metrics": [
                {"id": "created", "label": "Сайтов создано", "value": fac.get("websites_total") or fac.get("sites_created")},
                {"id": "avg_gen", "label": "Среднее время генерации", "value": fac.get("avg_generation_seconds"), "unit": "s"},
                {"id": "niches", "label": "Популярные ниши", "value": fac.get("top_niche")},
                {"id": "errors", "label": "Ошибки Factory", "value": fac.get("factory_errors")},
            ],
        },
        {
            "id": "store_factory",
            "label": "Store Factory",
            "status": "partial",
            "metrics": [
                {"id": "stores", "label": "Магазинов создано", "value": integ.get("stores_scanned")},
                {"id": "categories", "label": "Популярные категории", "value": fac.get("top_store_category")},
                {"id": "ai_products", "label": "Товаров через AI", "value": fac.get("ai_products_created")},
                {"id": "designs", "label": "Дизайнов выбрано", "value": fac.get("designs_chosen")},
            ],
        },
        {
            "id": "commerce",
            "label": "Commerce",
            "status": "live",
            "metrics": [
                {"id": "stripe", "label": "Stripe", "value": _pick(integ, "stripe")},
                {"id": "paypal", "label": "PayPal", "value": _pick(integ, "paypal")},
                {"id": "klarna", "label": "Klarna", "value": _pick(integ, "klarna")},
                {"id": "dhl", "label": "DHL", "value": _pick(integ, "dhl")},
                {"id": "ups", "label": "UPS", "value": _pick(integ, "ups")},
                {"id": "gmail", "label": "Gmail", "value": _pick(integ, "gmail")},
                {
                    "id": "incomplete",
                    "label": "Commerce не завершён",
                    "value": integ.get("commerce_incomplete_stores"),
                },
            ],
        },
        {
            "id": "marketing",
            "label": "Marketing",
            "status": "coming",
            "coming": "Post R3.3",
            "metrics": [
                {"id": "sources", "label": "Источники клиентов", "value": None},
                {"id": "campaigns", "label": "Кампании", "value": None},
                {"id": "seo", "label": "SEO", "value": None},
            ],
        },
        {
            "id": "apify",
            "label": "Apify",
            "status": "shell",
            "metrics": [
                {"id": "actors", "label": "Actor'ов", "value": None},
                {"id": "runs", "label": "Запусков", "value": None},
                {"id": "revenue", "label": "Доход", "value": None, "unit": "€"},
                {"id": "rating", "label": "Рейтинг", "value": None},
            ],
        },
        {
            "id": "ai_health",
            "label": "AI Health",
            "status": "shell",
            "metrics": [
                {"id": "website_factory", "label": "Website Factory", "value": "ok"},
                {"id": "store_factory", "label": "Store Factory", "value": "ok"},
                {"id": "vector", "label": "Vector", "value": "ok"},
                {"id": "commerce", "label": "Commerce", "value": "ok"},
                {"id": "analytics", "label": "Analytics", "value": "coming"},
                {"id": "crm", "label": "CRM", "value": "coming"},
                {"id": "apify", "label": "Apify", "value": "ok"},
            ],
        },
        {
            "id": "marketplace",
            "label": "Marketplace",
            "status": "coming",
            "coming": "R4",
            "metrics": [
                {"id": "top_modules", "label": "Популярные модули", "value": None},
                {"id": "module_revenue", "label": "Доход по модулям", "value": None},
                {"id": "licenses", "label": "Активные лицензии", "value": None},
            ],
        },
    ]

    headline = {
        "revenue_today_eur": fin.get("revenue_today_eur"),
        "new_clients": co.get("new_clients"),
        "sites_created": fac.get("websites_total") or fac.get("sites_created"),
        "stores_published": fac.get("stores_published"),
        "active_subscriptions": fin.get("active_subscriptions"),
        "commerce_incomplete": integ.get("commerce_incomplete_stores"),
        "stores_with_integrations": integ.get("stores_scanned"),
    }

    return {
        "ok": True,
        "title": "Global Analytics",
        "subtitle": "Весь бизнес Virtus Core в одном месте",
        "headline": headline,
        "sections": sections,
        "integrations": integ,
        "revenue": build_revenue_dashboard(memory_dir, finance=fin),
        "funnel": build_platform_funnel(memory_dir),
        "gen1_readiness": build_gen1_readiness(memory_dir),
        "launch_readiness": build_launch_readiness(memory_dir),
        "sales_focus": build_sales_focus(memory_dir),
        "business_kpis": build_business_kpis(memory_dir),
        "time_to_launch": build_time_to_launch(memory_dir),
        "first_value_time": build_first_value_time(memory_dir),
        "email": build_email_analytics(memory_dir),
        "shipping": build_shipping_analytics(memory_dir),
        "updated_at": _now(),
        "note": (
            "Gen1 Feature Freeze. Priority: Sales (first 5) → Real Beta → UX → Perf → Polish. "
            "KPIs: Success Path · First Value Time · Time To Launch · Funnel. No Gen2."
        ),
    }


def _pick(integ: dict[str, Any], provider_id: str) -> int | None:
    for p in integ.get("providers") or []:
        if isinstance(p, dict) and p.get("id") == provider_id:
            return int(p.get("connected_stores") or 0)
    return 0


def _stripe_oauth_connected_count(rows: list[dict[str, Any]]) -> int:
    n = 0
    for row in rows:
        payments = row.get("payments") if isinstance(row.get("payments"), dict) else {}
        stripe = payments.get("stripe") if isinstance(payments.get("stripe"), dict) else {}
        acct = str(stripe.get("stripe_user_id") or "").strip()
        if stripe.get("status") == "connected" and acct.startswith("acct_"):
            n += 1
    return n


def _email_provider_connected(rows: list[dict[str, Any]]) -> bool:
    for row in rows:
        email = row.get("email") if isinstance(row.get("email"), dict) else {}
        for p in email.values():
            if isinstance(p, dict) and p.get("status") == "connected":
                return True
    return False


def _email_test_success(rows: list[dict[str, Any]]) -> bool:
    for row in rows:
        transport = row.get("email_transport") if isinstance(row.get("email_transport"), dict) else {}
        last = transport.get("last_test") if isinstance(transport.get("last_test"), dict) else {}
        if last.get("ok"):
            return True
    return False


def build_email_analytics(memory_dir: Path) -> dict[str, Any]:
    """Mission Control — merchant email health across stores."""
    root = Path(memory_dir) / "store_admin"
    connected = 0
    test_ok = 0
    test_fail = 0
    queued = 0
    last_error: str | None = None
    last_error_at: str | None = None
    stores = 0
    if root.is_dir():
        for shop in root.iterdir():
            if not shop.is_dir():
                continue
            commerce = shop / "commerce_settings.json"
            if commerce.is_file():
                stores += 1
                try:
                    data = json.loads(commerce.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    data = {}
                email = data.get("email") if isinstance(data.get("email"), dict) else {}
                if any(
                    isinstance(p, dict) and p.get("status") == "connected"
                    for p in email.values()
                ):
                    connected += 1
                transport = (
                    data.get("email_transport")
                    if isinstance(data.get("email_transport"), dict)
                    else {}
                )
                last = (
                    transport.get("last_test")
                    if isinstance(transport.get("last_test"), dict)
                    else {}
                )
                if last.get("ok") is True:
                    test_ok += 1
                elif last.get("ok") is False:
                    test_fail += 1
                    err = str(last.get("title") or last.get("reason") or "SMTP failed")
                    at = str(last.get("sent_at") or "")
                    if not last_error_at or at > (last_error_at or ""):
                        last_error = err
                        last_error_at = at or last_error_at
            journal = shop / "email_send_journal.jsonl"
            if journal.is_file():
                try:
                    for line in journal.read_text(encoding="utf-8").splitlines():
                        if not line.strip():
                            continue
                        try:
                            row = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        if row.get("ok") is True:
                            test_ok += 0  # already counted from last_test; journal for fails/queue
                        if row.get("status") in {"queued", "queued_stub"}:
                            queued += 1
                        if row.get("ok") is False:
                            test_fail += 1
                            err = str(row.get("title") or row.get("reason") or "send failed")
                            at = str(row.get("at") or "")
                            if not last_error_at or at > (last_error_at or ""):
                                last_error = err
                                last_error_at = at or last_error_at
                except OSError:
                    pass
            outbox = shop / "mail_outbox.json"
            if outbox.is_file():
                try:
                    data = json.loads(outbox.read_text(encoding="utf-8"))
                    mails = data.get("messages") if isinstance(data, dict) else data
                    if isinstance(mails, list):
                        queued += sum(
                            1
                            for m in mails
                            if isinstance(m, dict)
                            and str(m.get("status") or "").startswith("queued")
                        )
                except (OSError, json.JSONDecodeError):
                    pass

    tested = test_ok + test_fail
    success_rate = round(100.0 * test_ok / tested, 1) if tested else None
    return {
        "ok": True,
        "title": "Email",
        "connected": connected,
        "stores_scanned": stores,
        "test_success_rate": success_rate,
        "failed_sends": test_fail,
        "queued": queued,
        "last_error": last_error,
        "last_error_at": last_error_at,
        "updated_at": _now(),
    }


def build_shipping_analytics(memory_dir: Path) -> dict[str, Any]:
    """Mission Control — carrier API adoption and shipment pipeline."""
    from app.integration.store_admin.shipping_api_service import count_shipping_api_activity

    stats = count_shipping_api_activity(memory_dir)
    by = stats.get("by_carrier") or {}
    return {
        "ok": True,
        "title": "Shipping",
        "dhl": int(by.get("dhl") or 0),
        "dpd": int(by.get("dpd") or 0),
        "gls": int(by.get("gls") or 0),
        "hermes": int(by.get("hermes") or 0),
        "ups": int(by.get("ups") or 0),
        "fedex": int(by.get("fedex") or 0),
        "shipments_created": int(stats.get("shipments_created") or 0),
        "delivered": int(stats.get("delivered") or 0),
        "api_errors": int(stats.get("api_errors") or 0),
        "stores_with_api": int(stats.get("stores_with_api") or 0),
        "updated_at": _now(),
    }


def build_gen1_readiness(memory_dir: Path) -> dict[str, Any]:
    """Mission Control — Gen1 launch checklist (business + technical readiness)."""
    rows = _scan_commerce_files(memory_dir)
    from app.integration import stripe_connect_oauth as stripe_oauth

    stripe_oauth_stores = _stripe_oauth_connected_count(rows)
    stripe_status = "done" if stripe_oauth_stores > 0 else "pending"
    stripe_detail = (
        f"{stripe_oauth_stores} store(s) Connected via OAuth"
        if stripe_oauth_stores
        else (
            "OAuth ready — waiting for first merchant Connect"
            if stripe_oauth.oauth_client_ready()
            else "Set STRIPE_CONNECT_CLIENT_ID (ca_…)"
        )
    )

    smtp_status = "done" if _email_test_success(rows) else "pending"
    smtp_detail = (
        "SMTP Connected + Test Email success"
        if smtp_status == "done"
        else (
            "Provider connected — Send Test Email required"
            if _email_provider_connected(rows)
            else "Gmail / Outlook / M365 / SMTP + Test Email"
        )
    )
    from app.integration.store_admin.invoice_pdf_service import count_issued_invoices
    from app.integration.store_admin.shipping_api_service import (
        count_shipping_api_activity,
        shipping_api_ready,
    )
    from app.factory.visual_intelligence import visual_intelligence_ready

    pdf_count = count_issued_invoices(memory_dir)
    pdf_status = "done" if pdf_count > 0 else "pending"
    ship_ready = shipping_api_ready(memory_dir)
    ship_stats = count_shipping_api_activity(memory_dir)
    ship_detail = (
        f"{ship_stats.get('shipments_created', 0)} shipment(s) · "
        f"{ship_stats.get('delivered', 0)} delivered"
        if ship_ready
        else "DHL / DPD / GLS — rates · create · track"
    )
    vie_ready = visual_intelligence_ready(memory_dir)
    items = [
        {"id": "architecture", "label": "Architecture", "status": "done"},
        {"id": "website_factory", "label": "Website Factory", "status": "done"},
        {"id": "store_factory", "label": "Store Factory", "status": "done"},
        {"id": "vector", "label": "Vector", "status": "done"},
        {"id": "commerce_ui", "label": "Commerce UI", "status": "done"},
        {"id": "checkout", "label": "Checkout", "status": "done"},
        {
            "id": "stripe_oauth",
            "label": "Stripe OAuth",
            "status": stripe_status,
            "detail": stripe_detail,
        },
        {
            "id": "smtp",
            "label": "SMTP",
            "status": smtp_status,
            "detail": smtp_detail,
        },
        {
            "id": "pdf",
            "label": "PDF",
            "status": pdf_status,
            "detail": (
                f"{pdf_count} invoice PDF(s) issued"
                if pdf_count
                else "Invoice + Credit Note with client logo"
            ),
        },
        {
            "id": "shipping_api",
            "label": "Shipping API",
            "status": "done" if ship_ready else "pending",
            "detail": ship_detail,
        },
        {
            "id": "visual_engine",
            "label": "Visual Engine",
            "status": "done" if vie_ready else "pending",
            "detail": (
                "Style · Asset · Motion · Quality Gate ≥ 90"
                if vie_ready
                else "Premium visual polish — Gen1 final polish"
            ),
        },
        {
            "id": "beta_customers",
            "label": "Beta Customers",
            "status": "pending",
            "detail": "5–10 first clients + feedback loop",
        },
        {
            "id": "public_launch",
            "label": "Public Launch",
            "status": "pending",
            "detail": "Only after core scenarios proven live",
        },
    ]
    done = sum(1 for i in items if i.get("status") == "done")
    total = len(items)
    next_item = next((i for i in items if i.get("status") != "done"), None)
    return {
        "ok": True,
        "title": "Gen1 Readiness",
        "done": done,
        "total": total,
        "pct": round(100.0 * done / total) if total else 0,
        "next": next_item,
        "items": items,
        "focus": (
            "FEATURE FREEZE. Next: Launch Readiness — Performance · Beta Feedback · Docs. "
            "Then Public Launch. Gen2 only after."
        ),
        "phase": "feature_freeze",
        "updated_at": _now(),
    }


def _scan_shop_orders(memory_dir: Path) -> list[dict[str, Any]]:
    root = Path(memory_dir) / "store_admin"
    if not root.is_dir():
        return []
    rows: list[dict[str, Any]] = []
    for path in root.glob("*/orders.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            orders = data.get("orders") if isinstance(data, dict) else data
            if isinstance(orders, list):
                rows.extend(o for o in orders if isinstance(o, dict))
        except (OSError, json.JSONDecodeError):
            continue
    return rows


def build_revenue_dashboard(
    memory_dir: Path,
    *,
    finance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    fin = finance or {}
    shop_orders = _scan_shop_orders(memory_dir)
    now = datetime.now(timezone.utc)

    def _in_range(iso: str | None, days: int | None) -> bool:
        if not iso:
            return False
        try:
            dt = datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            if days is None:
                return True
            return (now - dt).total_seconds() < days * 86400
        except Exception:
            return False

    def _sum(days: int | None) -> float:
        return round(
            sum(
                float(o.get("total_eur") or 0)
                for o in shop_orders
                if _in_range(o.get("created_at"), days)
            ),
            2,
        )

    pending = sum(
        1
        for o in shop_orders
        if str(o.get("status") or "").startswith(("pending", "awaiting"))
        or str(o.get("payment_status") or "") == "pending"
    )
    completed = sum(
        1
        for o in shop_orders
        if str(o.get("status") or "") in {"completed", "paid", "fulfilled"}
    )
    totals = [float(o.get("total_eur") or 0) for o in shop_orders]
    aov = round(sum(totals) / len(totals), 2) if totals else None
    mrr = fin.get("mrr_eur") or fin.get("subscription_mrr_eur")
    arr = float(mrr) * 12 if mrr is not None else None

    return {
        "ok": True,
        "title": "Revenue Dashboard",
        "periods": {
            "today_eur": fin.get("revenue_today_eur")
            if fin.get("revenue_today_eur") is not None
            else _sum(1),
            "week_eur": _sum(7),
            "month_eur": fin.get("revenue_month_eur")
            if fin.get("revenue_month_eur") is not None
            else _sum(30),
            "year_eur": _sum(365),
        },
        "metrics": {
            "mrr_eur": mrr,
            "arr_eur": arr,
            "avg_order_eur": aov or fin.get("avg_order_eur"),
            "ltv_eur": fin.get("ltv_eur"),
            "cac_eur": fin.get("cac_eur"),
            "conversion_pct": fin.get("conversion_pct"),
            "refunds_eur": fin.get("refunds_eur") or 0,
            "pending_orders": pending,
            "completed_orders": completed,
            "shop_orders_total": len(shop_orders),
            "shop_gmv_eur": round(sum(totals), 2),
        },
        "note": "Shop GMV from Checkout 1.0 + Virtus finance when available.",
        "updated_at": _now(),
    }


def build_platform_funnel(memory_dir: Path) -> dict[str, Any]:
    """Daily Mission Control funnel — find where people drop off."""
    path = Path(memory_dir) / "platform_funnel.json"
    counts: dict[str, int] = {}
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            raw = data.get("counts") if isinstance(data, dict) else {}
            if isinstance(raw, dict):
                counts = {str(k): int(v or 0) for k, v in raw.items()}
        except (OSError, json.JSONDecodeError):
            counts = {}

    commerce_rows = _scan_commerce_files(memory_dir)
    shop_orders = _scan_shop_orders(memory_dir)
    connected = sum(
        1
        for r in commerce_rows
        if any(
            isinstance(p, dict) and p.get("status") == "connected"
            for p in (r.get("payments") or {}).values()
        )
    )
    counts["commerce_connected"] = connected
    shops_with_orders = 0
    real_shop_orders = 0
    admin = Path(memory_dir) / "store_admin"
    if admin.is_dir():
        for op in admin.glob("*/orders.json"):
            try:
                data = json.loads(op.read_text(encoding="utf-8"))
                orders = data.get("orders") if isinstance(data, dict) else []
                if isinstance(orders, list) and orders:
                    shops_with_orders += 1
                    for o in orders:
                        if not isinstance(o, dict):
                            continue
                        mode = str(o.get("payment_mode") or "").lower()
                        if mode not in {"demo", "sandbox"} and o.get("demo") is not True:
                            real_shop_orders += 1
            except (OSError, json.JSONDecodeError):
                pass
    counts["shops_with_orders"] = shops_with_orders
    counts["store_orders"] = real_shop_orders
    counts["first_sale"] = int(counts.get("payment") or 0) or shops_with_orders
    counts["repeat_order"] = max(0, len(shop_orders) - shops_with_orders)
    counts["reviews"] = int(counts.get("reviews") or 0)
    counts["leads"] = int(counts.get("leads") or counts.get("registration") or 0)
    counts["website_orders"] = int(counts.get("website_orders") or counts.get("payment") or 0)

    stages = [
        {"id": "visitors", "label": "Visitors", "count": counts.get("visitors")},
        {"id": "leads", "label": "Leads", "count": counts.get("leads")},
        {"id": "website_orders", "label": "Website Orders", "count": counts.get("website_orders")},
        {"id": "store_orders", "label": "Store Orders", "count": counts.get("store_orders")},
        {"id": "payments", "label": "Payments", "count": counts.get("payment")},
        {"id": "factory", "label": "Factory", "count": counts.get("factory")},
        {"id": "published", "label": "Published", "count": counts.get("published")},
        {
            "id": "commerce_connected",
            "label": "Commerce Connected",
            "count": counts.get("commerce_connected"),
        },
        {"id": "first_sale", "label": "First Sale", "count": counts.get("first_sale")},
        {"id": "reviews", "label": "Reviews", "count": counts.get("reviews")},
        {
            "id": "repeat_customers",
            "label": "Repeat Customers",
            "count": counts.get("repeat_order"),
        },
    ]

    # Drop-off hint between consecutive non-null stages
    drop: dict[str, Any] | None = None
    prev_id, prev_n = None, None
    for st in stages:
        n = st.get("count")
        if n is None or prev_n is None or prev_n <= 0:
            if n is not None:
                prev_id, prev_n = st["id"], int(n)
            continue
        cur = int(n)
        if cur < prev_n:
            lost_pct = round(100.0 * (prev_n - cur) / prev_n, 1)
            if drop is None or lost_pct > float(drop.get("lost_pct") or 0):
                drop = {
                    "from": prev_id,
                    "to": st["id"],
                    "from_count": prev_n,
                    "to_count": cur,
                    "lost_pct": lost_pct,
                    "question": f"Где уходят? {prev_id} → {st['id']} (−{lost_pct}%)",
                }
        prev_id, prev_n = st["id"], cur

    return {
        "ok": True,
        "title": "Daily Funnel",
        "subtitle": "Каждый день: где люди уходят?",
        "stages": stages,
        "counts": counts,
        "biggest_drop": drop,
        "note": (
            "Если 40% бросают checkout — чинить checkout. "
            "Если никто не подключает Stripe — разбирать почему. "
            "Не добавлять модули."
        ),
        "updated_at": _now(),
    }


class PlatformGlobalAnalyticsService:
    def __init__(self, memory_dir: Path) -> None:
        self._memory = Path(memory_dir)

    def integrations(self) -> dict[str, Any]:
        return build_integrations_analytics(self._memory)

    def revenue(self, finance: dict[str, Any] | None = None) -> dict[str, Any]:
        return build_revenue_dashboard(self._memory, finance=finance)

    def funnel(self) -> dict[str, Any]:
        return build_platform_funnel(self._memory)

    def gen1_readiness(self) -> dict[str, Any]:
        return build_gen1_readiness(self._memory)

    def launch_readiness(self) -> dict[str, Any]:
        from app.integration.launch_readiness import build_launch_readiness

        return build_launch_readiness(self._memory)

    def business_kpis(self) -> dict[str, Any]:
        from app.integration.launch_readiness import build_business_kpis

        return build_business_kpis(self._memory)

    def global_snapshot(
        self,
        *,
        finance: dict[str, Any] | None = None,
        factory: dict[str, Any] | None = None,
        company: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return build_global_analytics(
            self._memory,
            finance=finance,
            factory=factory,
            company=company,
        )
